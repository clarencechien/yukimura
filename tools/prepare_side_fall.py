"""Register new low side-fall art; uniform scale, explicit alpha cleanup and overlap masks."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';SOURCE=ROOT/'assets/source/jigoku-2d/ghost-rig/side-fall-breakdowns.png'
frames=[]
# All three drawings use the same uniform scale. Register the two later bodies
# against the ground instead of shrinking them. Source shoulder marks stay fixed.
# Marks are author-chosen projected shoulder roots beneath the shoulder plates.
rows=[('roll',1260,[0,0,675,724],.70,[312,296],[260,350],390,[[205,315],[269,320],[312,381],[326,439],[256,462],[220,440]]),
 ('side',1380,[675,0,1408,724],.70,[-166,301],[908,370],1020,[[824,333],[882,328],[940,390],[958,432],[881,466],[842,411]]),
 ('rest',1500,[1408,0,2172,724],.70,[-689,300],[1640,385],1745,[[1575,345],[1650,326],[1696,382],[1724,436],[1659,466],[1610,420]])]
for name,time,box,scale,globalOffset,shoulder,waist,cap in rows:
 source=SOURCE
 sheet=Image.open(source).convert('RGBA')
 raw=sheet.crop(box);a=np.array(raw);a[a[:,:,3]<=16,3]=0;raw=Image.fromarray(a)
 small=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS)
 offset=[round(globalOffset[0]+box[0]*scale),globalOffset[1]]
 frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,offset)
 project=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+p[1]*scale]
 x=project([waist,0])[0]
 polys={'lower':[[x-20,0],[1152,0],[1152,768],[x-20,768]],'torso':[[0,0],[x+28,0],[x+28,768],[0,768]],'cap':[project(p) for p in cap]}
 # Ground cloth remains with the lower image instead of sinking with the
 # translated chest. Keep an overlap, without altering source RGB pixels.
 if name in ['roll','side']:
  gx,gy,overlap=(480,674,650) if name=='roll' else (500,678,655)
  polys['lower']=[[x-20,0],[1152,0],[1152,768],[gx,768],[gx,overlap],[x-20,overlap]]
  polys['torso']=[[0,0],[x+28,0],[x+28,gy],[gx,gy],[gx,768],[0,768]]
 parts={}
 for n,poly in polys.items():
  mask=Image.new('L',frame.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in poly],fill=255);a=np.array(frame);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));piece=Image.fromarray(a);bounds=piece.getbbox();piece=piece.crop(bounds);url=f'fall-{name}-{n}.webp';piece.save(OUT/url,lossless=True,method=6);parts[n]=dict(url=url,box=bounds,polygon=poly)
 frames.append(dict(id=name,time=time,shoulder=project(shoulder),parts=parts,source=str(source.relative_to(ROOT)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),registration=dict(box=box,scale=scale,offset=offset,sourceShoulder=shoulder)))
meta=dict(baselineCommit='a49fc49d46df735a6df1f8e3010c6d9d63efc26d',source=str(SOURCE.relative_to(ROOT)),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),generatedFile='exec-0e52d796-7d7c-4260-8516-1c2cde90b2c6.png',alphaCleanupThreshold=16,groundY=690,frames=frames,start=1180,end=1500,reviewEnd=1800,nearWrist=[420,665],farWrist=[365,655],method='Three generated body breakdowns, manually registered with uniform scales. Whole lower-body drawings switch at key midpoints; overlapping torso/cap translate with continuous shoulder. Existing fixed-length arms reused. No mesh warp, image morph or crossfade. Not continuous anatomical animation or production replacement.')
(OUT/'fall.json').write_text(json.dumps(meta,indent=2)+'\n');print([(f['id'],f['shoulder']) for f in frames])
