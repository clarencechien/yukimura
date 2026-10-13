"""Validate actual GLB payloads and Blender reimport including skin deformation."""
from pathlib import Path
import json,struct,math,bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'assets/optimized/open-hand'
report=[]
for lod in (0,1):
 path=OUT/f'kote-lod{lod}.glb';data=path.read_bytes();magic,version,length=struct.unpack_from('<III',data)
 assert magic==0x46546c67 and version==2 and length==len(data)
 n,kind=struct.unpack_from('<II',data,12);g=json.loads(data[20:20+n]);assert kind==0x4e4f534a
 assert len(g['meshes'])==1 and len(g['materials'])==1 and len(g['skins'])==1
 assert not g.get('animations');assert len(g['skins'][0]['joints'])==22
 assert all('uri' not in im for im in g['images'])
 primitives=g['meshes'][0]['primitives'];assert len(primitives)==1
 assert {'JOINTS_0','WEIGHTS_0','NORMAL','TEXCOORD_0','TANGENT'} <= primitives[0]['attributes'].keys()
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
 mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 def coords():
  bpy.context.view_layer.update();e=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());return [v.co.copy() for v in e.data.vertices]
 base=coords();assert all(math.isfinite(c) for v in base for c in v)
 sums=[sum(w.weight for w in v.groups) for v in mesh.data.vertices];assert max(abs(w-1) for w in sums)<1e-4
 bone=rig.pose.bones['lowerarm02.R'];bone.rotation_mode='XYZ';bone.rotation_euler.y=.15
 moved=coords();delta=max((a-b).length for a,b in zip(base,moved));assert delta>.001
 report.append({'lod':lod,'glb_bytes':len(data),'mesh_primitives':len(primitives),'materials':len(g['materials']),'embedded_images':len(g['images']),'bones':len(rig.data.bones),'reimported_vertices':len(base),'weight_sum_max_error':max(abs(w-1) for w in sums),'bone_deformation_max_m':delta})
(ROOT/'renders/open-hand/glb-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
