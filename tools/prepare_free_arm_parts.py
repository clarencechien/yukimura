"""Reuse existing arm art; register one generated occlusion-restoration body."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-parts';OUT.mkdir(exist_ok=True)
source=ROOT/'assets/source/jigoku-2d/ghost-rig/arm-parts-stocky.png';im=Image.open(source).convert('RGBA');parts={}
for name,box,scale,pivot,end in [
 ('upper',[260,0,700,630],85/465,[470,70],[470,535]),
 ('fore',[860,0,1320,630],90/500,[1080,80],[1080,580]),
 ('relax',[260,630,650,1024],.16,[465,690],None),
 ('open',[910,630,1290,1024],.16,[1100,690],None),
]:
 w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale;piece=im.crop(box).resize((round(w),round(h)),Image.Resampling.LANCZOS);piece.save(OUT/f'{name}.webp',lossless=True,method=6)
 local=lambda p:[(p[i]-box[i])*scale for i in range(2)]
 parts[name]={'box':box,'scale':scale,'size':list(piece.size),'displaySize':[w,h],'pivot':local(pivot),'end':local(end) if end else None,'axisDegrees':90}
bodySource=ROOT/'assets/source/jigoku-2d/ghost-rig/crouch-arm-clean.png';body=Image.open(bodySource).convert('RGBA');scale=.42;offset=[201,285];small=body.resize((round(body.width*scale),round(body.height*scale)),Image.Resampling.LANCZOS);frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,offset)
mass=lambda x:sum(a*n for a,n in enumerate(x.getchannel('A').histogram()));assert mass(frame)==mass(small)
frame.save(OUT/'body.webp',lossless=True,method=6)
# Shoulder cap alone overlays the rigid upper-arm root. Preserve source RGB;
# only a declared polygon limits alpha. It is not an erased/painted body patch.
polySource=[[640,190],[700,148],[780,165],[823,245],[850,335],[718,364],[671,297]]
project=lambda p:[offset[i]+p[i]*scale for i in range(2)]
poly=[project(p) for p in polySource];box=[465,344,560,441];cap=frame.crop(box);mask=Image.new('L',cap.size);ImageDraw.Draw(mask).polygon([(p[0]-box[0],p[1]-box[1]) for p in poly],fill=255)
import numpy as np
a=np.array(cap);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));Image.fromarray(a).save(OUT/'cap.webp',lossless=True,method=6)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta={'baselineCommit':'510560461411fba4ed6c0fd7161cc9df4ff2abf5','armSource':{'path':str(source.relative_to(ROOT)),'sha256':sha(source)},'parts':parts,'body':{'source':str(bodySource.relative_to(ROOT)),'sha256':sha(bodySource),'generatedFile':'exec-f616386a-1a7b-469c-9fd7-0d2976ab0b50.png','scale':scale,'offset':offset,'shoulderSource':[750,260],'shoulder':project([750,260]),'soleSources':[[586,934],[1255,954]],'soles':[project(p) for p in [[586,934],[1255,954]]]},'cap':{'box':box,'polygonSource':polySource,'polygon':poly},'method':'Upper/forearm and two hand states reused from existing stocky parts sheet, cropped and uniformly resampled. One image_gen near-arm removal and occlusion restoration of crouch-consistent.png; generated body framing/design drift remains. Fixed crouch fitting only, shoulder stays stationary; no full kneel or support contact. Cap is a masked mechanical source crop, not independently painted.','runtimeChanged':False,'reviewRGBA8Bytes':sum(Image.open(OUT/f'{n}.webp').width*Image.open(OUT/f'{n}.webp').height*4 for n in ['upper','fore','relax','open','body','cap'])}
(OUT/'parts.json').write_text(json.dumps(meta,indent=2)+'\n');print({'shoulder':meta['body']['shoulder'],'reviewMiB':meta['reviewRGBA8Bytes']/1048576})
