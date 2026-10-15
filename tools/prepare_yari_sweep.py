"""Pack four authored sweep silhouettes; no optical flow, warping or frame synthesis."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=ROOT/'assets/source/jigoku-2d/yari-sweep-poses.png';im=Image.open(source).convert('RGBA')
# Unequal gutters keep the follow-through blade inside its own crop.
poses=[('windup',(0,0,805,505),(150,470),(503,435),(765,168)),
       ('contact',(805,0,1536,510),(875,475),(1255,443),(1530,385)),
       ('follow',(0,510,830,1024),(113,979),(514,947),(810,853)),
       ('recover',(830,510,1536,1024),(919,969),(1298,939),(1514,682))]
frames=[];rows=[]
for name,box,rear,front,tip in poses:
    scale=398/(front[0]-rear[0]);crop=im.crop(box)
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=(round(228-(rear[0]-box[0])*scale),round(558-(rear[1]-box[1])*scale))
    frame=Image.new('RGBA',(1024,640));frame.alpha_composite(crop,offset)
    alpha_mass=lambda image:sum(i*n for i,n in enumerate(image.getchannel('A').histogram()))
    assert alpha_mass(frame)==alpha_mass(crop),(name,'clipped')
    point=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+(p[1]-box[1])*scale]
    mapped=point(tip);mapped_front=point(front)
    assert math.dist(point(rear),[228,558])<1
    assert math.dist(mapped_front,[626,516])<12
    rows.append({'pose':name,'sourceBox':box,'uniformScale':scale,'pasteOffset':offset,'sourceRearSole':rear,'sourceFrontSole':front,'sourceTip':tip,'rearSole':point(rear),'frontSole':mapped_front,'worldTip':{'x':35+mapped[0],'y':90+mapped[1]}})
    frames.append(frame)
for suffix,scale in [('-hd',1),('',.5)]:
    w,h=round(1024*scale),round(640*scale);atlas=Image.new('RGBA',(w*2,h*2))
    for i,frame in enumerate(frames):atlas.paste(frame.resize((w,h),Image.Resampling.LANCZOS),((i%2)*w,(i//2)*h))
    atlas.save(OUT/f'sweep{suffix}.webp',lossless=True,method=6)
pose_frames=[0]*8+[1]*6+[2]*8+[3]*10
track={'fps':30,'frames':[rows[i]['worldTip'] for i in pose_frames],'poseFrames':pose_frames,'activeFrames':list(range(9,17)),
       'note':'32 simulation frames / four authored silhouettes. Blade tips manually marked from the rendered sprite, not Blender or continuous 3D motion. Swept tip segments approximate unsampled movement between keys; drawn weapon projection and anatomy still vary.'}
(OUT/'sweep-track.json').write_text(json.dumps(track,indent=2)+'\n')
meta={'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-25b51d9d-0827-4e2c-95b8-35567e74c12b.png','referenceCommit':'3487e4aa12f67d96c91398d3e3994b6f6ae56851','reference':'First 1024x640 frame of yari-rigid/thrust-warm-left-hd.webp','method':'One image_gen four-pose sheet; uniform scale from projected sole span, rear sole aligned to existing hero. No anatomy warping, no new Blender render. Four discrete poses, not 32 unique drawings. Weapon length is drawn into the image and its projected appearance varies.','poses':rows,'frameSizeHD':[1024,640],'frameSizeMobile':[512,320],'hdRGBA8Bytes':2048*1280*4,'mobileRGBA8Bytes':1024*640*4}
(OUT/'sweep-art.json').write_text(json.dumps(meta,indent=2)+'\n')
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1024,720),'#1b2328')
for i,(frame,label) in enumerate(zip(frames,['蓄勢','低掃命中','隨勢','收勢'])):
    small=frame.resize((512,320),Image.Resampling.LANCZOS);x=i%2*512;y=i//2*360
    plate.paste(small,(x,y),small);ImageDraw.Draw(plate).text((x+18,y+325),label,font=font,fill='#e0c9a2')
plate.save(OUT/'sweep-poses.jpg',quality=94)
print('Packed four sweep poses, 32-frame timing and manually registered tip path.')
