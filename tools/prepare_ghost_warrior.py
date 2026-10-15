"""Pack ten authored poses on common ground anchors, without warping anatomy."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/routes/jigoku-2d/combat'
sources=[ROOT/'assets/source/jigoku-2d/ghost-rig'/name for name in ['bodies-a.png','bodies-b.png','bodies-c.png']]
images=[Image.open(p).convert('RGBA') for p in sources]
# Inspected unequal rows: top figures extend below the nominal 512 px quadrant.
# The new palm-braced silhouette lowers the helmet after the original kneeling pose.
poses=[
 ('guard',0,(0,0,740,595),(480,570),'戒備'),
 ('flinch',1,(0,0,765,595),(480,555),'輕受擊'),
 ('hurt',0,(740,0,1536,595),(1180,570),'後仰'),
 ('buckle',2,(0,0,1140,724),(750,690),'重心下沉'),
 ('crouch',1,(765,0,1536,595),(1270,535),'屈膝'),
 ('kneel',0,(0,595,740,1024),(485,955),'跪下'),
 ('brace',1,(0,595,765,1024),(500,955),'手掌承重'),
 ('lower',2,(1140,0,2172,724),(1780,660),'屈肘落胯'),
 ('settle',1,(765,595,1536,1024),(1180,955),'側身落地'),
 ('fallen',0,(740,595,1536,1024),(1180,955),'伏地'),
]
def alpha_mass(im):return sum(i*n for i,n in enumerate(im.getchannel('A').histogram()))
frames=[]; rows=[]
for name,source_id,box,anchor,label in poses:
    crop=images[source_id].crop(box); frame=Image.new('RGBA',(1152,768))
    scale=2/3 if source_id==2 else 1
    if scale!=1:crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=(576-round((anchor[0]-box[0])*scale),690-round((anchor[1]-box[1])*scale))
    frame.alpha_composite(crop,offset); assert frame.getbbox()
    assert alpha_mass(frame)==alpha_mass(crop), ('Clipped pose',name)
    frames.append(frame); rows.append({'pose':name,'source':source_id,'sourceBox':box,'sourceAnchor':anchor,'uniformScale':scale,'alignedAnchor':[576,690]})
for suffix,scale in [('-hd',1),('',2/3)]:
    w,h=round(1152*scale),round(768*scale); sheet=Image.new('RGBA',(w*2,h*5))
    for i,frame in enumerate(frames):sheet.paste(frame.resize((w,h),Image.Resampling.LANCZOS),((i%2)*w,(i//2)*h))
    sheet.save(OUT/f'ghost-warrior{suffix}.webp',lossless=True,method=6)
preview=Image.new('RGB',(1152,2100),'#1c2429'); font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(frame,pose) in enumerate(zip(frames,poses)):
    small=frame.resize((576,384),Image.Resampling.LANCZOS)
    preview.paste(small,((i%2)*576,(i//2)*420),small)
    ImageDraw.Draw(preview).text(((i%2)*576+20,(i//2)*420+385),pose[-1],font=font,fill='#dac7aa')
preview.save(OUT/'enemy-poses.jpg',quality=93)
(OUT/'enemy-art.json').write_text(json.dumps({
 'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generatedFile':generated} for p,generated in zip(sources,['exec-581d763c-0659-41fa-9c45-5d9e5aaee529.png','exec-732be87f-242b-475a-982b-96204b6e58d8.png','exec-d37250aa-a34a-48f2-b201-572887ec552a.png'])],
 'method':'Three image_gen cleanup edits of the previous ten-pose sources: remove swords and gripping hands for poses 0-6; retain relaxed hands for released poses 7-9. Layout and proportions may drift in these generative edits. Common hand and katana are separate reusable runtime layers, with fixed size and manual wrist sockets. No mesh warping or new Blender rendering.',
 'poses':rows,'hdFrame':[1152,768],'mobileFrame':[768,512],'atlasColumns':2,'atlasRows':5,'worldScaleFromHD':.6,'worldGroundY':574,'hdRGBA8Bytes':2304*3840*4,'mobileRGBA8Bytes':1536*2560*4},indent=2)+'\n')
print('Prepared ten aligned enemy poses, HD/mobile atlases and inspection plate.')

# Shared components: crop and uniformly downsample; no painted deformation.
source=ROOT/'assets/source/jigoku-2d/ghost-rig/katana-hand.png'
im=Image.open(source).convert('RGBA')
parts={}
for name,box,scale,pivot in [
 ('katana',(0,100,2048,355),.2,(1635,240)),
 ('grip',(1530,365,1940,720),.16,(1820,420)),
]:
    part=im.crop(box).resize((round((box[2]-box[0])*scale),round((box[3]-box[1])*scale)),Image.Resampling.LANCZOS)
    part.save(OUT/f'enemy-{name}.webp',lossless=True,method=6)
    parts[name]={'size':list(part.size),'pivot':[(pivot[0]-box[0])*scale,(pivot[1]-box[1])*scale],'sourceBox':box,'uniformScale':scale}
parts['grip']['gripPoint']=[(1700-1530)*.16,(585-365)*.16]
# Source-space socket centers inspected on the cleaned forearm cuffs.
sockets=[(388,260,0),(316,285,8),(1051,282,-8),(455,388,-8),(1025,381,8),(300,828,-4),(286,858,8)]
bindings=[]
for row,(x,y,angle) in zip(rows,sockets):
    ax,ay=row['sourceAnchor'];scale=row['uniformScale']
    bindings.append({'pose':row['pose'],'wrist':[576+(x-ax)*scale,690+(y-ay)*scale],'angle':angle,'sourceWrist':[x,y]})
rig={'parts':parts,'bindings':bindings,'releaseAge':500,'flightMs':280,'groundY':690,'worldScale':.6,'bodyOrigin':[576,690],
 'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-4eb8eba6-b48f-4afd-b737-7a200ae630a3.png',
 'method':'image_gen disassembled katana and grip, referencing exec-f7fc9938-d445-41cf-b7c0-efc72f1b3b0f.png (a generated combined hand-and-sword study based on ghost-warrior-poses.png). Manual wrist and handle anchors. One constant-size blade and one grip reused across seven held poses. Scripted drop to a flat plane, not a physics simulation. No reproducible seed.',
 'extraRGBA8Bytes':sum(v['size'][0]*v['size'][1]*4 for v in parts.values())}
(OUT/'enemy-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
print('Packed shared katana and gripping hand; seven wrist sockets and deterministic release.')
