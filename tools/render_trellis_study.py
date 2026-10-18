"""Render actual GLB geometry in Blender; no image-to-plane mockup.
Use /workspace/yukimura-tools/render-env/bin/python tools/render_trellis_study.py.
"""
from pathlib import Path
import argparse,json,math,time
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--model',default='docs/experiments/future-sanada/future-sanada.glb');p.add_argument('--output',default='docs/experiments/future-sanada');p.add_argument('--size',type=int,default=1000);p.add_argument('--samples',type=int,default=32);p.add_argument('--basecolor-only',action='store_true',help='Display baked-color assets with metallic=0; leave source GLB unchanged');a=p.parse_args()
out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert meshes,'GLB has no meshes'
if a.basecolor_only:
 for material in {m for o in meshes for m in o.data.materials if m and m.use_nodes}:
  bsdf=material.node_tree.nodes.get('Principled BSDF')
  if bsdf:bsdf.inputs['Metallic'].default_value=0

points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
low=Vector(tuple(min(v[i] for v in points) for i in range(3)));high=Vector(tuple(max(v[i] for v in points) for i in range(3)));height=high.z-low.z
assert height>0
# Normalize with a parent so all imported transformations remain intact.
root=bpy.data.objects.new('Asset normalization',None);bpy.context.collection.objects.link(root)
for o in list(bpy.context.scene.objects):
 if o!=root and o.parent is None:o.parent=root
scale=2.0/height;root.scale=(scale,)*3;root.location=(-(low.x+high.x)*.5*scale,-(low.y+high.y)*.5*scale,-low.z*scale)
bpy.context.view_layer.update()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=a.size;scene.render.resolution_y=a.size;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.10,.12,.15,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,energy,color,size):
 bpy.ops.object.light_add(type='AREA',location=location);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1))
area('Large warm key',(3,-4,5),650,(1,.88,.73),4);area('Soft cool fill',(-4,-2,3),450,(.7,.83,1),4);area('Back edge',(1,3,4),750,(1,.94,.8),3)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006));floor=bpy.context.object;floor.name='Studio floor';mat=bpy.data.materials.new('Slate');mat.diffuse_color=(.035,.042,.055,1);mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.035,.042,.055,1);bsdf.inputs['Roughness'].default_value=.73;floor.data.materials.append(mat)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.35;camera.data.lens=60
report={'renderer':bpy.app.version_string,'device':'CPU','samples':a.samples,'image_size':[a.size,a.size],'geometry_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'triangles':sum(sum(len(poly.vertices)-2 for poly in o.data.polygons) for o in meshes),'material_count':len({m.name for o in meshes for m in o.data.materials if m}),'images':[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.type=='IMAGE'],'views':[]}
report['display_override']='metallic=0 for baked-color-only source' if a.basecolor_only else None
original_materials={o.name:list(o.data.materials) for o in meshes}
clay=bpy.data.materials.new('Geometry inspection clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.45,.47,.5,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
# glTF +Z is front; Blender's import maps this to -Y.
for name,degrees in [('front',0),('three-quarter',35),('side',90),('back',180),('clay',0)]:
 if name=='clay':
  for o in meshes:
   for i in range(len(o.data.materials)):o.data.materials[i]=clay
 angle=math.radians(degrees);camera.location=(math.sin(angle)*5,-math.cos(angle)*5,1.5);aim(camera,(0,0,1.03));scene.render.filepath=str(out/f'{name}.png');started=time.monotonic();bpy.ops.render.render(write_still=True);report['views'].append({'name':name,'degrees':degrees,'seconds':round(time.monotonic()-started,2)})
for o in meshes:
 for i,m in enumerate(original_materials[o.name]):o.data.materials[i]=m
bpy.ops.wm.save_as_mainfile(filepath=str(out/'future-sanada-studio.blend'))
(out/'render-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
