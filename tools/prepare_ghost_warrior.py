"""Pack ten authored poses on common ground anchors, without warping anatomy."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/routes/jigoku-2d/combat'
sources=[ROOT/'assets/source/jigoku-2d'/name for name in ['ghost-warrior-poses.png','ghost-warrior-inbetweens.png','ghost-warrior-weight-shift.png']]
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
 'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generatedFile':generated} for p,generated in zip(sources,['exec-a2caeabc-b872-45ca-a782-3641042aed13.png','exec-66c79597-b037-4c85-b5ee-0d5846fe1c4f.png','exec-edeeb9bc-af2e-4d76-b7c5-808ed3808bc9.png'])],
 'method':'Original image_gen four-pose sheet with head-facing correction, plus referenced four-pose and two-pose inbetween sheets. Ten authored silhouettes, not 30 unique enemy poses per second. Manual crop and ground anchors; the third source is uniformly scaled 2/3 to match character size, no nonuniform scaling, morphing or whole-body death rotation. No reproducible seed; armor, sword and projected proportions still vary between poses.',
 'poses':rows,'hdFrame':[1152,768],'mobileFrame':[768,512],'atlasColumns':2,'atlasRows':5,'worldScaleFromHD':.6,'worldGroundY':574,'hdRGBA8Bytes':2304*3840*4,'mobileRGBA8Bytes':1536*2560*4},indent=2)+'\n')
print('Prepared ten aligned enemy poses, HD/mobile atlases and inspection plate.')
