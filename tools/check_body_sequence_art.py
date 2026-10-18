"""Rebuild each registered sprite and verify native alpha support; report every handoff."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,math
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parents[1];O=R/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((O/'body-sequence.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(R/m['source'])==m['sourceSHA256'];assert not m['adopted']
for ref in m['references']:assert sha(R/ref['path'])==ref['sha256']
a=np.array(Image.open(R/m['source']).convert('RGBA'));assert list(a.shape[1::-1])==m['sourceSize'];a[a[:,:,3]<=m['alphaCutoff']]=0;source=Image.fromarray(a);c,s=math.cos(math.radians(m['angle'])),math.sin(math.radians(m['angle']));scale=m['scale'];texture=0
for f in m['frames']:
 r=f['registration'];cell=r['cell'];piece=source.crop(cell);aa=np.array(piece)[:,:,3];assert not aa[:,0].any() and not aa[:,-1].any() and not aa[0].any() and not aa[-1].any(),'cell cuts into a visible pose'
 x,y=r['sourceShoulder'];u,v=r['targetShoulder'];inverse=[c/scale,s/scale,x-cell[0]-(c*u+s*v)/scale,-s/scale,c/scale,y-cell[1]-(-s*u+c*v)/scale];assert np.allclose(inverse,r['inverseAffine']);assert r['targetShoulder']==f['pivot']
 world=piece.transform((1152,768),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC);a=np.array(world);a[a[:,:,3]<=m['alphaCutoff']]=0;world=Image.fromarray(a);assert list(world.getbbox())==f['part']['box'];expected=np.array(world.crop(f['part']['box']));actual=np.array(Image.open(O/f['part']['url']).convert('RGBA'));assert np.array_equal(expected[:,:,3],actual[:,:,3]);visible=expected[:,:,3]>0;assert np.array_equal(expected[visible],actual[visible]);texture+=actual.shape[0]*actual.shape[1]*4/1048576
 ys,xs=np.nonzero(a[:,:,3]>0);cells=np.concatenate([np.column_stack([xs+dx,ys+dy]) for dx,dy in [(0,0),(1,0),(1,1),(0,1)]]);hull=cells[ConvexHull(cells).vertices];assert set(map(tuple,hull))==set(map(tuple,f['supportHull']))
assert abs(texture-m['textureRGBA8MiB'])<1e-12
rows=[]
for t in [1200,1220,1240,1320,1440]:
 row=dict(time=t)
 for label,directory in [('default','sequence-baseline'),('candidate','sequence')]:
  base=O/'handoffs'/directory;a,b=[np.array(Image.open(base/f'{t}-{s}.png').convert('RGB')).astype(float) for s in ['before','after']];ma,mb=[np.array(Image.open(base/f'{t}-{s}-body.png'))[:,:,3]>16 for s in ['before','after']];row[label]=dict(meanRGBDifference=float(np.abs(a-b).mean()),bodyMaskXorPixels=int(np.count_nonzero(ma^mb)),bodyMaskIoU=float(np.count_nonzero(ma&mb)/np.count_nonzero(ma|mb)))
 rows.append(row)
for t,suffix in [(1200,'before'),(1440,'after')]:assert np.array_equal(np.array(Image.open(O/'handoffs/sequence'/f'{t}-{suffix}.png')),np.array(Image.open(O/'handoffs/sequence-baseline'/f'{t}-{suffix}.png')))
report=dict(passed=True,adopted=False,registration='All three use one scale and angle; source hashes, cutout margins, inverse transforms, visible RGBA and exact alpha-cell convex hulls reproduced.',textureRGBA8MiB=texture,measurements=rows,limits='Projected rigid support constraint, not anatomical knee simulation. RGB and silhouette changes measure cuts, not art quality. All four body cuts remain worse than default; candidate only.')
(O/'sequence-art-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
