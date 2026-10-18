"""Validate exported cheek apertures, chin shells and shared roughness maps."""
import argparse,hashlib,io,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);a=p.parse_args()
data=Path(a.model).read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);binary=data[28+length:]
def accessor(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];size=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*size),size))
def get_mesh(name):
    node=next(n for n in doc['nodes'] if n.get('name')==name);positions=[];faces=[];count=0;materials=set()
    for part in doc['meshes'][node['mesh']]['primitives']:
        p=accessor(part['attributes']['POSITION']);positions.append(p);faces.append(accessor(part['indices']).reshape(-1,3)+count);count+=len(p);materials.add(part['material'])
        if 'TEXCOORD_0' in part['attributes']:
            uv=accessor(part['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1
    return np.concatenate(positions),np.concatenate(faces),materials

def ray_hits(x,z,positions,faces):
    t=positions[faces][:,:,:2].astype(np.float64);u=t[:,1]-t[:,0];v=t[:,2]-t[:,0];q=np.array([x,z])-t[:,0]
    cross=lambda a,b:a[:,0]*b[:,1]-a[:,1]*b[:,0]
    d=cross(u,v);valid=abs(d)>1e-12;s=cross(q,v)[valid]/d[valid];r=cross(u,q)[valid]/d[valid]
    return bool(((s>=-1e-6)&(r>=-1e-6)&(s+r<=1+1e-6)).any())

plates=['Menpo continuous '+kind+' plate '+str(sign) for kind in ['cheek','jaw'] for sign in [-1,1]]
rivets=['Menpo jaw rivet '+str(sign)+' '+str(i) for sign in [-1,1] for i in range(3)]
checks=[]
for name in ['Menpo cheek vent frame -1','Menpo cheek vent frame 1','Menpo reconstructed chin shield','Menpo chin brass inlay']+plates+rivets:
    positions,faces,materials=get_mesh(name);unique,inverse=np.unique(positions,axis=0,return_inverse=True);triangles=inverse[faces]
    edges=np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]);_,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
    assert (counts==2).all(),name+' is not closed/manifold'
    graph=[set() for _ in unique]
    for x,y in edges:graph[x].add(y);graph[y].add(x)
    reached={0};pending=[0]
    while pending:
        for i in graph[pending.pop()]-reached:reached.add(i);pending.append(i)
    assert len(reached)==len(unique),name+' has detached parts'
    fitted=(positions*np.float32(.26)+np.array([0,1.44,.005],dtype=np.float32))[faces]
    area=np.linalg.norm(np.cross(fitted[:,1]-fitted[:,0],fitted[:,2]-fitted[:,0]),axis=1)
    assert (area>=1e-12).all(),name+' has slivers after fitting'
    for z in [.405,.420]:assert not ray_hits(0,z,positions,faces),name+' covers the mouth opening'
    if 'vent frame' in name or name in plates:
        for sign in [-1,1]:
            for x,z in [(.074,.550),(.12,.71),(.17,.71),(.23,.73)]:assert not ray_hits(sign*x,z,positions,faces),name+' obstructs nostril/eye test ray'
    if 'vent frame' in name or name in plates:
        sign=-1 if name.endswith('-1') else 1
        for z in [.43,.48,.53]:
            for x in [sign*.19,sign*.202,sign*.214]:assert not ray_hits(x,z,positions,faces),name+' aperture is obstructed'
    checks.append({'object':name,'closed_connected':True,'near_zero_triangles_at_fit_scale':0,'mouth_clear':True})

finish_checks=[]
for name in ['Menpo repaired lacquer','Menpo aged brass shared finish']:
    material=next(m for m in doc['materials'] if m.get('name')==name);pbr=material['pbrMetallicRoughness'];texture=doc['textures'][pbr['metallicRoughnessTexture']['index']]
    image=doc['images'][texture['source']];v=doc['bufferViews'][image['bufferView']];start=v.get('byteOffset',0)
    pixels=np.asarray(Image.open(io.BytesIO(binary[start:start+v['byteLength']])).convert('RGB'))
    rough=pixels[:,:,1]/255*pbr.get('roughnessFactor',1)
    assert rough.min()>.30 and rough.max()<.70 and np.ptp(rough)>.02,name+' has missing/invalid roughness variation'
    finish_checks.append({'material':name,'roughness_min':float(rough.min()),'roughness_max':float(rough.max()),'embedded':True})
# Required surfaces must actually use the same exported lacquer material.
red=next(i for i,m in enumerate(doc['materials']) if m.get('name')=='Menpo repaired lacquer')
for name in ['Menpo reconstructed nasal shell','Menpo reconstructed upper lip','Menpo continuous eye rim and return','Menpo reconstructed chin shield','Menpo cheek vent frame -1','Menpo cheek vent frame 1']+plates:
    assert red in get_mesh(name)[2],name+' does not share the lacquer finish'
gold=next(i for i,m in enumerate(doc['materials']) if m.get('name')=='Menpo aged brass shared finish')
for name in rivets:assert gold in get_mesh(name)[2],name+' does not share the brass finish'
report={'model':a.model,'sha256':hashlib.sha256(data).hexdigest(),'passed':True,'checks':checks,'vent_aperture_test_rays_clear':True,'eye_nostril_test_rays_clear':True,'cheek_jaw_plates':len(plates),'jaw_rivets':len(rivets),'shared_finish':finish_checks,
        'scope':'New repair pieces only; recessed cloth backings are separate. Does not certify the entire generated head or animation.'}
Path(a.report).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
