"""Verify bounded collar reuse, no new transparency, and first-handoff pixels."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((OUT/'shoulder-entry.json').read_text());memory=0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for donor in [m['lining'],m['collar']]:assert sha(OUT/donor['source'])==donor['sourceSHA256']
for p in m['torsos'].values():
 source=OUT/p['source'];assert sha(source)==p['sourceSHA256'];old=np.array(Image.open(source).convert('RGBA'));new=np.array(Image.open(OUT/p['url']).convert('RGBA'));assert np.array_equal(new[:,:,3],old[:,:,3])
 mask=Image.new('L',(old.shape[1],old.shape[0]));cap=m['cap'];mask.paste(Image.open(OUT/cap['url']).getchannel('A'),(cap['box'][0]-p['box'][0],cap['box'][1]-p['box'][1]));region=np.array(mask)>=p['maskAlphaThreshold'];visible=old[:,:,3]>0
 assert np.array_equal(new[:,:,:3][visible&~region],old[:,:,:3][visible&~region]);assert np.any(new[:,:,:3][visible&region]!=old[:,:,:3][visible&region]);memory+=new.size
script="""import fs from 'node:fs';import {fallPose} from './docs/routes/jigoku-2d/free-arm-settle/fall.mjs';import {shoulderEntryPose} from './docs/routes/jigoku-2d/free-arm-settle/shoulder-entry.mjs';const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/shoulder-entry.json'),s=read('free-arm-settle/settle.json'),t=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),u=read('free-arm-support/support.json'),f=read('free-arm-settle/bridge.json');console.log(JSON.stringify(Array.from({length:1001},(_,i)=>{const age=1000+i*.2;return shoulderEntryPose(age,fallPose(age,s,t,k,u,f),m);})));"""
rows=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));cap=m['cap'];a=np.array(Image.open(OUT/cap['url']).convert('RGBA'));y,x=np.where(a[:,:,3]>16);x=x+cap['box'][0]-cap['pivot'][0];y=y+cap['box'][1]-cap['pivot'][1];maximum=-1
for p in rows:
 c,s=np.cos(np.deg2rad(p['angle'])),np.sin(np.deg2rad(p['angle']))
 for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
  px=p['point']['x']+(x+dx)*c-(y+dy)*s;py=p['point']['y']+(x+dx)*s+(y+dy)*c;maximum=max(maximum,float(py.max()));assert py.max()<=690;assert px.min()*.8-50>=0 and px.max()*.8-50<=600;assert py.min()*.8-10>=65
capture=OUT/'handoffs/entry';previous=ROOT/'.tmp/shoulder-entry-baseline';assert json.loads((capture/'entry-registration.json').read_text())==m
states=json.loads((capture/'draw-states.json').read_text());measurements=[]
def image(folder,time,suffix):return np.array(Image.open(folder/f'{time}-{suffix}.png').convert('RGBA'))
def measure(folder,time):
 a=image(folder,time,'before-body')[:,:,3]>16;b=image(folder,time,'after-body')[:,:,3]>16;x=image(folder,time,'before').astype(float);y=image(folder,time,'after').astype(float)
 return dict(bodyAlphaIoU=float((a&b).sum()/(a|b).sum()),meanRGBDelta=float(abs(x[:,:,:3]-y[:,:,:3]).mean()))
for time in [1000,1180,1200,1220,1240]:
 old=measure(previous,time);new=measure(capture,time)
 if time==1200:assert new['meanRGBDelta']<old['meanRGBDelta']*.9
 if time in [1220,1240]:
  for side in ['before','after']:assert np.array_equal(image(previous,time,side),image(capture,time,side))
 if time==1200:assert np.array_equal(image(previous,time,'after'),image(capture,time,'after'))
 if time==1180:
  a,b=[s['entryCap'] for s in states if abs(s['age']-time)<.002];assert a['url']==b['url']=='cap.webp';assert max(abs(a['transform'][k]-b['transform'][k]) for k in ['a','b','c','d','e','f'])<.003
 measurements.append(dict(time=time,previous=old,earlyDrop=new,previousScreenshotSHA256={side:sha(previous/f'{time}-{side}.png') for side in ['before','after']}))
assert np.array_equal(image(previous,1000,'before'),image(capture,1000,'before'))
a=image(previous,1000,'after').astype(float);b=image(capture,1000,'after').astype(float);activation=dict(meanRGBDelta=float(abs(a[:,:,:3]-b[:,:,:3]).mean()),pixelsOver8=int((abs(a-b).max(2)>8).sum()));assert activation['meanRGBDelta']<.015 and activation['pixelsOver8']<100
protected=['src','public','docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-settle/fall.json','docs/routes/jigoku-2d/free-arm-settle/bridge.json','docs/routes/jigoku-2d/free-arm-settle/shared-head.json','docs/routes/jigoku-2d/free-arm-settle/shared-shoulder.json','docs/routes/jigoku-2d/free-arm-settle/fall.mjs','docs/routes/jigoku-2d/free-arm-settle/yield.mjs','docs/routes/jigoku-2d/free-arm-settle/torso.webp','docs/routes/jigoku-2d/free-arm-settle/cap.webp'];subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE)
report=dict(passed=True,torsoAlphaPreserved=True,sourceRGBOutsideCoveredPlatePreserved=True,newTexturesRGBA8MiB=memory/1048576,capSamples=len(rows),maximumCapPixelCellY=maximum,activationComparedWithSameTimePrevious=activation,handoffs=measurements,limits='Plate projection uses an authored rotation and mounting offset; not anatomy or a gravity simulation. Existing collar is registered inside the old plate footprint only. 1200 ms still switches body and cap artwork; subsequent poses remain the previous version. No game integration or physical phone performance measurement.')
(OUT/'shoulder-entry-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
