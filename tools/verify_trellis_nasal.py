"""Check exported repair topology, actual nasal apertures and shared color tile."""
import argparse,io,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True);args=p.parse_args()
data=Path(args.model).read_bytes();length=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+length]);binary=data[28+length:]
def accessor(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];size=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,
                      offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*size),size))
def mesh(name):
    node=next(n for n in doc['nodes'] if n.get('name')==name);positions=[];faces=[];count=0
    primitives=doc['meshes'][node['mesh']]['primitives']
    for primitive in primitives:
        xyz=accessor(primitive['attributes']['POSITION']);positions.append(xyz)
        faces.append(accessor(primitive['indices']).reshape(-1,3)+count);count+=len(xyz)
        uv=accessor(primitive['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all()
        assert uv.min()>=0 and uv.max()<=1, name+' outside shared texture tile'
    return np.concatenate(positions),np.concatenate(faces),primitives

def closed_connected(positions,faces):
    # Weld exact exported positions only. Decimal rounding merged six distinct
    # bevel vertices in the inspected source and falsely produced 4-face edges.
    unique,inverse=np.unique(positions,axis=0,return_inverse=True);tris=inverse[faces]
    edges=np.concatenate([tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]])
    _,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
    assert (counts==2).all(), 'Open/nonmanifold repair edge'
    neighbours=[set() for _ in unique]
    for a,b in edges:neighbours[a].add(b);neighbours[b].add(a)
    reached={0};pending=[0]
    while pending:
        for i in neighbours[pending.pop()]-reached:reached.add(i);pending.append(i)
    assert len(reached)==len(unique), 'Detached repair fragment'

def covered(xy,positions,faces):
    pts=positions[faces][:,:,:2].astype(np.float64);u=pts[:,1]-pts[:,0];v=pts[:,2]-pts[:,0];q=np.array(xy)-pts[:,0]
    cross=lambda a,b:a[:,0]*b[:,1]-a[:,1]*b[:,0]
    determinant=cross(u,v);valid=np.abs(determinant)>1e-12
    a=cross(q,v)[valid]/determinant[valid];b=cross(u,q)[valid]/determinant[valid]
    return bool(((a>=-1e-6)&(b>=-1e-6)&(a+b<=1+1e-6)).any())
checks=[];materials=set()
for name in ['Menpo reconstructed nasal shell','Menpo reconstructed upper lip']:
    positions,faces,primitives=mesh(name);closed_connected(positions,faces)
    # Match the static body's scale/translation in float32, where small bevel
    # slivers can collapse even though the isolated head passed inspection.
    fitted=(positions*np.float32(.26)+np.array([0,1.44,.005],dtype=np.float32))[faces]
    doubled_area=np.linalg.norm(np.cross(fitted[:,1]-fitted[:,0],fitted[:,2]-fitted[:,0]),axis=1)
    assert (doubled_area>=1e-12).all(), name+' has near-zero triangles at fitting scale'
    # glTF X/Y correspond to Blender X/Z for these identity-transform meshes.
    for xy in [(0,.420),(0,.405),(-.190,.48),(.190,.48)]:
        assert not covered(xy,positions,faces), name+' covers preserved mouth/cheek aperture'
    if 'nasal' in name:
        for x in [-.074,.074]:assert not covered((x,.550),positions,faces), 'Nostril is filled'
        assert covered((0,.60),positions,faces), 'Nasal bridge is missing'
    for primitive in primitives:materials.add(primitive['material'])
    checks.append({'object':name,'closed_after_logical_weld':True,'single_connected_component':True,'near_zero_triangles_at_fit_scale':0,'mouth_and_cheek_test_rays_clear':True})
assert len(materials)==1, 'Repair parts no longer share their finish'
m=doc['materials'][materials.pop()];tex=m['pbrMetallicRoughness']['baseColorTexture']['index'];image=doc['images'][doc['textures'][tex]['source']]
v=doc['bufferViews'][image['bufferView']];pixels=np.asarray(Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGB'))
# Catch baking only the nose, which previously left the lip's UV area black.
assert pixels[:,:,0].min()>20, 'Unpainted black regions in shared lacquer tile'
report={'model':args.model,'passed':True,'checks':checks,'nostril_center_rays_clear':True,
        'shared_finish_tile_fully_painted':True,'scope':'New repair shells only; dark nostril backings excluded. Not full-head manifold/animation certification.'}
Path(args.report).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
