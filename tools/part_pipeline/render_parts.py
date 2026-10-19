"""Inspection renders for single generated parts: colour and clay from the front-left and the back-right.

Each part is scaled to fit a unit box and centred, with the body-v2 studio lights. One row per part:
  colour 30 deg | colour 210 deg | clay 30 deg | clay 210 deg

  python tools/part_pipeline/render_parts.py --parts .tmp/parts --seed 1615 --output .../stage3/renders
"""
from pathlib import Path
import argparse, json, math
import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--parts', required=True); p.add_argument('--seed', default='1615'); p.add_argument('--output', required=True)
p.add_argument('--names'); p.add_argument('--variant', default='high', help='high (open surface) or closed (remeshed)'); p.add_argument('--size', type=int, default=700); p.add_argument('--samples', type=int, default=16)
a = p.parse_args()
out = Path(a.output).resolve(); out.mkdir(parents=True, exist_ok=True)
names = a.names.split(',') if a.names else sorted(d.name for d in Path(a.parts).iterdir() if d.is_dir())
VIEWS = [('color', 30), ('color', 210), ('clay', 30), ('clay', 210)]
report = {}
for name in names:
    glb = Path(a.parts) / name / f'seed-{a.seed}' / f'{name}-{a.variant}.glb'
    if not glb.exists(): print('missing', glb); continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(v[i] for v in pts) for i in range(3)]); hi = Vector([max(v[i] for v in pts) for i in range(3)])
    root = bpy.data.objects.new('fit', None); bpy.context.collection.objects.link(root)
    for o in list(bpy.context.scene.objects):
        if o != root and o.parent is None: o.parent = root
    s = 1.6 / max(hi - lo); root.scale = (s,) * 3; root.location = -(lo + hi) / 2 * s
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = a.samples; scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = a.size; scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.10, .12, .15, 1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    def aim(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    for loc, energy, col in (((3, -4, 4), 650, (1, .88, .73)), ((-4, -2, 2), 450, (.7, .83, 1)), ((1, 3, 3), 750, (1, .94, .8)), ((-2, 4, -1), 250, (.8, .85, 1))):
        bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object; L.data.energy = energy; L.data.color = col; L.data.size = 4; aim(L, (0, 0, 0))
    bpy.ops.object.camera_add(); cam = bpy.context.object; scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0
    clay = bpy.data.materials.new('clay'); clay.use_nodes = True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.45, .47, .5, 1); clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .8
    orig = {o.name: list(o.data.materials) for o in meshes}
    for kind, deg in VIEWS:
        for o in meshes:
            for i in range(len(o.data.materials)): o.data.materials[i] = clay if kind == 'clay' else orig[o.name][i]
        t = math.radians(deg); cam.location = (math.sin(t) * -5, -math.cos(t) * 5, 1.2); aim(cam, (0, 0, 0))
        scene.render.filepath = str(out / f'{name}{"" if a.variant == "high" else "-" + a.variant}-{kind}-{deg}.png'); bpy.ops.render.render(write_still=True)
    report[name] = {'triangles': sum(len(f.vertices) - 2 for o in meshes for f in o.data.polygons), 'size_m_before_fit': [round(x, 3) for x in (hi - lo)]}
(out / 'render-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
