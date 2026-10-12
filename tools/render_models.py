"""Optional inexpensive preview: blender -b assets/source/samurai-kit.blend --python tools/render_models.py"""
import bpy
from pathlib import Path
from mathutils import Vector
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.22,.30,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015))
floor=bpy.context.object
mat=bpy.data.materials.new('snow stage');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.13,.18,.22,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
floor.data.materials.append(mat)
for name,location,power,color,size in [('warm key',(-3,-4,6),1100,(1,.78,.60),4),('cold rim',(3,2,5),1400,(.55,.72,1),3),('soft fill',(0,-5,2),180,(.75,.83,1),5)]:
    bpy.ops.object.light_add(type='AREA',location=location)
    light=bpy.context.object;light.name=name;light.data.energy=power;light.data.color=color;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1400;scene.render.resolution_y=700;scene.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(3,-12,5))
cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.15))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=10.5;scene.camera=cam
path=Path(__file__).resolve().parent.parent/'docs/art/models-lineup.png'
scene.render.filepath=str(path)
bpy.ops.render.render(write_still=True)
