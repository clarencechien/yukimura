"""Pack four low-hit/recovery body layers and append sockets for the shared arm/katana."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/ghost-rig/low-hit.png'
recovery_source=ROOT/'assets/source/jigoku-2d/ghost-rig/low-recovery.png'
images=[Image.open(p).convert('RGBA') for p in [source,recovery_source]]
# Same uniform scale and rear-sole anchor, preserving the two authored body heights.
poses=[('leg-flinch',0,.78,(740,686),(0,0,887,887),(680,785),(292,774),(292,284),(270,420)),
       ('low-stagger',0,.78,(740,686),(887,0,1774,887),(1645,785),(1230,774),(1165,360),(1140,495)),
       ('leg-rise',1,.82,(740,686),(0,0,1086,724),(875,670),(430,670),(510,245),(490,380)),
       ('guard-settle',1,.88,(750,680),(1086,0,2172,724),(1740,670),(1295,670),(1415,215),(1405,345))]
frames=[];rows=[];bindings=[]
for name,source_id,scale,target,box,rear,front,shoulder,wrist in poses:
    crop=images[source_id].crop(box);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=(round(target[0]-(rear[0]-box[0])*scale),round(target[1]-(rear[1]-box[1])*scale))
    frame=Image.new('RGBA',(1152,768));frame.alpha_composite(crop,offset)
    mass=lambda f:sum(i*n for i,n in enumerate(f.getchannel('A').histogram()))
    assert mass(frame)==mass(crop),'Clipped body'
    point=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+(p[1]-box[1])*scale]
    bindings.append({'pose':name,'shoulder':point(shoulder),'wrist':point(wrist),'sourceShoulder':shoulder,'sourceWrist':wrist,'footContacts':[point(front),point(rear)]})
    rows.append({'pose':name,'source':source_id,'sourceBox':box,'uniformScale':scale,'pasteOffset':offset,'rearSole':point(rear),'frontSole':point(front),'sourceRearSole':rear,'sourceFrontSole':front})
    frames.append(frame)
checks=[]
for suffix,ratio in [('-hd',1),('',2/3)]:
    w,h=round(1152*ratio),round(768*ratio);atlas=Image.new('RGBA',(w*2,h*2))
    for i,frame in enumerate(frames):
        cell=frame.resize((w,h),Image.Resampling.LANCZOS);atlas.paste(cell,((i%2)*w,(i//2)*h))
        box=cell.getchannel('A').point(lambda a:255 if a>16 else 0).getbbox();l,t,r,b=box
        bounds=[970+(l/ratio-576)*.6,574+(t/ratio-690)*.6,970+(r/ratio-576)*.6,574+(b/ratio-690)*.6]
        assert 0<=bounds[0]<bounds[2]<=1200 and 0<=bounds[1]<bounds[3]<=750
        checks.append({'resolution':suffix or 'mobile','pose':poses[i][0],'worldBounds':bounds})
    atlas.save(OUT/f'enemy-low{suffix}.webp',lossless=True,method=6)
rig=json.loads((OUT/'enemy-rig.json').read_text());assert len(rig['bindings'])>=12
rig['bindings']=rig['bindings'][:12]+bindings
rig['lowHitSource']='enemy-low-art.json'
(OUT/'enemy-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
meta={'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-4bc112f1-deeb-4eda-9314-f489d1ba5cea.png','referenceCommit':'4f794f485ed1feeaaac305643ad33cc2a42fde51','referenceFrames':[0,1,3,4],'method':'One image_gen two-pose edit from existing body layers, keeping far weapon arm absent. Same .78 uniform scale and rear-sole registration; manually measured shoulder/wrist anchors. Reuses original arm, grip and katana components. No whole-body rotation, nonuniform scaling, crossfade, new Blender render or physical ragdoll. Armor, head projection and soles still vary.','recoverySource':{'path':str(recovery_source.relative_to(ROOT)),'sha256':hashlib.sha256(recovery_source.read_bytes()).hexdigest(),'generatedFile':'exec-7988ca99-5e29-4083-828e-bc5fb973b26d.png','referenceCommit':'21d8b539b1a2abc9c38d2f0b8c0fdaf104cdf0aa','referenceFrames':[13,0],'method':'Two authored recovery poses; uniform .82/.88 scales with manually registered sole/shoulder/wrist points. Replaces reverse playback of flinch with rise and guard-settle silhouettes. Original low-hit cells retained. No body warping or new Blender render.'},'poses':rows,'bindings':[12,13,14,15],'hdFrame':[1152,768],'mobileFrame':[768,512],'hdRGBA8Bytes':2304*1536*4,'mobileRGBA8Bytes':1536*1024*4,'boundaryChecks':checks}
(OUT/'enemy-low-art.json').write_text(json.dumps(meta,indent=2)+'\n')
plate=Image.new('RGB',(1152,860),'#1b2328');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',23)
for i,(frame,label) in enumerate(zip(frames,['腿部受擊 · 屈膝卸力','低身失衡 · 重心下沉','重新踩穩 · 抬身回正','收手回防 · 恢復戒備'])):
    small=frame.resize((576,384),Image.Resampling.LANCZOS);x,y=i%2*576,i//2*430;plate.paste(small,(x,y),small);ImageDraw.Draw(plate).text((x+18,y+390),label,font=font,fill='#e0c9a2')
plate.save(OUT/'enemy-low-poses.jpg',quality=94)
print('Packed four low-hit/recovery silhouettes; eight viewport checks passed; appended shared-arm bindings 12..15.')
