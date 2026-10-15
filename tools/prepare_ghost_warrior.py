"""Pack twelve authored poses on inspected contact anchors, without warping anatomy."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs/routes/jigoku-2d/combat'
sources=[ROOT/'assets/source/jigoku-2d/ghost-rig'/name for name in ['arm-bodies-a.png','arm-bodies-b.png','arm-bodies-c.png','shoulder-refined.png']]
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
 # Align the inspected support fingertip to the prior version's authored contact.
 ('yield',3,(0,0,1086,724),(390+(576-455)/.87,650),'屈肘承重'),
 ('sink',3,(1086,0,2172,724),(1500+(576-435)/.84,650),'落胯過渡'),
]
def alpha_mass(im):return sum(i*n for i,n in enumerate(im.getchannel('A').histogram()))
frames=[]; rows=[]
for name,source_id,box,anchor,label in poses:
    crop=images[source_id].crop(box); frame=Image.new('RGBA',(1152,768))
    scale={'yield':.87,'sink':.84}.get(name,2/3 if source_id==2 else 1)
    if scale!=1:crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
    offset=(576-round((anchor[0]-box[0])*scale),690-round((anchor[1]-box[1])*scale))
    frame.alpha_composite(crop,offset); assert frame.getbbox()
    assert alpha_mass(frame)==alpha_mass(crop), ('Clipped pose',name)
    frames.append(frame); rows.append({'pose':name,'source':source_id,'sourceBox':box,'sourceAnchor':anchor,'uniformScale':scale,'alignedAnchor':[576,690]})
for suffix,scale in [('-hd',1),('',2/3)]:
    w,h=round(1152*scale),round(768*scale); sheet=Image.new('RGBA',(w*3,h*4))
    for i,frame in enumerate(frames):sheet.paste(frame.resize((w,h),Image.Resampling.LANCZOS),((i%3)*w,(i//3)*h))
    sheet.save(OUT/f'ghost-warrior{suffix}.webp',lossless=True,method=6)
preview=Image.new('RGB',(1728,1680),'#1c2429'); font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,index in enumerate([0,1,2,3,4,5,6,10,11,7,8,9]):
    frame,pose=frames[index],poses[index]
    small=frame.resize((576,384),Image.Resampling.LANCZOS)
    preview.paste(small,((i%3)*576,(i//3)*420),small)
    ImageDraw.Draw(preview).text(((i%3)*576+20,(i//3)*420+385),pose[-1],font=font,fill='#dac7aa')
preview.save(OUT/'enemy-poses.jpg',quality=93)
(OUT/'enemy-art.json').write_text(json.dumps({
 'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generatedFile':generated} for p,generated in zip(sources,['exec-2fec5164-0ca5-40c3-8616-f0f413e7686d.png','exec-3f92b7d4-a205-40ff-9827-20759bcfee52.png','exec-e08ce8d8-91a8-4b56-b6fc-4da9581326d5.png','exec-acf88264-061d-4c09-a38e-7c76b93ab6c1.png'])],
 'method':'Three image_gen arm removal edits of bodies-a/b/c.png, followed by three repairs restoring mistakenly removed near arms. Far arms are now separate runtime upper/forearm/grip layers. Generative cleanup can change details and proportions. Manual shoulder anchors and fixed-length 2D IK, no new Blender rendering.',
 'transitionReferenceCommit':'6100c076457a68c965b1474327b3a2739eb150bc','transitionReferenceFrames':{'targets':[10,11],'neighbors':[6,7]},
 'transitionMethod':'One image_gen consistency edit of the prior yield/sink frames, with brace/lower as size references. Smaller helmet/menpo, close-fitting shoulder armor, restrained brass and finer hand details. Uniform scales 0.87/0.84 align the manually inspected support-finger contact and rear-foot span. Repaint shifted anatomy, so shoulder/wrist anchors were remeasured. No runtime root translation, warp or crossfade; armor and knee contacts still vary.',
 'poses':rows,'hdFrame':[1152,768],'mobileFrame':[768,512],'atlasColumns':3,'atlasRows':4,'worldScaleFromHD':.6,'worldGroundY':574,'hdRGBA8Bytes':3456*3072*4,'mobileRGBA8Bytes':2304*2048*4},indent=2)+'\n')
print('Prepared twelve enemy poses, HD/mobile atlases and inspection plate.')

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
# Rigid upper arm, forearm and releasing hands from a single authored parts sheet.
arm_source=ROOT/'assets/source/jigoku-2d/ghost-rig/arm-parts.png'
arm_im=Image.open(arm_source).convert('RGBA')
bulk_source=ROOT/'assets/source/jigoku-2d/ghost-rig/arm-parts-stocky.png'
bulk_im=Image.open(bulk_source).convert('RGBA')
for name,box,scale,pivot in [
 ('upper',(260,0,700,630),65/465,(470,70)),
 ('fore',(860,0,1320,630),75/500,(1080,80)),
 ('relax',(260,580,650,1000),.16,(460,625)),
 ('open',(910,580,1290,1024),.16,(1095,625)),
]:
    part=(bulk_im if name in ['upper','fore'] else arm_im).crop(box).resize((round((box[2]-box[0])*scale),round((box[3]-box[1])*scale)),Image.Resampling.LANCZOS)
    part.save(OUT/f'enemy-{name}.webp',lossless=True,method=6)
    parts[name]={'size':list(part.size),'pivot':[(pivot[0]-box[0])*scale,(pivot[1]-box[1])*scale],'sourceBox':box,'uniformScale':scale,'axisDegrees':90}
import math
parts['grip']['axisDegrees']=math.degrees(math.atan2(parts['grip']['gripPoint'][1]-parts['grip']['pivot'][1],parts['grip']['gripPoint'][0]-parts['grip']['pivot'][0]))
# Original desired sockets are retained as authoring targets, then constrained by two-bone IK.
sockets=[(388,260),(316,285),(1051,282),(455,388),(1025,381),(300,828),(286,858),(1430,575),(965,895),(980,900),(272,580),(1389,588)]
shoulders=[(385,150),(360,150),(1088,164),(520,230),(1090,260),(335,735),(335,748),(1350,440),(900,810),(930,815),(300,460),(1380,470)]
bindings=[]
support_contacts={'brace':(384,965),'yield':(390,650),'sink':(1500,650),'lower':(1561,660)}
for row,(x,y),(sx,sy) in zip(rows,sockets,shoulders):
    ax,ay=row['sourceAnchor'];scale=row['uniformScale']
    binding={'pose':row['pose'],'wrist':[576+(x-ax)*scale,690+(y-ay)*scale],'shoulder':[576+(sx-ax)*scale,690+(sy-ay)*scale],'sourceWrist':[x,y],'sourceShoulder':[sx,sy]}
    if row['pose'] in support_contacts:
        cx,cy=support_contacts[row['pose']]
        binding['supportContact']=[576+(cx-ax)*scale,690+(cy-ay)*scale]
        binding['sourceSupportContact']=[cx,cy]
    bindings.append(binding)
rig={'parts':parts,'bindings':bindings,'armLengths':[65,75],'relaxAge':430,'releaseAge':500,'flightMs':280,'groundY':690,'worldScale':.6,'bodyOrigin':[576,690],
 'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-4eb8eba6-b48f-4afd-b737-7a200ae630a3.png',
 'armSource':str(arm_source.relative_to(ROOT)),'armSha256':hashlib.sha256(arm_source.read_bytes()).hexdigest(),'armGeneratedFile':'exec-0c203020-19d7-4f8a-84da-60cc3ae54737.png',
 'bulkArmSource':str(bulk_source.relative_to(ROOT)),'bulkArmSha256':hashlib.sha256(bulk_source.read_bytes()).hexdigest(),'bulkArmGeneratedFile':'exec-9c05eb10-612f-4f45-8ed8-b9d578b85253.png',
 'method':'Image_gen separate arm segments and half/open hands, plus reused katana and closed grip. A thicker arm redraw supplies the upper/forearm only; original half/open hands retained. Redraw joint anchors remeasured and uniformly rescaled to the same 65/75 lengths. Fixed 65/75 px segments, manual shoulder anchors, interpolated local reach targets and two-bone IK. Shoulder anchors still switch with twelve body images, including two additional torso transitions. No continuous torso animation or physical finger simulation. Scripted blade release from the last held transform to a flat plane.',
 'extraRGBA8Bytes':sum(v['size'][0]*v['size'][1]*4 for v in parts.values())}
(OUT/'enemy-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
print('Packed shared two-bone arm, three hand states, katana and twelve shoulder bindings.')
