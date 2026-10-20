"""Quick low-sample Cycles contact sheet of a rigged, animated GLB: a few frames of every clip, front three-quarter view.

  blender-python tools/rig_check_render.py --glb .tmp/rig-open/rig-open.glb --output .tmp/rig-open/check.png \
      [--forward x] [--frames 4]
Clips are the GLB's animations; --forward x turns a +X-facing export (Tripo) to face -Y.
"""
from pathlib import Path
import argparse, math, sys, tempfile
import bpy
from mathutils import Vector
p = argparse.ArgumentParser()
p.add_argument('--glb', required=True); p.add_argument('--output', required=True)
p.add_argument('--forward', default='-y'); p.add_argument('--frames', type=int, default=4); p.add_argument('--size', type=int, default=360)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=a.glb)
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
top = rig
while top.parent: top = top.parent
root = bpy.data.objects.new('turn', None); scene.collection.objects.link(root); top.parent = root
if a.forward == 'x': root.rotation_euler.z = -math.pi / 2
actions = [x for x in bpy.data.actions]
print('actions', [(x.name, tuple(x.frame_range)) for x in actions])
# height from the rest pose
rig.animation_data_create(); rig.animation_data.action = None
for t in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(t)
bpy.context.view_layer.update()
meshes = [o for o in scene.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
zmin = min(q.z for q in pts); h = max(q.z for q in pts) - zmin
s = 2.0 / h; root.scale = (s, s, s); root.location.z = -zmin * s
scene.render.engine = 'CYCLES'; scene.cycles.samples = 12; scene.cycles.use_denoising = False   # no GL on the render boxes
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (.7, 0, -.5); scene.collection.objects.link(sun)
scene.render.resolution_x = a.size; scene.render.resolution_y = int(a.size * 1.4)
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True; scene.world.node_tree.nodes['Background'].inputs[1].default_value = .8
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 85; ang = math.radians(-30); cam.location = (4.4 * math.sin(ang) * -1, -4.4 * math.cos(ang), 1.2)
cam.rotation_euler = (Vector((0, 0, 1.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
tmp = Path(tempfile.mkdtemp()); tiles = []
for act in actions:
    rig.animation_data.action = act
    f0, f1 = act.frame_range
    row = []
    for k in range(a.frames):
        f = f0 + (f1 - f0) * k / max(a.frames - 1, 1)
        scene.frame_set(int(round(f))); out = tmp / f'{act.name}-{k}.png'
        scene.render.filepath = str(out); bpy.ops.render.render(write_still=True); row.append(out)
    tiles.append((act.name, row))
from PIL import Image, ImageDraw
W, Hh = a.size, int(a.size * 1.4)
sheet = Image.new('RGB', (W * a.frames, Hh * len(tiles)), (30, 30, 30)); d = ImageDraw.Draw(sheet)
for r, (name, row) in enumerate(tiles):
    for c, f in enumerate(row): sheet.paste(Image.open(f).convert('RGB'), (c * W, r * Hh))
    d.text((8, r * Hh + 8), name, fill=(255, 255, 255))
Path(a.output).parent.mkdir(parents=True, exist_ok=True); sheet.save(a.output); print('wrote', a.output)
