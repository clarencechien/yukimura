"""Verify registration and report BOTH sprite boundaries; never assume an art improvement."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,math
R=Path(__file__).resolve().parents[1];O=R/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((O/'body-transition.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not m['adopted'];assert sha(R/m['source'])==m['sourceSHA256']
for ref in m['references']+[m['earlierStudy']]+m['revisionReferences']:assert sha(R/ref['path'])==ref['sha256']
a=np.array(Image.open(R/m['source']).convert('RGBA'));assert list(a.shape[1::-1])==m['sourceSize'];a[a[:,:,3]<=m['alphaCutoff']]=0
r=m['registration'];angle=math.radians(r['angle']);co=math.cos(angle);si=math.sin(angle);scale=r['scale'];x,y=r['sourceShoulder'];u,v=r['targetShoulder'];inverse=[co/scale,si/scale,x-(co*u+si*v)/scale,-si/scale,co/scale,y-(-si*u+co*v)/scale]
assert np.allclose(inverse,r['inverseAffine']);assert np.allclose([inverse[0]*u+inverse[1]*v+inverse[2],inverse[3]*u+inverse[4]*v+inverse[5]],[x,y]);assert abs(inverse[0]*inverse[1]+inverse[3]*inverse[4])<1e-8
world=Image.fromarray(a).transform((1152,768),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC);a=np.array(world);a[a[:,:,3]<=m['alphaCutoff']]=0;world=Image.fromarray(a);assert list(world.getbbox())==m['part']['box'];assert m['part']['box'][3]<=690
expected=np.array(world.crop(m['part']['box']));actual=np.array(Image.open(O/m['part']['url']).convert('RGBA'));assert np.array_equal(actual[:,:,3],expected[:,:,3]);visible=expected[:,:,3]>0;assert np.array_equal(actual[visible],expected[visible]);assert abs(actual.shape[0]*actual.shape[1]*4/1048576-m['textureRGBA8MiB'])<1e-10
rows=[]
for t in [1200,1220,1240,1320]:
 row=dict(time=t)
 for name,directory in [('default','body-baseline'),('candidate','body')]:
  base=O/'handoffs'/directory;before,after=[np.array(Image.open(base/f'{t}-{s}.png').convert('RGB')).astype(float) for s in ['before','after']];masks=[np.array(Image.open(base/f'{t}-{s}-body.png'))[:,:,3]>16 for s in ['before','after']];a,b=masks
  row[name]=dict(meanRGBDifference=float(np.abs(before-after).mean()),bodyMaskXorPixels=int(np.count_nonzero(a^b)),bodyMaskIoU=float(np.count_nonzero(a&b)/np.count_nonzero(a|b)))
 # Outside the painted interval actual browser pixels must remain unchanged.
 for s in (['before'] if t==1200 else ['after'] if t==1240 else ['before','after'] if t==1320 else []):
  assert np.array_equal(np.array(Image.open(O/'handoffs/body'/f'{t}-{s}.png')),np.array(Image.open(O/'handoffs/body-baseline'/f'{t}-{s}.png')))
 rows.append(row)
report=dict(passed=True,adopted=False,registration='Single uniform scale and rigid rotation; inverse anchor and visible pixels reproduced exactly; source hashes checked.',ground='Registered body exclusive bottom 687 <= ground 690; browser separately validates actual moving body bounds.',textureRGBA8MiB=m['textureRGBA8MiB'],measurements=rows,limits='RGB changes and alpha silhouettes quantify image cuts, not anatomy or aesthetic quality. New drawing worsens both endpoint changes; opt-in only.')
(O/'body-transition-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
