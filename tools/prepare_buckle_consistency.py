"""Register one image_gen buckle repair by uniform scale and translation only."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/ghost-rig/buckle-consistent.png'
im=Image.open(source).convert('RGBA');scale=.5025;offset=(184,198)
frame=Image.new('RGBA',(1152,768));resized=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);frame.alpha_composite(resized,offset)
assert sum(i*n for i,n in enumerate(frame.getchannel('A').histogram()))==sum(i*n for i,n in enumerate(resized.getchannel('A').histogram()))
for suffix,size in [('-hd',(1152,768)),('',(768,512))]:
 atlas=Image.open(OUT/f'ghost-warrior{suffix}.webp').convert('RGBA');atlas.paste(frame.resize(size,Image.Resampling.LANCZOS),(0,size[1]));atlas.save(OUT/f'ghost-warrior{suffix}.webp',lossless=True,method=6)
project=lambda p:[offset[0]+p[0]*scale,offset[1]+p[1]*scale]
rig=json.loads((OUT/'enemy-rig.json').read_text());old=rig['bindings'][3];shoulder=project([553,319]);localReach=[-20.1,97.15]
rig['bindings'][3]={**old,'sourceShoulder':[553,319],'sourceWrist':None,'shoulder':shoulder,'wrist':[shoulder[i]+localReach[i] for i in range(2)],'footContacts':[project(p) for p in [[520,971],[1080,975]]],'registrationNote':'Shoulder and soles manually inspected on new body; detached far arm is absent, so local wrist reach retains the prior authored offset, not a new anatomical landmark.'}
(OUT/'enemy-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
art=json.loads((OUT/'enemy-art.json').read_text());entry={'path':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-e2f2ffcf-0b34-4107-a70a-094c83b50f53.png'}
if len(art['sources'])==5:art['sources'].append(entry)
else:art['sources'][5]=entry
art['poses'][3]={'pose':'buckle','source':5,'sourceBox':[0,0,1536,1024],'sourceAnchor':[(576-offset[0])/scale,(690-offset[1])/scale],'uniformScale':scale,'alignedAnchor':[576,690]}
art['buckleConsistency']={'baselineCommit':'893bb9df5ef78290a2e2b8e963e215e2abfde1ac','source':entry,'referenceFilesAtBaseline':['assets/source/jigoku-2d/ghost-rig/recoil-buckle.png','docs/routes/jigoku-2d/combat/enemy-body-torso-hd.webp','docs/routes/jigoku-2d/combat/enemy-footwork-thrust-handoff.jpg'],'uniformScale':scale,'offsetHD':offset,'sourceShoulder':[553,319],'sourceSoleCenters':[[520,971],[1080,975]],'method':'One image_gen edit matching shared torso helmet/face and closed free fist. Uniform resize and translation only; pose 3 replaced in both existing atlases. Shoulder/soles remeasured, detached sword-arm reach retained. Anatomy and knee silhouette still differ.'}
(OUT/'enemy-art.json').write_text(json.dumps(art,indent=2)+'\n')
meta=json.loads((OUT/'enemy-body-art.json').read_text());meta['sourceSHA256']=hashlib.sha256((OUT/'ghost-warrior-hd.webp').read_bytes()).hexdigest();(OUT/'enemy-body-art.json').write_text(json.dumps(meta,indent=2)+'\n')
print({'scale':scale,'offset':offset,'shoulder':shoulder,'soles':rig['bindings'][3]['footContacts']})

# Keep the atlas inspection sheet consistent with the actually loaded pose 3.
atlas=Image.open(OUT/'ghost-warrior-hd.webp').convert('RGBA');preview=Image.new('RGB',(1728,1680),'#1c2429');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(index,label) in enumerate([(0,'戒備'),(1,'輕受擊'),(2,'後仰'),(3,'屈膝・造型修稿'),(4,'蹲低'),(5,'跪下'),(6,'手掌承重'),(10,'屈肘承重'),(11,'落胯過渡'),(7,'屈肘落胯'),(8,'側身落地'),(9,'伏地')]):
 cell=atlas.crop((index%3*1152,index//3*768,(index%3+1)*1152,(index//3+1)*768)).resize((576,384),Image.Resampling.LANCZOS);preview.paste(cell,((i%3)*576,(i//3)*420),cell);ImageDraw.Draw(preview).text(((i%3)*576+20,(i//3)*420+385),label,font=font,fill='#dac7aa')
preview.save(OUT/'enemy-poses.jpg',quality=93)
