"""Render actual sculpt masters from the saved .blend, not concept artwork."""
import bpy
from pathlib import Path
from mathutils import Vector
scene=bpy.context.scene
for obj in scene.objects:obj.hide_render=True
masters=next(c for c in bpy.data.collections if c.name.startswith('20_YUKIMURA_HIGH'))
masters.hide_render=False;masters.hide_viewport=False
for obj in masters.objects:obj.hide_render=False;obj.hide_set(False)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.use_denoising=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
for name,pos,energy,color,size in [('soft key',(2,-4,5),550,(1,.83,.69),3),('cold rim',(-3,1,3),800,(.64,.76,1),2),('fill',(-2,-4,2),160,(.8,.85,1),2)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.0,-5.3,2.7));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1.65))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=3.9;scene.camera=camera
scene.render.resolution_x=1080;scene.render.resolution_y=1280;scene.render.resolution_percentage=100
target=Path(__file__).resolve().parent.parent/'docs/art'
scene.render.filepath=str(target/'hero-highpoly.png');bpy.ops.render.render(write_still=True)
# Neutral clay makes the actual geometry inspectable without painted detail.
clay=bpy.data.materials.new('inspection clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.34,.36,.38,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.6
scene.view_layers[0].material_override=clay
camera.location=(1.5,-4,2.35);camera.rotation_euler=(Vector((0,-.05,1.97))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=1.3
scene.render.resolution_x=1200;scene.render.resolution_y=1000
scene.render.filepath=str(target/'hero-highpoly-clay.png');bpy.ops.render.render(write_still=True)
