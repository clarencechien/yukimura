"""Audit exported coin geometry and human-eye material, not just source parameters."""
from pathlib import Path
import json,struct
import numpy as np

root=Path('docs/experiments/future-sanada/head-study')
checks=[]
for relative in ['refined/head-refined.glb','refined/head-preview.glb']:
    data=(root/relative).read_bytes();length=struct.unpack_from('<I',data,12)[0]
    document=json.loads(data[20:20+length]);binary=data[28+length:]
    def accessor(index):
        a=document['accessors'][index];view=document['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        width={'SCALAR':1,'VEC3':3}[a['type']];size=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,
                          offset=view.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(view.get('byteStride',width*size),size))
    coins=[n for n in document['nodes'] if n.get('name','').startswith('Six coins /')]
    orbital=[n for n in document['nodes'] if n.get('name','').startswith('Human eyes and orbital skin')]
    assert len(coins)==6 and len(orbital)==1
    assert not any(n.get('name','').startswith(('Eye sclera ','Iris ','Pupil ','Temporary')) for n in document['nodes'])
    coin_checks=[]
    for node in coins:
        positions=[];indices=[];count=0
        for primitive in document['meshes'][node['mesh']]['primitives']:
            p=accessor(primitive['attributes']['POSITION']);positions.append(p)
            indices.append(accessor(primitive['indices']).reshape(-1,3)+count);count+=len(p)
        positions=np.concatenate(positions);indices=np.concatenate(indices)
        # Logical weld for the audit only; do not alter UV or normal seams.
        unique,inverse=np.unique(np.round(positions,7),axis=0,return_inverse=True)
        triangles=inverse[indices]
        edges=np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]])
        _,incidence=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
        assert (incidence==2).all(),node['name']+' has an open/nonmanifold coin edge'
        # glTF X/Y are the frontal projection. The center ray must pass through
        # the actual coin mesh; the separate dark seat behind it is excluded.
        center=(positions[:,:2].min(0)+positions[:,:2].max(0))/2
        pts=positions[indices][:,:,:2].astype(np.float64)
        u=pts[:,1]-pts[:,0];v=pts[:,2]-pts[:,0];q=center-pts[:,0]
        cross=lambda a,b:a[:,0]*b[:,1]-a[:,1]*b[:,0]
        determinant=cross(u,v);valid=np.abs(determinant)>1e-12
        aa=cross(q,v)[valid]/determinant[valid];bb=cross(u,q)[valid]/determinant[valid]
        assert not ((aa>=-1e-6)&(bb>=-1e-6)&(aa+bb<=1+1e-6)).any(),node['name']+' center hole is covered'
        coin_checks.append({'name':node['name'],'closed_after_logical_weld':True,'center_hole_open':True})
    human_mesh=document['meshes'][orbital[0]['mesh']]
    materials=[document['materials'][p['material']] for p in human_mesh['primitives']]
    assert any(m.get('normalTexture') and m['pbrMetallicRoughness'].get('baseColorTexture') for m in materials)
    checks.append({'file':relative,'coins':coin_checks,'orbital_patch':orbital[0]['name'],
                   'skin_color_and_normal_textures':True,'procedural_eye_caps_removed':True})
report={'passed':True,'checks':checks,
        'scope':'Coin closure/center opening and exported human-eye patch. Does not certify full-head topology, likeness, rig or performance.'}
(root/'part-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'variants':len(checks),'coins_per_variant':6}))
