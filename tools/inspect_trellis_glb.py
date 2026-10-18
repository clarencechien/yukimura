"""Validate actual geometry and embedded PBR texture accessors in the exported GLB."""
from pathlib import Path
import struct,json,hashlib,argparse
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('--model',default='docs/experiments/future-sanada/future-sanada.glb')
p.add_argument('--material-profile',choices=['pbr','basecolor'],default='pbr')
p.add_argument('--report',help='Optional output report path for multi-model studies')
args=p.parse_args()
path=Path(args.model);data=path.read_bytes()
magic,version,total=struct.unpack_from('<III',data);assert magic==0x46546c67 and version==2 and total==len(data)
chunks={};offset=12
while offset<len(data):
 length,kind=struct.unpack_from('<II',data,offset);chunks[kind]=data[offset+8:offset+8+length];offset+=8+length
j=json.loads(chunks[0x4e4f534a]);binary=chunks[0x004e4942]
def accessor(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];count=a['count'];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize;start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',n*item);return np.ndarray((count,n),dtype=dtype,buffer=binary,offset=start,strides=(stride,item))
positions=[];triangles=0;degenerate=0;missing_normals=0
for mesh in j['meshes']:
 for p in mesh['primitives']:
  assert p.get('mode',4)==4
  a=p['attributes'];pos=accessor(a['POSITION']);assert np.isfinite(pos).all()
  material=j.get('materials',[])[p['material']] if 'material' in p else {}
  texture_slots=[value for value in material.get('pbrMetallicRoughness',{}).values() if isinstance(value,dict) and 'index' in value]
  texture_slots += [material[k] for k in ['normalTexture','occlusionTexture','emissiveTexture'] if k in material]
  for slot in texture_slots:assert 'TEXCOORD_'+str(slot.get('texCoord',0)) in a, 'Textured primitive missing required UVs'
  for key in a:
   if key.startswith('TEXCOORD_'):assert np.isfinite(accessor(a[key])).all()
  if 'NORMAL' in a:assert np.isfinite(accessor(a['NORMAL'])).all()
  else:missing_normals+=1  # NORMAL is optional in glTF; importers derive it from triangles.
  idx=accessor(p['indices']).reshape(-1,3);assert idx.max()<len(pos)
  points=pos[idx];area=np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1);degenerate+=int((area<1e-12).sum());triangles+=len(idx);positions.append(pos)
allpos=np.concatenate(positions);bounds=[allpos.min(0).tolist(),allpos.max(0).tolist()];extent=(allpos.max(0)-allpos.min(0)).tolist();assert min(extent)>.01,'Unexpectedly flat geometry'
assert triangles>1000;assert j.get('materials');assert j.get('images');assert all('bufferView' in im for im in j['images']), 'Textures must be embedded'
materials=[]
for m in j['materials']:
 p=m.get('pbrMetallicRoughness',{});materials.append({'name':m.get('name'),'baseColorTexture':p.get('baseColorTexture'),'metallicRoughnessTexture':p.get('metallicRoughnessTexture'),'alphaMode':m.get('alphaMode','OPAQUE')})
assert any(m['baseColorTexture'] is not None for m in materials)
if args.material_profile=='pbr':
 assert any(m['metallicRoughnessTexture'] is not None for m in materials)
report={'file':path.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'vertices':len(allpos),'triangles':triangles,'degenerate_triangles':degenerate,'bounds':bounds,'extent':extent,'materials':materials,'embedded_images':len(j['images']),'skins':len(j.get('skins',[])),'animations':len(j.get('animations',[])),'validated':True}
report['material_profile']=args.material_profile
report['primitives_without_normals']=missing_normals
(Path(args.report) if args.report else path.with_name('mesh-inspection.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
