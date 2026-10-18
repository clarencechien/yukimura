"""Register support art, split overlapping torso/lower body, reuse the arm kit."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-support';OUT.mkdir(exist_ok=True)
bodySource=ROOT/'assets/source/jigoku-2d/ghost-rig/kneel-arm-clean.png';raw=Image.open(bodySource).convert('RGBA');scale=.64;offset=[43,65]
frame=Image.new('RGBA',(1152,768));small=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS);frame.alpha_composite(small,offset)
mass=lambda im:sum(a*n for a,n in enumerate(im.getchannel('A').histogram()));assert mass(frame)==mass(small)
# 24 px waist overlap accommodates -10 to +8 px rigid chest movement.
cut=[[0,530],[460,530],[555,555],[615,535],[700,550],[1152,550]]
upperPoly=[[0,0],[1152,0]]+[[x,y+24] for x,y in reversed(cut)]
lowerPoly=cut+[[1152,768],[0,768]]
project=lambda p:[offset[i]+p[i]*scale for i in range(2)]
capPoly=[project(p) for p in [[650,595],[716,565],[754,600],[785,713],[684,733],[668,678]]]
boxes={'torso':[320,330,760,590],'lower':[320,510,850,720],'cap':[455,422,555,543]}
polys={'torso':upperPoly,'lower':lowerPoly,'cap':capPoly}
for name,box in boxes.items():
 crop=frame.crop(box);mask=Image.new('L',crop.size);ImageDraw.Draw(mask).polygon([(x-box[0],y-box[1]) for x,y in polys[name]],fill=255);a=np.array(crop);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));Image.fromarray(a).save(OUT/f'{name}.webp',lossless=True,method=6)
frame.save(OUT/'body.webp',lossless=True,method=6)
handSource=ROOT/'assets/source/jigoku-2d/ghost-rig/support-palm.png';hand=Image.open(handSource).convert('RGBA');hscale=.06;box=[200,0,1420,1024];size=[(box[2]-box[0])*hscale,(box[3]-box[1])*hscale];crop=hand.crop(box).resize(tuple(round(n) for n in size),Image.Resampling.LANCZOS);crop.save(OUT/'palm.webp',lossless=True,method=6)
local=lambda p:[(p[i]-box[i])*hscale for i in range(2)]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta={'baselineCommit':'75a55debb368c2627a299800c3d6cec74dd5717e','body':{'source':str(bodySource.relative_to(ROOT)),'sha256':sha(bodySource),'generatedFile':'exec-93997f27-c8eb-48c6-a599-c0d945062db7.png','scale':scale,'offset':offset,'shoulderSource':[730,675],'shoulder':project([730,675]),'boxes':boxes,'polygons':polys,'overlap':24},'palm':{'source':str(handSource.relative_to(ROOT)),'sha256':sha(handSource),'generatedFile':'exec-be1e0169-e038-4c54-b3bc-2f1f54981d25.png','box':box,'scale':hscale,'size':list(crop.size),'displaySize':size,'pivot':local([1070,260]),'heel':local([1000,470]),'sourceWrist':[1070,260],'sourceHeel':[1000,470],'axisDegrees':108.43494882292201},'contact':[470,668],'armMetadata':'../free-arm-parts/parts.json','method':'Two image_gen edits: armless kneel occlusion restoration and a planted-palm sprite. Manual sockets/contact marker; rigid overlapping chest/lower crops, no mesh warp. Reuses previous 85/90 upper and forearm textures. Kneeling support segment only, not a crouch-to-kneel full-body transition or force simulation.','runtimeChanged':False}
(OUT/'support.json').write_text(json.dumps(meta,indent=2)+'\n');print({'shoulder':meta['body']['shoulder'],'palmPivot':meta['palm']['pivot'],'heel':meta['palm']['heel']})
