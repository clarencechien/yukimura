"""Pack two low-hit body layers and append sockets for the shared arm/katana."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/ghost-rig/low-hit.png';im=Image.open(source).convert('RGBA')
# Same uniform scale and rear-sole anchor, preserving the two authored body heights.
poses=[('leg-flinch',(0,0,887,887),(680,785),(292,774),(292,284),(270,420)),
       ('low-stagger',(887,0,1774,887),(1645,785),(1230,774),(1165,360),(1140,495))]
frames=[];rows=[];bindings=[];scale=.78
for name,box,rear,front,shoulder,wrist in poses:
    crop=im.crop(box);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=(round(740-(rear[0]-box[0])*scale),round(686-(rear[1]-box[1])*scale))
    frame=Image.new('RGBA',(1152,768));frame.alpha_composite(crop,offset)
    mass=lambda f:sum(i*n for i,n in enumerate(f.getchannel('A').histogram()))
    assert mass(frame)==mass(crop),'Clipped body'
    point=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+(p[1]-box[1])*scale]
    bindings.append({'pose':name,'shoulder':point(shoulder),'wrist':point(wrist),'sourceShoulder':shoulder,'sourceWrist':wrist,'footContacts':[point(front),point(rear)]})
    rows.append({'pose':name,'sourceBox':box,'uniformScale':scale,'pasteOffset':offset,'rearSole':point(rear),'frontSole':point(front),'sourceRearSole':rear,'sourceFrontSole':front})
    frames.append(frame)
checks=[]
for suffix,ratio in [('-hd',1),('',2/3)]:
    w,h=round(1152*ratio),round(768*ratio);atlas=Image.new('RGBA',(w*2,h))
    for i,frame in enumerate(frames):
        cell=frame.resize((w,h),Image.Resampling.LANCZOS);atlas.paste(cell,(i*w,0))
        box=cell.getchannel('A').point(lambda a:255 if a>16 else 0).getbbox();l,t,r,b=box
        bounds=[970+(l/ratio-576)*.6,574+(t/ratio-690)*.6,970+(r/ratio-576)*.6,574+(b/ratio-690)*.6]
        assert 0<=bounds[0]<bounds[2]<=1200 and 0<=bounds[1]<bounds[3]<=750
        checks.append({'resolution':suffix or 'mobile','pose':poses[i][0],'worldBounds':bounds})
    atlas.save(OUT/f'enemy-low{suffix}.webp',lossless=True,method=6)
rig=json.loads((OUT/'enemy-rig.json').read_text());assert len(rig['bindings'])>=12
rig['bindings']=rig['bindings'][:12]+bindings
rig['lowHitSource']='enemy-low-art.json'
(OUT/'enemy-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
meta={'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-4bc112f1-deeb-4eda-9314-f489d1ba5cea.png','referenceCommit':'4f794f485ed1feeaaac305643ad33cc2a42fde51','referenceFrames':[0,1,3,4],'method':'One image_gen two-pose edit from existing body layers, keeping far weapon arm absent. Same .78 uniform scale and rear-sole registration; manually measured shoulder/wrist anchors. Reuses original arm, grip and katana components. No whole-body rotation, nonuniform scaling, crossfade, new Blender render or physical ragdoll. Armor, head projection and soles still vary.','poses':rows,'bindings':[12,13],'hdFrame':[1152,768],'mobileFrame':[768,512],'hdRGBA8Bytes':2304*768*4,'mobileRGBA8Bytes':1536*512*4,'boundaryChecks':checks}
(OUT/'enemy-low-art.json').write_text(json.dumps(meta,indent=2)+'\n')
plate=Image.new('RGB',(1152,430),'#1b2328');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',23)
for i,(frame,label) in enumerate(zip(frames,['腿部受擊 · 屈膝卸力','低身失衡 · 重心下沉'])):
    small=frame.resize((576,384),Image.Resampling.LANCZOS);plate.paste(small,(i*576,0),small);ImageDraw.Draw(plate).text((i*576+18,390),label,font=font,fill='#e0c9a2')
plate.save(OUT/'enemy-low-poses.jpg',quality=94)
print('Packed two low-hit silhouettes; four viewport checks passed; appended shared-arm bindings 12/13.')
