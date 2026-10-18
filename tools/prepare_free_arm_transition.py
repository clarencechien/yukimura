"""Uniformly register three breakdown drawings; masks only, no body warping."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-transition';OUT.mkdir(exist_ok=True)
BASE='44f0f796d747789f03d6b7f26244d5dd16624379';SOURCE=ROOT/'assets/source/jigoku-2d/ghost-rig/crouch-kneel-breakdowns.png'
kit=json.loads((ROOT/'docs/routes/jigoku-2d/free-arm-parts/parts.json').read_text());support=json.loads((ROOT/'docs/routes/jigoku-2d/free-arm-support/support.json').read_text())
frames=[];sole=kit['body']['soles'][0]
def split(frame,key,shoulder,cut,cap,registration):
 # Torso has 48 px of waist overlap for continuous shoulder translation.
 polys={'torso':[[0,0],[1152,0]]+[[x,y+48] for x,y in reversed(cut)],'lower':cut+[[1152,768],[0,768]],'cap':cap}
 parts={}
 for name,poly in polys.items():
  mask=Image.new('L',frame.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in poly],fill=255)
  a=np.array(frame);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));piece=Image.fromarray(a);box=piece.getbbox();piece=piece.crop(box)
  file=f'{key}-{name}.webp';piece.save(OUT/file,lossless=True,method=6);parts[name]={'url':file,'box':box,'polygon':poly}
 frames.append({'id':key,'shoulder':shoulder,'parts':parts,'registration':registration})
body=Image.open(ROOT/'docs/routes/jigoku-2d/free-arm-parts/body.webp').convert('RGBA')
split(body,'crouch',kit['body']['shoulder'],[[0,435],[420,435],[492,480],[550,500],[630,500],[730,550],[1152,550]],kit['cap']['polygon'],{'existing':'../free-arm-parts/body.webp','frontSole':sole})
sheet=Image.open(SOURCE).convert('RGBA')
# Source coordinates are authored landmarks, not anatomy measurements.
rows=[('shift',[0,0,770,724],[210,666],[355,220],[[0,310],[260,310],[320,345],[500,345],[640,420],[770,420]],[[310,153],[365,127],[409,151],[446,270],[339,298]]),
 ('lower',[770,0,1500,724],[985,668],[1090,290],[[770,348],[1020,348],[1090,380],[1250,390],[1410,510],[1500,510]],[[1040,210],[1105,185],[1155,225],[1175,325],[1075,351]]),
 ('touch',[1500,0,2172,724],[1690,669],[1810,350],[[1500,405],[1730,405],[1780,450],[1920,450],[2080,560],[2172,560]],[[1770,280],[1835,257],[1885,290],[1900,399],[1790,421]])]
for key,box,foot,shoulder,cut,cap in rows:
 scale={'shift':.62,'lower':.64,'touch':.70}[key];offset=[round(sole[i]-(foot[i]-box[i])*scale) for i in range(2)]
 project=lambda p:[offset[i]+(p[i]-box[i])*scale for i in range(2)]
 crop=sheet.crop(box);small=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,offset)
 projectedCut=[project(p) for p in cut];projectedCut[0][0]=0;projectedCut[-1][0]=1152
 split(frame,key,project(shoulder),projectedCut,[project(p) for p in cap],{'source':str(SOURCE.relative_to(ROOT)),'box':box,'scale':scale,'offset':offset,'sourceShoulder':shoulder,'sourceFrontSole':foot,'frontSole':project(foot)})
frames.append({'id':'kneel','shoulder':support['body']['shoulder'],'parts':{n:{'url':f'../free-arm-support/{n}.webp','box':b,'polygon':support['body']['polygons'][n]} for n,b in support['body']['boxes'].items()},'registration':{'existing':'../free-arm-support/body.webp'}})
for f,t in zip(frames,[330,352,376,400,420]):f['time']=t
meta={'baselineCommit':BASE,'source':str(SOURCE.relative_to(ROOT)),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'generatedFile':'exec-1da5004b-81c8-48ae-948d-5a1ab8c55945.png','frames':frames,'bodyRule':'Nearest drawn key pose, no crossfade; rigid torso/cap translation follows continuous shoulder curve. Lower body changes only at pose boundaries.','contactTime':420,'scope':'Independent five-pose crouch-to-kneel study. Manual registration; no force simulation or production replacement.'}
(OUT/'transition.json').write_text(json.dumps(meta,indent=2)+'\n');print([(f['id'],f['shoulder']) for f in frames])
