"""Repeatable close-up views of actual source/head/body geometry in Blender Cycles."""
import argparse,json,math,time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector,Matrix
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',required=True);p.add_argument('--raw',action='store_true');p.add_argument('--normalization-report');p.add_argument('--body',action='store_true');p.add_argument('--fullbody',action='store_true');p.add_argument('--views',default='front,three-quarter,side,back,eyes,crest,mask,clay');p.add_argument('--samples',type=int,default=24);p.add_argument('--size',type=int,default=1000);p.add_argument('--save-scene',action='store_true');a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True)
if a.raw:
 arrays=np.load(a.model,allow_pickle=False);vertices=arrays['vertices'];faces=arrays['faces'];mesh=bpy.data.meshes.new('Unmodified source topology');mesh.vertices.add(len(vertices));mesh.vertices.foreach_set('co',vertices.ravel());mesh.loops.add(faces.size);mesh.loops.foreach_set('vertex_index',faces.ravel());mesh.polygons.add(len(faces));mesh.polygons.foreach_set('loop_start',np.arange(0,faces.size,3));mesh.polygons.foreach_set('loop_total',np.full(len(faces),3));mesh.update();obj=bpy.data.objects.new('Raw head',mesh);bpy.context.collection.objects.link(obj)
else:bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for obj in objects:
 world=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=Matrix.Identity(4);obj.data.transform(world)
points=[Vector(c) for o in objects for c in o.bound_box];low=Vector([min(v[i] for v in points) for i in range(3)]);high=Vector([max(v[i] for v in points) for i in range(3)])
if a.normalization_report:
 frame=json.loads(Path(a.normalization_report).read_text())['normalization'];low=Vector(frame['original_low']);high=Vector(frame['original_high'])
scale=2/(high.z-low.z);center=Vector(((high.x+low.x)/2,(high.y+low.y)/2,low.z))
for obj in objects:
 obj.data.transform(Matrix.Scale(scale,4)@Matrix.Translation(-center))
 for poly in obj.data.polygons:poly.use_smooth=True
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=a.size;scene.render.resolution_y=a.size;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.world=bpy.data.worlds.new('Neutral inspection studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.11,.13,.16,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,energy,color,size):
 bpy.ops.object.light_add(type='AREA',location=location);obj=bpy.context.object;obj.name=name;obj.data.energy=energy;obj.data.color=color;obj.data.shape='DISK';obj.data.size=size;aim(obj,(0,0,1))
area('soft key',(2.5,-4,3.4),500,(1,.88,.76),3);area('eye fill',(-2,-3,1),350,(.80,.89,1),2.5);area('top rim',(1,2,3),650,(1,.94,.8),3)
clay=bpy.data.materials.new('Inspection clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.45,.46,.48,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
original={o.name:list(o.data.materials) for o in objects}
if a.raw:
 for obj in objects:obj.data.materials.append(clay)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.clip_start=.01
if a.fullbody:
 views={'front':(0,(0,0,1),2.22),'three-quarter':(30,(0,0,1),2.22),'side':(90,(0,0,1),2.22),'back':(180,(0,0,1),2.22),'clay':(0,(0,0,1),2.22),'torso':(0,(0,0,1.39),.78),'shoulder':(70,(.30,.02,1.44),.44),'rear-armor':(180,(0,0,1.28),.88),'hands':(0,(.40,-.02,.94),.40),'hand-back':(180,(.40,-.02,.94),.40),'waist':(0,(0,0,.87),.78),'legs':(0,(0,0,.34),.88),'boots':(35,(.04,0,.10),.88)}
elif a.body:
 views={'front':(0,(0,0,1.73),.66),'three-quarter':(25,(0,0,1.73),.66),'eyes':(0,(0,-.03,1.675),.25),'clay':(0,(0,0,1.73),.66)}
else:
 views={'front':(0,(0,0,1),2.22),'three-quarter':(28,(0,0,1),2.22),'side':(90,(0,0,1),2.22),'back':(180,(0,0,1),2.22),'eyes':(0,(0,0,.74),.83),'crest':(0,(0,0,1.1),.90),'mask':(0,(0,0,.43),.85),'clay':(0,(0,0,1),2.22)}
report={'model':a.model,'renderer':bpy.app.version_string,'device':'CPU','size':a.size,'samples':a.samples,'normalization':{'scale':scale,'original_low':list(low),'original_high':list(high)},'geometry_vertices':sum(len(o.data.vertices) for o in objects),'geometry_triangles':sum(len(p.vertices)-2 for o in objects for p in o.data.polygons),'views':[]}
for name in a.views.split(','):
 angle,target,span=views[name];angle=math.radians(angle);camera.location=Vector(target)+Vector((math.sin(angle)*5,-math.cos(angle)*5,0));aim(camera,target);camera.data.ortho_scale=span
 if name=='clay':
  for o in objects:
   for i in range(len(o.data.materials)):o.data.materials[i]=clay
 scene.render.filepath=str((out/f'{name}.png').resolve());t=time.monotonic();bpy.ops.render.render(write_still=True);report['views'].append({'name':name,'angle':angle,'target':target,'span':span,'seconds':time.monotonic()-t})
 if name=='clay':
  for o in objects:
   for i,m in enumerate(original[o.name]):o.data.materials[i]=m
if a.save_scene:bpy.ops.wm.save_as_mainfile(filepath=str((out/'head-inspection.blend').resolve()),compress=True)
(out/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
