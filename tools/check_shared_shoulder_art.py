"""Verify lining coverage, immutable source art and measured Canvas handoffs."""
from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((OUT/'shared-shoulder.json').read_text());memory=0
lining=m['lining'];source=OUT/lining['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==lining['sourceSHA256'];tile=np.array(Image.open(source).crop(lining['box']).convert('RGBA'));assert tile[:,:,3].min()>=250
for p in m['torsos'].values():
 source=OUT/p['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==p['sourceSHA256'];old=np.array(Image.open(source).convert('RGBA'));new=np.array(Image.open(OUT/p['url']).convert('RGBA'));assert np.array_equal(new[:,:,3],old[:,:,3]),'Lining must not introduce transparent holes'
 mask=Image.new('L',(old.shape[1],old.shape[0]));cap=p['cap'];mask.paste(Image.open(OUT/cap['url']).getchannel('A'),(cap['box'][0]-p['box'][0],cap['box'][1]-p['box'][1]));region=np.array(mask.filter(ImageFilter.MaxFilter(3)))>0
 visible=old[:,:,3]>0;assert np.array_equal(new[:,:,:3][visible&~region],old[:,:,:3][visible&~region]);yy,xx=np.indices(region.shape);expected=tile[yy%tile.shape[0],xx%tile.shape[1],:3];assert np.array_equal(new[:,:,:3][visible&region],expected[visible&region]);memory+=new.size
capture=OUT/'handoffs/shoulder';assert json.loads((capture/'shoulder-registration.json').read_text())==m
states=json.loads((capture/'draw-states.json').read_text());measurements=[]
def image(folder,time,suffix):return np.array(Image.open(folder/f'{time}-{suffix}.png').convert('RGBA'))
def measure(folder,time):
 a=image(folder,time,'before-body')[:,:,3]>16;b=image(folder,time,'after-body')[:,:,3]>16;x=image(folder,time,'before').astype(float);y=image(folder,time,'after').astype(float)
 return dict(bodyAlphaIoU=float((a&b).sum()/(a|b).sum()),meanRGBDelta=float(abs(x[:,:,:3]-y[:,:,:3]).mean()))
for time in [1200,1240,1320,1440]:
 old=measure(OUT/'handoffs/helmet',time);new=measure(capture,time);layer=None
 if time==1200:
  assert old==new
  for suffix in ['before','after']:assert np.array_equal(image(OUT/'handoffs/helmet',time,suffix),image(capture,time,suffix))
 else:
  assert new['meanRGBDelta']<old['meanRGBDelta'];assert new['bodyAlphaIoU']>old['bodyAlphaIoU']
  a,b=[s['shoulder'] for s in states if abs(s['age']-time)<.002];assert a['url']==b['url']==m['cap']['url'];delta=max(abs(a['transform'][k]-b['transform'][k]) for k in ['a','b','c','d','e','f']);assert delta<.002
  x=image(capture,time,'before-cap').astype(float);y=image(capture,time,'after-cap').astype(float);d=np.abs(x[:,:,:3]*x[:,:,3:]/255-y[:,:,:3]*y[:,:,3:]/255);outliers=int((d.max(2)>3).sum());assert outliers<=8
  layer=dict(matrixMaxDelta=delta,maxPremultipliedRGBDelta=float(d.max()),pixelsOver3=outliers)
 measurements.append(dict(time=time,previous=old,sharedShoulder=new,capLayer=layer))
x=image(capture,1220,'before').astype(float);y=image(capture,1220,'after').astype(float);activation=dict(meanRGBDelta=float(abs(x[:,:,:3]-y[:,:,:3]).mean()),pixelsOver8=int((abs(x-y).max(2)>8).sum()));assert activation['meanRGBDelta']<.02 and activation['pixelsOver8']<200
protected=['src','public','docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-settle/fall.json','docs/routes/jigoku-2d/free-arm-settle/bridge.json','docs/routes/jigoku-2d/free-arm-settle/shared-head.json','docs/routes/jigoku-2d/free-arm-settle/torso.webp','docs/routes/jigoku-2d/free-arm-settle/fall-bridge-cap.webp'];subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE)
report=dict(passed=True,torsoAlphaPreserved=True,sourceRGBOutsidePlatePreserved=True,newTexturesRGBA8MiB=memory/1048576,reusedCap=m['cap']['url'],lining=lining,activation=activation,handoffs=measurements,limits='First body handoff unchanged. Plate moves rigidly; collar mount and cloth tile are authored 2D assembly, not anatomical simulation. Body outline and neck edges still change with four drawings. Not integrated into the game or measured on a phone.')
(OUT/'shared-shoulder-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
