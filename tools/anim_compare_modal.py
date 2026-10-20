"""Animated rigging comparison, rendered with Cycles on Modal GPUs (same studio as turntable_modal.py).

Inputs (all face -Y except the Tripo preset export, which faces +X and is turned here):
  open    tools/rig_open.py output: open-source rig + the game's clips
  tripo   tools/rig_tripo_gameclips.py output: Tripo's auto-rig + the same game clips
  preset  Tripo's retarget export: Tripo's auto-rig + Tripo's preset animations
Each model is scaled to 2 m from its rest pose and every clip is centred on its root's mean ground
position. Shots: 'full' and 'close' (upper body) at 960x1080 for open/tripo side by side, 'wide' at
1920x1080 for the presets. Frames land on the Modal Volume and are pulled back for
tools/anim_compare_compose.sh.

  python tools/run_trellis.py --anim-compare --open .tmp/rig-open/rig-open.glb \
      --tripo .tmp/rig-tripo/tripo-gameclips.glb --preset docs/.../rig/tripo/retarget-model_url.glb
"""
from pathlib import Path
import modal

app = modal.App('yukimura-anim-compare')
cache = modal.Volume.from_name('yukimura-trellis2-cache')
image = (modal.Image.debian_slim(python_version='3.11')
         .apt_install('libxrender1', 'libxi6', 'libxkbcommon0', 'libsm6', 'libgl1', 'libegl1', 'libxxf86vm1', 'libxfixes3', 'libgomp1')
         .pip_install('bpy==4.3.0'))
ROOT = '/cache/animcmp'
GAME_CLIPS = ['idle', 'run', 'slash', 'hurt']
PRESET_CAP = {'run': 999, 'slash': 999, 'hurt': 240, 'idle': 120}      # frames; Tripo's idle and hurt run 13-15 s
SHOTS = {'full': {'target': (0, 0, 1.0), 'height': 1.25, 'span': 2.4, 'size': (960, 1080)},
         'close': {'target': (0, 0, 1.4), 'height': 1.55, 'span': 1.25, 'size': (960, 1080)},
         'wide': {'target': (0, 0, 1.0), 'height': 1.25, 'span': 2.4, 'size': (1920, 1080)}}
YAW, SAMPLES = -30, 64            # camera 30 degrees to the figure's right of straight-on


@app.function(image=image, gpu='L4', cpu=4, memory=16384, timeout=3600, max_containers=12, volumes={'/cache': cache}, retries=1)
def render(name: str, shot: str, clip: str, frames: list):
    import math, time
    import bpy
    from mathutils import Vector
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=f'{ROOT}/inputs/{name}.glb')
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    meshes = [o for o in scene.objects if o.type == 'MESH' and o.parent is rig]
    for o in [o for o in scene.objects if o.type == 'MESH' and o not in meshes]: bpy.data.objects.remove(o, do_unlink=True)
    top = rig
    while top.parent: top = top.parent
    root = bpy.data.objects.new('root', None); scene.collection.objects.link(root); top.parent = root
    if name == 'preset': root.rotation_euler.z = -math.pi / 2
    for t in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(t)
    # rest-pose height of the skinned mesh (Tripo's raw vertex data is in bind space)
    rig.animation_data.action = None; rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); zs = []
    for o in meshes:
        e = o.evaluated_get(dg); m = e.to_mesh(); zs += [(e.matrix_world @ v.co).z for v in m.vertices]; e.to_mesh_clear()
    rig.data.pose_position = 'POSE'
    s = 2.0 / (max(zs) - min(zs)); root.scale = (s,) * 3; root.location.z = -min(zs) * s
    act = next(x for x in bpy.data.actions if x.name.split('_')[0] == clip)
    rig.animation_data.action = act
    hips = next(b for b in rig.pose.bones if not b.parent); c = Vector(); f0, f1 = (int(math.ceil(act.frame_range[0])), int(act.frame_range[1]))
    span = range(f0, f1 + 1, 2)
    for f in span: scene.frame_set(f); c += (rig.matrix_world @ hips.head) / len(span)
    root.location.x, root.location.y = -c.x, -c.y
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(d.type == kind for d in prefs.devices): break
        except TypeError:
            continue
    for d in prefs.devices: d.use = d.type != 'CPU'
    cfg = SHOTS[shot]
    scene.cycles.device = 'GPU'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = cfg['size']
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
    bpy.ops.object.camera_add(); cam = bpy.context.object; scene.camera = cam
    cam.data.lens = 85; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24
    dist = (cfg['span'] / 2) / math.tan(math.atan(12 / 85)); a = math.radians(YAW)
    tgt = Vector(cfg['target']); cam.location = tgt + Vector((-dist * math.sin(a), -dist * math.cos(a), cfg['height'] - tgt.z)); aim(cam, tgt)
    out = Path(f'{ROOT}/frames/{shot}/{name}/{clip}'); out.mkdir(parents=True, exist_ok=True)
    for f in frames:
        scene.frame_set(f0 + f); scene.render.filepath = str(out / f'{f:04d}.png'); bpy.ops.render.render(write_still=True)
    cache.commit()
    return {'name': name, 'shot': shot, 'clip': clip, 'frames': len(frames), 'seconds': round(time.time() - t0, 1)}


@app.function(image=image, volumes={'/cache': cache})
def lengths(name: str):
    """frame count of every clip in an uploaded GLB"""
    import math, bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'{ROOT}/inputs/{name}.glb')
    return {x.name.split('_')[0]: int(x.frame_range[1]) - int(math.ceil(x.frame_range[0])) + 1 for x in bpy.data.actions}


@app.local_entrypoint()
def main(open: str, tripo: str, preset: str, output: str = '.tmp/animcmp', chunk: int = 20, test: bool = False):
    names = {'open': open, 'tripo': tripo, 'preset': preset}
    with cache.batch_upload(force=True) as up:
        for k, path in names.items(): up.put_file(path, f'/animcmp/inputs/{k}.glb')
    game = lengths.remote('open'); pre = lengths.remote('preset'); print('clips', game, pre, flush=True)
    work = [(k, s, c, game[c]) for s in ('full', 'close') for k in ('open', 'tripo') for c in GAME_CLIPS]
    work += [('preset', 'wide', c, min(pre[c], PRESET_CAP[c])) for c in GAME_CLIPS]
    jobs = [(k, s, c, list(range(i, min(i + chunk, n)))) for k, s, c, n in work for i in range(0, n, chunk)]
    if test: jobs = [(k, s, c, [n // 2]) for k, s, c, n in work if c == 'slash']        # framing check
    print(len(jobs), 'jobs', sum(len(j[3]) for j in jobs), 'frames', flush=True)
    for r in render.starmap(jobs, order_outputs=False): print(r, flush=True)
    for k, s, c in sorted({j[:3] for j in jobs}):
        d = Path(output, s, k, c); d.mkdir(parents=True, exist_ok=True)
        for e in cache.listdir(f'/animcmp/frames/{s}/{k}/{c}'):
            (d / Path(e.path).name).write_bytes(b''.join(cache.read_file(e.path)))
    print('downloaded to', output, flush=True)
