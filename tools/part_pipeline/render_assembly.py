"""Render an assembled character .blend: rest or a clip frame, from several angles.

  blender-python tools/part_pipeline/render_assembly.py --blend .tmp/stage4/body.blend --output DIR \
      [--pose slash:0.5] [--views front,three-quarter,side,back] [--clay]
"""
from pathlib import Path
import argparse, json, math, sys
import bpy
from mathutils import Vector

p = argparse.ArgumentParser(); p.add_argument('--blend', required=True); p.add_argument('--output', required=True)
p.add_argument('--pose', default='rest', help='rest, or clip:fraction'); p.add_argument('--views', default='front,three-quarter,side,back')
p.add_argument('--clay', action='store_true'); p.add_argument('--size', type=int, default=800); p.add_argument('--samples', type=int, default=16)
p.add_argument('--prefix', default=''); p.add_argument('--transparent', action='store_true', help='RGBA output, to composite on the concept sheets\' grey')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.open_mainfile(filepath=str(Path(a.blend).resolve()))
scene = bpy.context.scene
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
if a.pose != 'rest':
    clip, frac = a.pose.split(':'); act = next(x for x in bpy.data.actions if x.name.split('_')[0] == clip)
    rig.animation_data_create(); rig.animation_data.action = act
    f0, f1 = act.frame_range; scene.frame_set(round(f0 + (f1 - f0) * float(frac)))
else:
    if rig.animation_data: rig.animation_data.action = None
    for pb in rig.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.update()
meshes = [o for o in scene.objects if o.type == 'MESH' and o.visible_get()]
deps = bpy.context.evaluated_depsgraph_get()
pts = []
for o in meshes:
    e = o.evaluated_get(deps); m = e.to_mesh(); pts += [o.matrix_world @ m.vertices[k].co for k in range(0, len(m.vertices), 50)]; e.to_mesh_clear()
lo = Vector([min(v[i] for v in pts) for i in range(3)]); hi = Vector([max(v[i] for v in pts) for i in range(3)])
centre = (lo + hi) / 2; span = max(hi - lo) * 1.08
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = a.samples; scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = a.size; scene.render.film_transparent = a.transparent; scene.render.image_settings.color_mode = 'RGBA'; scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.10, .12, .15, 1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
def aim(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
for loc, energy, col in (((3, -4, 5), 900, (1, .88, .73)), ((-4, -2, 3), 600, (.7, .83, 1)), ((1, 4, 4), 900, (1, .94, .8))):
    bpy.ops.object.light_add(type='AREA', location=Vector(loc) * 1.4 + centre); L = bpy.context.object; L.data.energy = energy * 2; L.data.color = col; L.data.size = 5; aim(L, centre)
if a.clay:
    clay = bpy.data.materials.new('clay'); clay.use_nodes = True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.45, .47, .5, 1)
    for o in meshes:
        for i in range(len(o.data.materials)): o.data.materials[i] = clay
        if not o.data.materials: o.data.materials.append(clay)
bpy.ops.object.camera_add(); cam = bpy.context.object; scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = span
VIEWS = {'front': 0, 'three-quarter': 35, 'side': 90, 'back': 180, 'three-quarter-back': 215}
out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
for name in a.views.split(','):
    t = math.radians(VIEWS[name]); cam.location = centre + Vector((math.sin(t) * 6, -math.cos(t) * 6, 0)); aim(cam, centre)
    scene.render.filepath = str((out / f'{a.prefix}{name}.png').resolve()); bpy.ops.render.render(write_still=True)
print(json.dumps({'pose': a.pose, 'bounds': [list(map(lambda x: round(x, 3), lo)), list(map(lambda x: round(x, 3), hi))]}))
