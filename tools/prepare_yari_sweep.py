"""Pack shared boundary frames and authored sweep inbetweens; no image warping."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
old_source=ROOT/'assets/source/jigoku-2d/yari-sweep-poses.png'
new_source=ROOT/'assets/source/jigoku-2d/yari-sweep-transitions.png'
frames=[];rows=[]

def shared(name,clip,index):
    suffix="-2" if index>=24 else ""
    atlas=ROOT/f'docs/routes/jigoku-2d/yari-rigid/{clip}-warm-left-hd{suffix}.webp'
    local=index%24;box=((local%4)*1024,(local//4)*640,(local%4+1)*1024,(local//4+1)*640)
    frame=Image.open(atlas).convert('RGBA').crop(box);frames.append(frame)
    tip=json.loads((OUT/'spear-track.json').read_text())['frames'][35 if clip=='thrust' else 0]
    rows.append({'pose':name,'source':str(atlas.relative_to(ROOT)),'sourceFrame':index,'sourceBox':box,'uniformScale':1,'pasteOffset':[0,0],'worldTip':tip,'method':'Reference to the resident source atlas cell in each resolution; no duplicate texture.'})

def authored(name,source,box,rear,front,tip):
    scale=398/(front[0]-rear[0]);crop=Image.open(source).convert('RGBA').crop(box)
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=(round(228-(rear[0]-box[0])*scale),round(558-(rear[1]-box[1])*scale))
    frame=Image.new('RGBA',(1024,640));frame.alpha_composite(crop,offset)
    alpha_mass=lambda image:sum(i*n for i,n in enumerate(image.getchannel('A').histogram()))
    assert alpha_mass(frame)==alpha_mass(crop),(name,'clipped')
    point=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+(p[1]-box[1])*scale]
    mapped=point(tip)
    assert math.dist(point(rear),[228,558])<1
    assert math.dist(point(front),[626,516])<12
    rows.append({'pose':name,'source':str(source.relative_to(ROOT)),'sourceBox':box,'uniformScale':scale,'pasteOffset':offset,'sourceRearSole':rear,'sourceFrontSole':front,'sourceTip':tip,'rearSole':point(rear),'frontSole':point(front),'worldTip':{'x':35+mapped[0],'y':90+mapped[1]}})
    frames.append(frame)

shared('shared-thrust-end','thrust',35)
authored('descend',new_source,(0,0,1060,783),(199,708),(701,664),(1044,466))
authored('contact',old_source,(805,0,1536,510),(875,475),(1255,443),(1530,385))
authored('follow',old_source,(0,510,830,1024),(113,979),(514,947),(810,853))
authored('rise',new_source,(1060,0,2009,783),(1185,710),(1675,665),(1967,403))
shared('shared-idle-start','idle',0)
# Only the four middle silhouettes occupy new texture memory; boundaries reference
# the already-loaded idle/thrust atlases directly in Phaser.
for suffix,scale in [('-hd',1),('',.5)]:
    w,h=round(1024*scale),round(640*scale);atlas=Image.new('RGBA',(w*2,h*2))
    for i,frame in enumerate(frames[1:5]):
        cell=frame.resize((w,h),Image.Resampling.LANCZOS)
        atlas.paste(cell,((i%2)*w,(i//2)*h))
    atlas.save(OUT/f'sweep{suffix}.webp',lossless=True,method=6)
pose_sources=[{'clip':'thrust','frame':35}]+[{'clip':'sweep','frame':i} for i in range(4)]+[{'clip':'idle','frame':0}]
pose_frames=[0]*4+[1]*4+[2]*6+[3]*5+[4]*5+[5]*8
track={'fps':30,'frames':[rows[i]['worldTip'] for i in pose_frames],'poseFrames':pose_frames,'poseSources':pose_sources,'activeFrames':list(range(9,17)),
       'note':'32 simulation frames / six silhouettes: two shared existing animation frames, two preserved low poses, two new illustrated transitions. Manual tip coordinates, not continuous 3D motion. Active timing unchanged.'}
(OUT/'sweep-track.json').write_text(json.dumps(track,indent=2)+'\n')
meta={'sources':[{'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (old_source,new_source)],'newGeneratedFile':'exec-b5a2bcbb-2a47-4201-bad2-701bf0629a72.png','referenceCommit':'a6bf7a6ba0978ad81c3bd2b6e78c6bd6363c0950','reference':'Neutral composite of original thrust frame 35 and previous sweep contact/follow/windup frames.','method':'Two new image_gen inbetweens; uniform foot-span registration. First/last poses directly reference resident thrust 35 / idle 0 textures in both resolutions, no duplicate texture cells. No new Blender render, no anatomy warping. Drawn pole projection and armor details still vary inside the sweep.','poses':rows,'frameSizeHD':[1024,640],'frameSizeMobile':[512,320],'newTextureCells':4,'logicalPoseCount':6,'hdRGBA8Bytes':2048*1280*4,'mobileRGBA8Bytes':1024*640*4}
(OUT/'sweep-art.json').write_text(json.dumps(meta,indent=2)+'\n')
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1024,1080),'#1b2328')
for i,(frame,label) in enumerate(zip(frames,['共用收槍','沉腰下槍','低掃命中','隨勢','提槍回正','共用待機'])):
    small=frame.resize((512,320),Image.Resampling.LANCZOS);x=i%2*512;y=i//2*360
    plate.paste(small,(x,y),small);ImageDraw.Draw(plate).text((x+18,y+325),label,font=font,fill='#e0c9a2')
plate.save(OUT/'sweep-poses.jpg',quality=94)
print('Packed four texture cells for six logical poses with resident boundary references; 32-frame duration and active window retained.')
