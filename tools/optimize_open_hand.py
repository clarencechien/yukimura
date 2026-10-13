"""Bake the CC0 hand study to a posed-bind, skinned PBR atlas and two GLB LODs."""
from pathlib import Path
import bpy, json, math, time
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'assets/optimized/open-hand';OUT.mkdir(parents=True,exist_ok=True)
start=time.perf_counter()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/cinema/open-hand-study.blend'))
s=bpy.context.scene;s.frame_set(24);s.render.engine='CYCLES';s.cycles.samples=16
s.render.threads_mode='FIXED';s.render.threads=4
s.render.bake.margin=8;s.render.bake.use_clear=True;s.render.bake.use_selected_to_active=False
rig=bpy.data.objects['Open hand rig'];hand=bpy.data.objects['MPFB right hand — CC0 anatomy base']
source=[hand]+[o for o in s.objects if o.get('study_component')=='open-source-hand-kote']
source_triangles=0
for o in source:
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();source_triangles+=len(m.loop_triangles);e.to_mesh_clear()
hand.modifiers['anatomical surface smoothing'].levels=1
for o in source:
 if o.type=='CURVE':o.data.bevel_resolution=0
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();parts=[]
for o in source:
 e=o.evaluated_get(deps);mesh=bpy.data.meshes.new_from_object(e,preserve_all_data_layers=True,depsgraph=deps)
 mesh.transform(o.matrix_world);part=bpy.data.objects.new('baked '+o.name,mesh);s.collection.objects.link(part)
 if o==hand:
  for g in o.vertex_groups:part.vertex_groups.new(name=g.name)
 else:
  bone=o.parent_bone;g=part.vertex_groups.new(name=bone);g.add(list(range(len(mesh.vertices))),1,'REPLACE')
 parts.append(part)
# All evaluated deformations, including the grip contact, become the new bind geometry.
bpy.ops.object.select_all(action='DESELECT')
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='Sanada kote LOD0'
for o in list(s.objects):
 if o not in (obj,rig):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
rig.animation_data_clear();bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
# Reduce the evaluated armor and continuous hand before creating the atlas.
dec=obj.modifiers.new("near-view budget","DECIMATE");dec.ratio=.38
bpy.ops.object.modifier_apply(modifier=dec.name)
# Four skin influences per vertex, matching standard glTF skin attributes.
for v in obj.data.vertices:
 groups=sorted([(g.group,g.weight) for g in v.groups],key=lambda p:p[1],reverse=True)
 total=sum(w for i,w in groups[:4]);assert total>0
 for i,w in groups:obj.vertex_groups[i].remove([v.index])
 for i,w in groups[:4]:obj.vertex_groups[i].add([v.index],w/total,'REPLACE')
while obj.data.uv_layers:obj.data.uv_layers.remove(obj.data.uv_layers[0])
obj.data.uv_layers.new(name='Game atlas')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006,area_weight=1,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
materials=list(obj.data.materials)
def target(name,space):
 im=bpy.data.images.new(name,width=1024,height=1024,alpha=False);im.colorspace_settings.name=space
 for m in materials:
  n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.nodes.active=n
 return im
def save(im):
 im.filepath_raw=str(OUT/(im.name+'.png'));im.file_format='PNG';im.save()
base=target('kote-basecolor','sRGB');bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'});save(base)
normal=target('kote-normal','Non-Color');bpy.ops.object.bake(type='NORMAL');save(normal)
# glTF ORM convention: R occlusion (1 here), G roughness, B metallic.
for m in materials:
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');out=next(a for a in n if a.type=='OUTPUT_MATERIAL')
 combine=n.new('ShaderNodeCombineColor');combine.inputs[0].default_value=1
 for dst,name in ((1,'Roughness'),(2,'Metallic')):
  inp=p.inputs[name]
  if inp.is_linked:l.new(inp.links[0].from_socket,combine.inputs[dst])
  else:combine.inputs[dst].default_value=inp.default_value
 emit=n.new('ShaderNodeEmission');l.new(combine.outputs[0],emit.inputs[0]);l.new(emit.outputs[0],out.inputs['Surface'])
orm=target('kote-orm','Non-Color');bpy.ops.object.bake(type='EMIT');save(orm)
mat=bpy.data.materials.new('Kote baked PBR');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
for im,kind in ((base,'base'),(normal,'normal'),(orm,'orm')):
 tex=n.new('ShaderNodeTexImage');tex.image=im
 if kind=='base':l.new(tex.outputs['Color'],p.inputs['Base Color'])
 elif kind=='normal':
  nm=n.new('ShaderNodeNormalMap');l.new(tex.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
 else:
  sep=n.new('ShaderNodeSeparateColor');l.new(tex.outputs['Color'],sep.inputs[0]);l.new(sep.outputs[1],p.inputs['Roughness']);l.new(sep.outputs[2],p.inputs['Metallic'])
obj.data.materials.clear();obj.data.materials.append(mat)
for poly in obj.data.polygons:poly.material_index=0
obj.parent=rig;arm=obj.modifiers.new('game skin','ARMATURE');arm.object=rig
obj['license']='MPFB anatomical mesh and weights CC0-1.0; original armor generated in this repository'
obj['bind_pose']='Fixed grip; original open/close animation intentionally omitted; contact baked into bind mesh.'
# Store editable atlas scene, then export each LOD separately with its skeleton.
bpy.context.preferences.filepaths.save_version=0
for im in (base,normal,orm):im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kote-game.blend'),compress=True)
report={'source_triangles':source_triangles,'source_objects':len(source),'bones':len(rig.data.bones),'atlas_resolution':1024,'texture_count':3,'bind_pose':'grip','animation_clips':0,'lods':[]}
for lod,ratio in ((0,1),(1,.45)):
 if lod:
  dec=obj.modifiers.new('distance LOD','DECIMATE');dec.ratio=ratio
  bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_move_up(modifier=dec.name)
  bpy.ops.object.modifier_apply(modifier=dec.name)
 obj.name=f'Sanada kote LOD{lod}'
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True)
 path=OUT/f'kote-lod{lod}.glb'
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=False,export_skins=True,export_apply=False,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT')
 obj.data.calc_loop_triangles();report['lods'].append({'file':path.name,'triangles':len(obj.data.loop_triangles),'vertices':len(obj.data.vertices),'bytes':path.stat().st_size})
report['seconds']=round(time.perf_counter()-start,2)
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
