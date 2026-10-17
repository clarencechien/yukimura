"""Verify local replacement and compare both actual image handoffs, including regressions."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
ROOT=Path('.');OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((OUT/'waist-transition.json').read_text());src=ROOT/m['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==m['sourceSHA256']
for reference in [*m['references'],m['earlierStudy']]:assert hashlib.sha256((ROOT/reference['path']).read_bytes()).hexdigest()==reference['sha256']
r=m['registration'];raw=Image.open(src).convert('RGBA');assert list(raw.size)==r['sourceSize'];size=[round(v*r['scale']) for v in raw.size];assert size==r['resizedSize']
world=Image.new('RGBA',(1152,768));world.alpha_composite(raw.resize(size,Image.Resampling.LANCZOS),tuple(r['offset']));pixels=0;counts={}
for p in [m['part'],*m['torsos'].values()]:
 assert hashlib.sha256((OUT/p['original']).read_bytes()).hexdigest()==p['originalSHA256'];old=Image.open(OUT/p['original']).convert('RGBA');new=Image.open(OUT/p['url']).convert('RGBA');assert old.size==new.size
 a=np.array(old);b=np.array(world.crop(p['box']));mask=Image.new('L',old.size);ImageDraw.Draw(mask).polygon([(x-p['box'][0],y-p['box'][1]) for x,y in m['polygon']],fill=255)
 region=(np.array(mask)>0)&(a[:,:,3]>=m['alphaThreshold'])&(b[:,:,3]>=m['alphaThreshold']);expected=a.copy();expected[region,:3]=b[region,:3];actual=np.array(new)
 visible=a[:,:,3]>0;assert np.array_equal(expected[visible],actual[visible]);assert np.array_equal(actual[:,:,3],a[:,:,3]);assert np.array_equal(actual[(~region)&visible],a[(~region)&visible]);assert region.any();pixels+=old.width*old.height;counts[p['url']]=int(region.sum())
rows=[]
for t in [1200,1220,1240,1320]:
 row={'time':t}
 for label,folder in [('previous',Path('.tmp/hip-study/baseline')),('candidate',OUT/'handoffs/hip')]:
  a=np.array(Image.open(folder/f'{t}-before.png').convert('RGB'),float);b=np.array(Image.open(folder/f'{t}-after.png').convert('RGB'),float)
  row[label]={'fullRGBMeanDelta':float(np.abs(a-b).mean()),'waistRegionRGBMeanDelta':float(np.abs(a[340:455,380:505]-b[340:455,380:505]).mean()),'SHA256':{s:hashlib.sha256((folder/f'{t}-{s}.png').read_bytes()).hexdigest() for s in ['before','after']}}
 for suffix in ['before','after']:
  a=np.array(Image.open(Path('.tmp/hip-study/baseline')/f'{t}-{suffix}-body.png').convert('RGBA'));b=np.array(Image.open(OUT/'handoffs/hip'/f'{t}-{suffix}-body.png').convert('RGBA'));assert np.array_equal(a[:,:,3],b[:,:,3])
  if (t==1200 and suffix=='before') or (t==1240 and suffix=='after') or t==1320:assert row['previous']['SHA256'][suffix]==row['candidate']['SHA256'][suffix]
 rows.append(row)
report=dict(passed=True,adopted=False,reason='Both adjacent full-color handoff deltas are essentially unchanged and slightly higher; preserve the current default. Local armor repaint does not solve pose and occlusion continuity.',additionalRGBA8MiB=pixels*4/1048576,replacedPixels=counts,waistRegionInCapture=[380,340,505,455],handoffs=rows,checks=['Generated source and original crop hashes verified; one uniform resize with recorded registration','All three crop alphas and all visible pixels outside the opaque local mask remain exact originals','Actual body-layer alpha matches previous version at all captured boundaries; pixels outside candidate interval unchanged'],limits='New waist design is an opt-in study; no full-body anatomical interpolation, physics, new rig, or production game replacement. Source images are generated, animation footage is actual Canvas playback.')
(OUT/'waist-transition-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
