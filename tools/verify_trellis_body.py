"""Verify the actual exported full-body pass, including hand source and coverage."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);a=p.parse_args();root=Path(a.directory)
report=json.loads((root/'refinement-report.json').read_text())

def read(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);buf=raw[28+n:]
 def accessor(i):
  d=doc['accessors'][i];v=doc['bufferViews'][d['bufferView']];typ={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[d['componentType']];width={'VEC3':3,'VEC2':2,'SCALAR':1}[d['type']];size=np.dtype(typ).itemsize
  return np.ndarray((d['count'],width),typ,buf,v.get('byteOffset',0)+d.get('byteOffset',0),strides=(v.get('byteStride',width*size),size)).copy()
 meshes={}
 for node in doc['nodes']:
  if 'mesh' not in node:continue
  # The builder deliberately bakes object transforms before exporting.
  assert 'matrix' not in node and 'rotation' not in node and 'scale' not in node and 'translation' not in node,node['name']+' has unexpected transforms'
  points=[];faces=[];materials=set();count=0
  for part in doc['meshes'][node['mesh']]['primitives']:
   pos=accessor(part['attributes']['POSITION']);points.append(pos);faces.append(accessor(part['indices']).astype(np.int64).reshape(-1,3)+count);count+=len(pos);materials.add(part['material'])
   assert np.isfinite(pos).all()
   if 'TEXCOORD_0' in part['attributes']:assert np.isfinite(accessor(part['attributes']['TEXCOORD_0'])).all()
  meshes[node['name']]=(np.concatenate(points),np.concatenate(faces),materials)
 return doc,meshes,hashlib.sha256(raw).hexdigest()

def topology(positions,faces):
 unique,inv=np.unique(np.round(positions,7),axis=0,return_inverse=True);f=inv[faces]
 edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
 assert (counts==2).all(),'open or nonmanifold logical edges'
 q=positions[faces];areas=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);assert (areas>=1e-12).all(),'degenerate triangles'
 return len(f)

high,parts,sha=read(root/'body-refined.glb');preview,preview_parts,preview_sha=read(root/'body-preview.glb')
expected={'torso','shoulders','arms','hands','waist','legs','feet'};assert set(report['regions'])==expected
checks={};failures=[]
for region,names in report['regions'].items():
 triangles=0
 for name in names:
  assert name in parts,name
  try:triangles+=topology(*parts[name][:2])
  except AssertionError as e:failures.append(name+': '+str(e))
 checks[region]={'closed_parts':len(names),'triangles':triangles}
assert not failures,'; '.join(failures)
# Joining shared-material parts must preserve their geometry and triangles.
for group in report['preview_groups']:
 pos,faces,mats=preview_parts[group['name']];topology(pos,faces)
 author_names=report['regions'][group['region']]
 mat_name=group['name'].split(group['region']+' ',1)[1]
 author=[parts[n] for n in author_names if any(high['materials'][i]['name']==mat_name for i in parts[n][2])]
 assert sum(len(f) for _,f,_ in author)==len(faces),group['name']+' lost triangles'
# Head is inherited from the already-refined static fitting, unchanged in space.
_,before,_=read(Path(report['source']));head_count=0
for name,(positions,faces,mats) in before.items():
 if name=='Body with old head region removed':continue
 assert name in parts,name
 old=np.unique(np.round(positions,6),axis=0);now=np.unique(np.round(parts[name][0],6),axis=0)
 assert old.shape==now.shape and np.allclose(old,now,atol=2e-6,rtol=0),name+' head geometry changed'
 assert len(faces)==len(parts[name][1]);head_count+=1
hands=[]
for sign in [-1,1]:
 pos,faces,mats=parts['CC0 anatomical glove '+str(sign)];tips=report['finger_tip_landmarks_blender'][str(sign)];distances=[]
 assert len(tips)==5
 for point in tips.values():
  x,y,z=point;distance=float(np.linalg.norm(pos-np.array([x,z,-y]),axis=1).min());assert distance<.018,distance;distances.append(distance)
 hands.append({'side':sign,'finger_chains':5,'max_tip_to_vertex_distance':max(distances),'closed':True})
knees=[]
for sign in [-1,1]:
 shield=parts['Knee shield '+str(sign)][0];lining=parts['Leg indigo lining '+str(sign)][0]
 distances=[]
 for start in range(0,len(shield),128):
  distances.extend(np.linalg.norm(shield[start:start+128,None,:]-lining[None,:,:],axis=2).min(axis=1))
 clearance=float(max(distances));assert clearance<.020,('floating knee',sign,clearance)
 knees.append({'side':sign,'max_shield_vertex_to_lining_vertex_distance':clearance})
assert hashlib.sha256(Path(report['hand_source']['file']).read_bytes()).hexdigest()==report['hand_source']['sha256']
assert report['hand_source']['asset_license']=='CC0-1.0'
# Textures must be embedded and PBR finish maps survive glTF export.
for doc in [high,preview]:
 assert all('bufferView' in image for image in doc['images'])
 for name in report['shared_materials']:
  mat=next(m for m in doc['materials'] if m['name']==name);pbr=mat['pbrMetallicRoughness'];assert 'baseColorTexture' in pbr and 'metallicRoughnessTexture' in pbr and 'normalTexture' in mat,name
 assert not doc.get('skins') and not doc.get('animations')
result={'passed':True,'high_sha256':sha,'preview_sha256':preview_sha,'regions':checks,'head_meshes_preserved':head_count,'hands':hands,'knees':knees,'preview_groups':len(report['preview_groups']),'high_meshes':len(parts),'preview_meshes':len(preview_parts),'embedded_pbr_textures':True,'limits':['Logical edge checks use 1e-7 position rounding; no global self-intersection proof','Knee fit uses nearest vertices, not a signed collision or binding test','Static fitting only, no rigging or weapon-contact animation','No physical mobile performance measurement']}
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
