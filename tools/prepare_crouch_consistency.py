"""Register the crouch repaint without warping the painted anatomy."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/ghost-rig/crouch-consistent.png'
im=Image.open(source).convert('RGBA');scale=.49;offset=(138,234)
frame=Image.new('RGBA',(1152,768));resized=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);frame.alpha_composite(resized,offset)
mass=lambda image:sum(i*n for i,n in enumerate(image.getchannel('A').histogram()))
assert mass(frame)==mass(resized), 'Clipped generated body'
for suffix,size in [('-hd',(1152,768)),('',(768,512))]:
 atlas=Image.open(OUT/f'ghost-warrior{suffix}.webp').convert('RGBA');atlas.paste(frame.resize(size,Image.Resampling.LANCZOS),size);atlas.save(OUT/f'ghost-warrior{suffix}.webp',lossless=True,method=6)
project=lambda p:[offset[i]+p[i]*scale for i in range(2)]
shoulder_source=[520,390];sole_sources=[[631,909],[1206,930]];shoulder=project(shoulder_source);reach=[-65,121]
rig=json.loads((OUT/'enemy-rig.json').read_text())
rig['bindings'][4]={**rig['bindings'][4],'sourceShoulder':shoulder_source,'sourceWrist':None,'shoulder':shoulder,'wrist':[shoulder[i]+reach[i] for i in range(2)],'footContacts':[project(p) for p in sole_sources],'registrationNote':'Manually inspected far shoulder and sole centers. Far sword arm is absent from artwork; previous local wrist target is retained, not measured on the new image.'}
(OUT/'enemy-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
art=json.loads((OUT/'enemy-art.json').read_text());assert len(art['sources'])>=6, 'Apply buckle repair first'
entry={'path':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-d9a88a36-94da-45fd-b3bb-72108e302d19.png'}
if len(art['sources'])==6:art['sources'].append(entry)
else:art['sources'][6]=entry
art['poses'][4]={'pose':'crouch','source':6,'sourceBox':[0,0,1536,1024],'sourceAnchor':[(576-offset[0])/scale,(690-offset[1])/scale],'uniformScale':scale,'alignedAnchor':[576,690]}
art['crouchConsistency']={'baselineCommit':'f97f3a1e63af572be6d4ea904e1de0ff07e2f4da','source':entry,'referenceAtlasAtBaseline':'docs/routes/jigoku-2d/combat/ghost-warrior-hd.webp','referenceFrames':[4,3,5],'referencePreparation':'HD cells cropped without visible-pixel edits; RGB under alpha=0 cleared for references only.','uniformScale':scale,'offsetHD':offset,'sourceShoulder':shoulder_source,'sourceSoleCenters':sole_sources,'method':'One image_gen edit of crouch using buckle identity and kneel as next-pose reference. Uniform resize and translation only. More consistent knee fabric, helmet and waist armor; fingers less splayed but still mostly open. Only frame 4 replaced. Separate sword arm and timing retained. No continuous finger animation or anatomical guarantee.'}
(OUT/'enemy-art.json').write_text(json.dumps(art,indent=2)+'\n')
meta=json.loads((OUT/'enemy-body-art.json').read_text());meta['sourceSHA256']=hashlib.sha256((OUT/'ghost-warrior-hd.webp').read_bytes()).hexdigest();(OUT/'enemy-body-art.json').write_text(json.dumps(meta,indent=2)+'\n')
atlas=Image.open(OUT/'ghost-warrior-hd.webp').convert('RGBA');preview=Image.new('RGB',(1728,1680),'#1c2429');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(index,label) in enumerate([(0,'戒備'),(1,'輕受擊'),(2,'後仰'),(3,'屈膝・前輪修稿'),(4,'蹲低・本輪修稿'),(5,'跪下'),(6,'手掌承重'),(10,'屈肘承重'),(11,'落胯過渡'),(7,'屈肘落胯'),(8,'側身落地'),(9,'伏地')]):
 cell=atlas.crop((index%3*1152,index//3*768,(index%3+1)*1152,(index//3+1)*768)).resize((576,384),Image.Resampling.LANCZOS);preview.paste(cell,((i%3)*576,(i//3)*420),cell);ImageDraw.Draw(preview).text(((i%3)*576+20,(i//3)*420+385),label,font=font,fill='#dac7aa')
preview.save(OUT/'enemy-poses.jpg',quality=93)
print({'scale':scale,'offset':offset,'shoulder':shoulder,'soles':rig['bindings'][4]['footContacts']})
