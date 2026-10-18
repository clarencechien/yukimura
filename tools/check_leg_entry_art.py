"""Validate exact source crops and actual first-handoff browser pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,subprocess,math
OUT=Path('docs/routes/jigoku-2d/free-arm-settle');m=json.loads((OUT/'leg-entry.json').read_text());pixels=0
for p in [m['calf'],*m['parts'].values()]:
 assert hashlib.sha256((OUT/p['source']).read_bytes()).hexdigest()==p['sourceSHA256']
 im=Image.open(OUT/p['url']);pixels+=im.width*im.height

waist=m['preservedWaist'];assert hashlib.sha256((OUT/waist['source']).read_bytes()).hexdigest()==waist['sourceSHA256']
def region(size,box,overlap=0):
 pts=[[x-box[0]-overlap,y-box[1]] for x,y in m['seam']];poly=[*pts,[size[0]+100,pts[-1][1]],[size[0]+100,pts[0][1]]]
 mask=Image.new('L',size);ImageDraw.Draw(mask).polygon(poly,fill=255);preserved=Image.new('L',size);preserved.paste(Image.open(OUT/waist['source']).getchannel('A'),(waist['box'][0]-box[0],waist['box'][1]-box[1]));return (np.array(mask)>0)&(np.array(preserved)<=waist['alphaThreshold'])
for p in m['parts'].values():
 im=Image.open(OUT/p['source']).convert('RGBA');a=np.array(im);b=np.array(Image.open(OUT/p['url']).convert('RGBA'));expected=a[:,:,3].copy();expected[region(im.size,p['box'])]=0
 assert np.array_equal(b[:,:,3],expected);v=b[:,:,3]>0;assert v.any();assert np.array_equal(a[v],b[v])
p=m['calf'];base=m['parts']['lower'];im=Image.open(OUT/p['source']).convert('RGBA');a=np.array(im);alpha=a[:,:,3].copy();alpha[~region(im.size,base['box'],p['overlapPixels'])]=0;alpha[alpha<=p['alphaCutoff']]=0
b=np.array(Image.open(OUT/p['url']).convert('RGBA'));x=p['box'][0]-base['box'][0];y=p['box'][1]-base['box'][1];a=a[y:y+b.shape[0],x:x+b.shape[1]];alpha=alpha[y:y+b.shape[0],x:x+b.shape[1]];v=b[:,:,3]>0
assert np.array_equal(alpha,b[:,:,3]);assert np.array_equal(a[v],b[v])
# Test actual alpha cell corners, independently of the saved hull.
yy,xx=np.where(v);points=np.concatenate([np.column_stack([xx+dx+p['box'][0]-p['pivot'][0],yy+dy+p['box'][1]-p['pivot'][1]]) for dx,dy in [(0,0),(1,0),(0,1),(1,1)]])
script="import fs from 'node:fs';import {legEntryPose} from './docs/routes/jigoku-2d/free-arm-settle/leg-entry.mjs';const m=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/free-arm-settle/leg-entry.json'));console.log(JSON.stringify(Array.from({length:1001},(_,i)=>legEntryPose(1000+i/5,m))));"
poses=json.loads(subprocess.check_output(['node','--input-type=module','-e',script]));maxY=-1
for q in poses:
 r=math.radians(q['angle']);bottom=float((points[:,0]*math.sin(r)+points[:,1]*math.cos(r)+q['point']['y']).max());maxY=max(maxY,bottom);assert bottom<=m['groundY']
metrics=[]
for t in [1000,1180,1200,1220,1240]:
 row={'time':t}
 for name,folder in [('previous',Path('.tmp/calf-entry-baseline')),('current',OUT/'handoffs/calf')]:
  a=np.array(Image.open(folder/f'{t}-before.png').convert('RGB'),dtype=float);b=np.array(Image.open(folder/f'{t}-after.png').convert('RGB'),dtype=float)
  row[name]={'fullRGBMeanDelta':float(np.abs(a-b).mean()),'footRegionRGBMeanDelta':float(np.abs(a[415:485,500:590]-b[415:485,500:590]).mean()),'SHA256':{s:hashlib.sha256((folder/f'{t}-{s}.png').read_bytes()).hexdigest() for s in ['before','after']}}
 metrics.append(row)
 # After the first body swap, every actual pixel must remain unchanged.
 if t>=1200:
  for suffix in (['after'] if t==1200 else ['before','after']):
   assert (Path('.tmp/calf-entry-baseline')/f'{t}-{suffix}.png').read_bytes()==(OUT/'handoffs/calf'/f'{t}-{suffix}.png').read_bytes()
first=next(r for r in metrics if r['time']==1200);assert first['current']['footRegionRGBMeanDelta']<first['previous']['footRegionRGBMeanDelta']
a=np.array(Image.open('.tmp/calf-entry-baseline/1000-after.png').convert('RGB'),dtype=float);b=np.array(Image.open(OUT/'handoffs/calf/1000-after.png').convert('RGB'),dtype=float)
report=dict(passed=True,additionalRGBA8MiB=pixels*4/1048576,actualAlphaSamples=1001,maxVisibleCellY=maxY,groundY=m['groundY'],activationRGBMeanDifference=float(np.abs(a-b).mean()),activationPixelsOver8=int((np.abs(a-b).max(axis=2)>8).sum()),footRegionInCapture=[500,415,590,485],handoffs=metrics,checks=['Source hashes and exact retained RGBA; alpha masks explicitly exclude original waist, which remains unmodified','1001 actual JS poses checked against every visible pixel-cell corner','After first body cut, full captured pixels equal previous version'],limits='Foot region improves; waist and thigh still swap drawings. No 3D knee/ankle or physics validation. Two parts still swap at 1200 ms; no continuous full-body claim.')
(OUT/'leg-entry-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
