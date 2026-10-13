"""Extend the straight tachi grip to cover both anatomical hands, preserving UVs.
Fresh builds author this length in build_models.py; this migrates an existing kit.
"""
from pathlib import Path
import os,json,bpy
from mathutils import Vector
from samurai_rig import point,weapon_point
from gltf_assets import share_images
ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path(os.environ.get('MODEL_SOURCE',ROOT/'assets/source/samurai-kit.blend'))
OUT=Path(os.environ.get('MODEL_OUTPUT',ROOT/'public/models'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for layer in bpy.context.view_layer.layer_collection.children:
 if layer.name.startswith('20_'):layer.exclude=True
mesh=bpy.data.objects['ieyasu_runtime'];rig=mesh.parent
assert not mesh.get('extended_tachi_hilt'), 'Hilt already migrated'
origin=point(.47,-.16,.91);axis=(weapon_point(Vector((.47,-.16,1.91)))-origin).normalized()
a=(.79-.91)*1.10;b=(1.05-.91)*1.10;new_a=(.70-.91)*1.10
radius=.022*.9
weapon=mesh.vertex_groups['weapon'].index
ids=[]
for v in mesh.data.vertices:
 if not any(g.group==weapon and g.weight>.99 for g in v.groups):continue
 delta=v.co-origin;t=delta.dot(axis);r=(delta-axis*t).length
 if a-1e-5<=t<=b+1e-5 and r<=radius+1e-5:ids.append(v.index)
assert len(ids)>=12,ids
assert min((mesh.data.vertices[i].co-origin).dot(axis) for i in ids)<a+1e-5

def stretch(p):
 t=(p-origin).dot(axis);return p+axis*(new_a+(t-a)/(b-a)*(b-new_a)-t)
for i in ids:mesh.data.vertices[i].co=stretch(mesh.data.vertices[i].co)
mesh.data.update();mesh['extended_tachi_hilt']=True
seen=set();masters=0
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('part_name')=='katana.hilt' and o.data not in seen:
  seen.add(o.data);masters+=1
  for v in o.data.vertices:v.co=stretch(v.co)
  rest=o.data.attributes.get('RestPosition')
  if rest:
   for value in rest.data:value.vector=stretch(value.vector)
  o.data.update()
rig.location=(0,0,0);rig.hide_set(False);rig.hide_render=False;mesh.hide_set(False);mesh.hide_render=False
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.context.scene.render.fps=int(rig.get('animation_fps',90))
path=OUT/'ieyasu.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
report=json.loads((OUT/'manifest.json').read_text());report['shared_textures'].update(share_images(path));report['shared_texture_bytes']=sum(report['shared_textures'].values());report['variants']['ieyasu']['bytes']=path.stat().st_size
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
rig.location=(0,3.5,0);rig.hide_render=True;mesh.hide_render=True
for layer in bpy.context.view_layer.layer_collection.children:
 if layer.name.startswith('20_'):layer.exclude=False
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),compress=True)
print(json.dumps({'runtime_vertices_extended':len(ids),'source_meshes_extended':masters,'hilt_length_m':b-new_a}))
