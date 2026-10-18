"""Sample source-to-export surface distances and preserve a front-region source crop.
No remeshing or smoothing is applied to the source crop. Not a full Hausdorff test.
"""
from pathlib import Path
import json
import numpy as np
import bpy,bmesh
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
root=Path('docs/experiments/future-sanada/head-study');source=np.load('.tmp/head-study/source/source-geometry.npz',allow_pickle=False);v=source['vertices'];f=source['faces']
frame=json.loads((root/'high/render-report.json').read_text())['normalization'];low=np.array(frame['original_low']);high=np.array(frame['original_high']);scale=frame['scale'];center=np.array([(low[0]+high[0])/2,(low[1]+high[1])/2,low[2]])
norm=(v-center)*scale
regions={'eyes':(abs(norm[:,0])<.30)&(norm[:,2]>.63)&(norm[:,2]<.83)&(norm[:,1]<-.15),'crest':(abs(norm[:,0])<.28)&(norm[:,2]>.88)&(norm[:,2]<1.23)&(norm[:,1]<-.2),'mask':(abs(norm[:,0])<.30)&(norm[:,2]>.24)&(norm[:,2]<.64)&(norm[:,1]<-.2),'antlers':norm[:,2]>1.45}
samples={}
for name,mask in regions.items():
 idx=np.flatnonzero(mask);samples[name]=v[idx[np.linspace(0,len(idx)-1,min(5000,len(idx)),dtype=int)]]
result={'method':'5000 deterministic source vertex samples per region; nearest exported triangle, one directional; geometry only, not texture or semantic correctness','normalized_height':2,'source_vertices':len(v),'source_triangles':len(f),'variants':{}}
for name in ['high','light']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str((root/f'head-{name}.glb').resolve()));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');obj.data.transform(obj.matrix_world);obj.parent=None;obj.matrix_world=Matrix.Identity(4)
 bm=bmesh.new();bm.from_mesh(obj.data);bvh=BVHTree.FromBMesh(bm);bm.free();stats={}
 for region,points in samples.items():
  distances=np.array([bvh.find_nearest(Vector(p))[3] for p in points])*scale
  stats[region]={'samples':len(points),'median_normalized':float(np.median(distances)),'p95_normalized':float(np.quantile(distances,.95)),'maximum_normalized':float(distances.max())}
 result['variants'][name]=stats
mask=(abs(norm[:,0])<.35)&(norm[:,2]>.20)&(norm[:,2]<1.30)&(norm[:,1]<-.12)
keep=mask[f].all(1);crop=f[keep];used,remapped=np.unique(crop,return_inverse=True)
np.savez_compressed('.tmp/head-study/source/front-region.npz',vertices=v[used],faces=remapped.reshape(-1,3).astype(np.int32))
result['source_crop']={'vertices':len(used),'triangles':len(crop),'unchanged_vertex_positions':True,'boundary':'cropped for inspection; not a replacement head mesh'}
(root/'source-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
