"""Verify source-preserving head cuts, ground clearance and actual Canvas handoffs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((OUT/'shared-head.json').read_text());memory=0
for name,p in m['torsos'].items():
 source=OUT/p['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==p['sourceSHA256'];a=np.array(Image.open(source).convert('RGBA'));mask=Image.new('L',(a.shape[1],a.shape[0]));ImageDraw.Draw(mask).polygon([(x-p['box'][0],y-p['box'][1]) for x,y in p['polygon']],fill=255)
 expected=a.copy();expected[:,:,3]=np.minimum(a[:,:,3],255-np.array(mask.filter(ImageFilter.MinFilter(5))));actual=np.array(Image.open(OUT/p['url']).convert('RGBA'));assert np.array_equal(actual[:,:,3],expected[:,:,3]);visible=actual[:,:,3]>0;assert np.array_equal(actual[:,:,:3][visible],expected[:,:,:3][visible]);memory+=actual.size
 if name=='unload':
  expected=a.copy();expected[:,:,3]=np.minimum(a[:,:,3],np.array(mask));head=m['head'];b=[head['box'][0]-p['box'][0],head['box'][1]-p['box'][1],head['box'][2]-p['box'][0],head['box'][3]-p['box'][1]];expected=expected[b[1]:b[3],b[0]:b[2]];actual=np.array(Image.open(OUT/head['url']).convert('RGBA'));assert np.array_equal(actual[:,:,3],expected[:,:,3]);visible=actual[:,:,3]>0;assert np.array_equal(actual[:,:,:3][visible],expected[:,:,:3][visible]);memory+=actual.size
script="""import fs from 'node:fs';import {sharedHeadPose} from './docs/routes/jigoku-2d/free-arm-settle/shared-head.mjs';import {yieldPose} from './docs/routes/jigoku-2d/free-arm-settle/yield.mjs';const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/shared-head.json'),b=yieldPose(1180,read('free-arm-settle/settle.json'),read('free-arm-transition/transition.json'),read('free-arm-parts/parts.json'),read('free-arm-support/support.json'));console.log(JSON.stringify(Array.from({length:1601},(_,i)=>sharedHeadPose(1180+i*.2,b,m))));"""
rows=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));head=m['head'];a=np.array(Image.open(OUT/head['url']).convert('RGBA'));y,x=np.where(a[:,:,3]>16);x=x+head['box'][0]-head['pivot'][0];y=y+head['box'][1]-head['pivot'][1];maximum=-1
for p in rows:
 angle=np.deg2rad(p['angle']);c,s=np.cos(angle),np.sin(angle)
 for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
  px=p['point']['x']+(x+dx)*c-(y+dy)*s;py=p['point']['y']+(x+dx)*s+(y+dy)*c;maximum=max(maximum,float(py.max()));assert py.max()<=m['groundY'];assert px.min()*.8-50>=0 and px.max()*.8-50<=600;assert py.min()*.8-10>=65
capture=OUT/'handoffs/helmet';assert json.loads((capture/'head-registration.json').read_text())==m
states=json.loads((capture/'draw-states.json').read_text());measurements=[]
def image(folder,time,suffix):return np.array(Image.open(folder/f'{time}-{suffix}.png').convert('RGBA'))
def measure(folder,time):
 a=image(folder,time,'before-body')[:,:,3]>16;b=image(folder,time,'after-body')[:,:,3]>16;x=image(folder,time,'before').astype(float);y=image(folder,time,'after').astype(float)
 return dict(bodyAlphaIoU=float((a&b).sum()/(a|b).sum()),meanRGBDelta=float(abs(x[:,:,:3]-y[:,:,:3]).mean()))
for time in [1200,1240,1320,1440]:
 old=measure(OUT/'handoffs/bridge',time);new=measure(capture,time);assert new['bodyAlphaIoU']>old['bodyAlphaIoU'];assert new['meanRGBDelta']<old['meanRGBDelta']
 a,b=[s['helmet'] for s in states if abs(s['age']-time)<.002];delta=max(abs(a['transform'][k]-b['transform'][k]) for k in ['a','b','c','d','e','f']);assert delta<.002
 x=image(capture,time,'before-head').astype(float);y=image(capture,time,'after-head').astype(float);headDelta=float(max(abs(x[:,:,:3]*x[:,:,3:]/255-y[:,:,:3]*y[:,:,3:]/255).max(),abs(x[:,:,3]-y[:,:,3]).max()));headOutliers=int((abs(x[:,:,:3]*x[:,:,3:]/255-y[:,:,:3]*y[:,:,3:]/255).max(axis=2)>3).sum());assert headDelta<=8 and headOutliers<=4
 measurements.append(dict(time=time,baked=old,shared=new,headMatrixMaxDelta=delta,headLayerMaxPremultipliedDelta=headDelta,headPixelsOver3=headOutliers))
x=image(capture,1180,'before').astype(float);y=image(capture,1180,'after').astype(float);activation=dict(meanRGBDelta=float(abs(x[:,:,:3]-y[:,:,:3]).mean()),pixelsOver8=int((abs(x-y).max(axis=2)>8).sum()));assert activation['meanRGBDelta']<.01 and activation['pixelsOver8']<100
protected=['src','public','docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-settle/fall.json','docs/routes/jigoku-2d/free-arm-settle/bridge.json','docs/routes/jigoku-2d/free-arm-settle/torso.webp'];subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE)
report=dict(passed=True,sourcePixelsPreserved=True,newTexturesRGBA8MiB=memory/1048576,headSamples=len(rows),maximumHeadPixelCellY=maximum,activation=activation,handoffs=measurements,limits='Head layer and its rigid transform are continuous; shoulder occlusion and body drawings still switch. Neck overlap is a manually authored 2D cut, not anatomical deformation or contact physics. Source split activation has small filtering differences. Protected game and original body assets unchanged.')
(OUT/'shared-head-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
