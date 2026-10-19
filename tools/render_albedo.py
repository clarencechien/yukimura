"""Unlit base-colour render (every BSDF replaced by emission of its base colour).

Separates texture problems from lighting: metallic gold reflecting a dark studio, or rim
light on lacquer, can look like a colour defect in shaded renders.
  python tools/render_albedo.py --model X.glb --output out.png --target -0.39,0.16,0.88 --span .35
"""
import argparse, math
import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--output', required=True)
p.add_argument('--target', default='0,0,.82', help='x,y,z in normalized body space (front = -Y)')
p.add_argument('--span', type=float, default=.7, help='orthographic width')
p.add_argument('--angle', type=float, default=0, help='degrees around Z; 0 = front, 180 = back')
p.add_argument('--size', type=int, default=600)
a = p.parse_args()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.model)
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    if not b: continue
    em = nt.nodes.new('ShaderNodeEmission')
    if b.inputs['Base Color'].links: nt.links.new(b.inputs['Base Color'].links[0].from_socket, em.inputs['Color'])
    else: em.inputs['Color'].default_value = b.inputs['Base Color'].default_value
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
s = bpy.context.scene; s.render.engine = 'CYCLES'; s.cycles.samples = 4; s.view_settings.view_transform = 'Standard'
s.render.resolution_x = s.render.resolution_y = a.size; s.render.filepath = a.output
cam = bpy.data.objects.new('albedo camera', bpy.data.cameras.new('albedo camera')); s.collection.objects.link(cam); s.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = a.span
t = Vector(tuple(map(float, a.target.split(',')))); ang = math.radians(a.angle)
cam.location = t + Vector((math.sin(ang) * 5, -math.cos(ang) * 5, .1))
cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.render.render(write_still=True)
