"""Side-by-side 360-degree turntable of two GLBs, rendered with Cycles on Modal GPUs.

Each model is scaled to 2 m tall and turned on the spot under fixed studio lights (the
body-v2 inspection studio), so both get exactly the same lighting at every angle. Two shots:
full body and an upper-body close-up. Frames land on the Modal Volume and are pulled back for
ffmpeg (side by side, labels, H.264).

  python tools/run_trellis.py --turntable --left .tmp/body-v2/seed-7/body-remesh.glb --right .tmp/tripo-ultra-ny.glb
"""
from pathlib import Path
import os
import modal

app = modal.App('yukimura-turntable')
cache = modal.Volume.from_name('yukimura-trellis2-cache')
image = (modal.Image.debian_slim(python_version='3.11')
         .apt_install('libxrender1', 'libxi6', 'libxkbcommon0', 'libsm6', 'libgl1', 'libegl1', 'libxxf86vm1', 'libxfixes3', 'libgomp1')
         .pip_install('bpy==4.3.0'))
ROOT = '/cache/turntable'
FRAMES = 360                      # 12 s at 30 fps per shot
SHOTS = {'full': {'target': (0, 0, 1.03), 'height': 1.2, 'span': 2.3}, 'close': {'target': (0, 0, 1.5), 'height': 1.55, 'span': 1.06}}
W, H, SAMPLES = 960, 1080, 96


@app.function(image=image, gpu='L4', cpu=4, memory=16384, timeout=3600, max_containers=12, volumes={'/cache': cache}, retries=1)
def render(name: str, shot: str, frames: list):
    import math, time
    import bpy
    from mathutils import Vector
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'{ROOT}/inputs/{name}.glb')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(v[i] for v in pts) for i in range(3)]); hi = Vector([max(v[i] for v in pts) for i in range(3)])
    spin = bpy.data.objects.new('spin', None); bpy.context.collection.objects.link(spin)
    fit = bpy.data.objects.new('fit', None); bpy.context.collection.objects.link(fit); fit.parent = spin
    for o in list(bpy.context.scene.objects):
        if o not in (spin, fit) and o.parent is None: o.parent = fit
    s = 2.0 / (hi.z - lo.z); fit.scale = (s,) * 3; fit.location = (-(lo.x + hi.x) / 2 * s, -(lo.y + hi.y) / 2 * s, -lo.z * s)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(d.type == kind for d in prefs.devices): break
        except TypeError:
            continue
    for d in prefs.devices: d.use = d.type != 'CPU'
    scene.cycles.device = 'GPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.world = bpy.data.worlds.new('studio'); scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (.10, .12, .15, 1); bg.inputs['Strength'].default_value = .35
    def aim(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    for loc, energy, col, size in (((3, -4, 5), 650, (1, .88, .73), 4), ((-4, -2, 3), 450, (.7, .83, 1), 4), ((1, 3, 4), 750, (1, .94, .8), 3)):
        bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object; L.data.energy = energy; L.data.color = col; L.data.shape = 'DISK'; L.data.size = size; aim(L, (0, 0, 1))
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.006)); floor = bpy.context.object
    m = bpy.data.materials.new('slate'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.035, .042, .055, 1); b.inputs['Roughness'].default_value = .73; floor.data.materials.append(m)
    cfg = SHOTS[shot]
    bpy.ops.object.camera_add(); cam = bpy.context.object; scene.camera = cam
    cam.data.lens = 85; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24
    dist = (cfg['span'] / 2) / math.tan(math.atan(12 / 85))
    tgt = Vector(cfg['target']); cam.location = tgt + Vector((0, -dist, cfg['height'] - tgt.z)); aim(cam, tgt)
    out = Path(f'{ROOT}/frames/{shot}/{name}'); out.mkdir(parents=True, exist_ok=True)
    for f in frames:
        spin.rotation_euler = (0, 0, math.radians(360 * f / FRAMES))
        scene.render.filepath = str(out / f'{f:04d}.png'); bpy.ops.render.render(write_still=True)
    cache.commit()
    return {'name': name, 'shot': shot, 'frames': len(frames), 'seconds': round(time.time() - t0, 1),
            'devices': [d.name for d in prefs.devices if d.use]}


@app.local_entrypoint()
def main(left: str, right: str, output: str = '.tmp/turntable', chunk: int = 30, shots: str = 'full,close', test: bool = False):
    names = {'left': left, 'right': right}
    with cache.batch_upload(force=True) as up:
        for k, path in names.items(): up.put_file(path, f'/turntable/inputs/{k}.glb')
    jobs = [(k, s, list(range(i, min(i + chunk, FRAMES)))) for s in shots.split(',') for k in names for i in range(0, FRAMES, chunk)]
    if test: jobs = [(k, s, [0, 90]) for s in shots.split(',') for k in names]      # framing / device check
    for r in render.starmap(jobs, order_outputs=False): print(r, flush=True)
    for s in shots.split(','):
        for k in names:
            d = Path(output, s, k); d.mkdir(parents=True, exist_ok=True)
            for e in cache.listdir(f'/turntable/frames/{s}/{k}'):
                (d / Path(e.path).name).write_bytes(b''.join(cache.read_file(e.path)))
            print('downloaded', s, k, len(list(d.iterdir())), flush=True)
