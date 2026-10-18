"""Reuse the existing shoulder plate and cloth lining; preserve source files."""
from pathlib import Path
from PIL import Image, ImageFilter
import json, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
head=json.loads((OUT/'shared-head.json').read_text());fall=json.loads((OUT/'bridge.json').read_text())
parts={}
liningSource='headless-bridge.webp';liningBox=[182,52,202,66]
lining=np.array(Image.open(OUT/liningSource).convert('RGBA').crop(liningBox));assert (lining[:,:,3]>=250).all()
for name,torso in head['torsos'].items():
 if name=='unload':continue
 cap=next(f for f in fall['frames'] if f['id']==name)['parts']['cap']
 raw=Image.open(OUT/torso['url']).convert('RGBA');mask=Image.new('L',raw.size)
 mask.paste(Image.open(OUT/cap['url']).getchannel('A'),(cap['box'][0]-torso['box'][0],cap['box'][1]-torso['box'][1]))
 # A reusable quilted lining fills the vacated plate footprint, retaining the
 # original torso alpha. Texture is tiled at native scale, never stretched.
 region=np.array(mask.filter(ImageFilter.MaxFilter(3)))>0;a=np.array(raw)
 yy,xx=np.indices(region.shape);tile=lining[yy%lining.shape[0],xx%lining.shape[1],:3]
 a[region,:3]=tile[region]
 url=f'shoulderless-{name}.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
 parts[name]=dict(url=url,box=torso['box'],source=torso['url'],sourceSHA256=hashlib.sha256((OUT/torso['url']).read_bytes()).hexdigest(),cap=cap,maskExpansionPixels=1)
m=dict(baselineCommit='3eb80f3a439bd0552cc0178e39d789876d073577',start=1220,end=1500,cap={**fall['frames'][0]['parts']['cap'],'pivot':fall['frames'][0]['shoulder']},torsos=parts,lining=dict(source=liningSource,sourceSHA256=hashlib.sha256((OUT/liningSource).read_bytes()).hexdigest(),box=liningBox),keys=[dict(time=1260,angle=2,offset=[0,-6]),dict(time=1380,angle=10,offset=[-10,-12]),dict(time=1500,angle=14,offset=[0,-20])],method='Reuse existing fall-bridge-cap.webp at fixed size. Plate mount follows the shoulder with an authored collar offset. Four torso variants retain their alpha and replace the old plate footprint with native-scale tiled existing quilted lining. One-pixel mask expansion. Authored rotation, not shoulder biomechanics.')
(OUT/'shared-shoulder.json').write_text(json.dumps(m,indent=2)+'\n')
print('Prepared four shoulderless torsos; reused existing fall-bridge-cap.webp.')
