"""Cut four authored enemy poses; align to ground anchors without warping anatomy."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/ghost-warrior-poses.png';im=Image.open(source).convert('RGBA')
# The generated sheet has unequal row heights. These inspected bounds avoid cutting feet/weapons.
poses=[('guard',(0,0,740,595),(480,570)),('hurt',(740,0,1536,595),(1180,570)),('kneel',(0,595,740,1024),(485,955)),('fallen',(740,595,1536,1024),(1180,955))]
frames=[];rows=[]
for name,box,anchor in poses:
    crop=im.crop(box);frame=Image.new('RGBA',(1152,768));offset=(576-(anchor[0]-box[0]),690-(anchor[1]-box[1]))
    frame.alpha_composite(crop,offset);assert frame.getbbox()
    # No nontransparent pixels may be lost when aligning onto the common canvas.
    assert sum(frame.getchannel('A').getdata())==sum(crop.getchannel('A').getdata())
    frames.append(frame);rows.append({'pose':name,'sourceBox':box,'sourceAnchor':anchor,'alignedAnchor':[576,690]})
for suffix,scale in [('-hd',1),('',2/3)]:
    w,h=round(1152*scale),round(768*scale);sheet=Image.new('RGBA',(w*2,h*2))
    for i,frame in enumerate(frames):sheet.paste(frame.resize((w,h),Image.Resampling.LANCZOS),((i%2)*w,(i//2)*h))
    sheet.save(OUT/f'ghost-warrior{suffix}.webp',lossless=True,method=6)
preview=Image.new('RGB',(1152,840),'#1c2429');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(frame,label) in enumerate(zip(frames,['戒備','受擊','跪倒','伏地'])):
    small=frame.resize((576,384),Image.Resampling.LANCZOS);preview.paste(small,((i%2)*576,(i//2)*410),small);ImageDraw.Draw(preview).text(((i%2)*576+20,(i//2)*410+385),label,font=font,fill='#dac7aa')
preview.save(OUT/'enemy-poses.jpg',quality=93)
(OUT/'enemy-art.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-a2caeabc-b872-45ca-a782-3641042aed13.png','method':'One image_gen sheet referencing clean Sanada armor material style, followed by a head-facing correction edit; four separately authored poses, not 30fps skeletal animation. Manual crop and ground anchors, no nonuniform scaling or whole-body death rotation. No reproducible seed. Armor details and projected proportions may vary between poses.','poses':rows,'hdFrame':[1152,768],'mobileFrame':[768,512],'worldScaleFromHD':.6,'worldGroundY':574,'hdRGBA8Bytes':2304*1536*4,'mobileRGBA8Bytes':1536*1024*4},indent=2)+'\n')
print('Prepared four aligned enemy poses, HD/mobile atlases and inspection plate.')
