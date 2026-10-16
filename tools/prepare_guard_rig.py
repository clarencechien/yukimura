"""Pack authored body/hand layers and a single rigid spear; no body warping."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';SRC=ROOT/'assets/source/jigoku-2d/guard-rig'
source=Image.open(SRC/'bodies.png').convert('RGBA');weapon=Image.open(SRC/'yari.png').convert('RGBA')
# Manually marked sole centers, palm centers and foreground finger/cuff rectangles.
config=[
 ('lift',(0,0,793,504),(255,495),(675,465),[(392,221),(630,145)],[(370,202,413,242),(605,122,654,164)]),
 ('brace',(793,0,1586,504),(970,495),(1385,465),[(1106,217),(1327,104)],[(1083,199,1134,236),(1303,80,1352,123)]),
 ('absorb',(0,504,793,992),(254,965),(671,936),[(390,713),(631,642)],[(367,693,410,735),(607,618,654,661)]),
 ('lower',(793,504,1586,992),(972,965),(1386,935),[(1108,717),(1353,669)],[(1086,697,1130,739),(1328,647,1378,689)])]
frames=[];hands=[];poses=[]
def mass(im):return sum(i*n for i,n in enumerate(im.getchannel('A').histogram()))
for name,box,rear,front,grips,patches in config:
 scale=398/(front[0]-rear[0]);rear_y=537+(rear[1]-front[1])*scale/2
 offset=(round(228-(rear[0]-box[0])*scale),round(rear_y-(rear[1]-box[1])*scale))
 point=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+(p[1]-box[1])*scale]
 crop=source.crop(box);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 frame=Image.new('RGBA',(1024,640));frame.alpha_composite(crop,offset);assert mass(frame)==mass(crop),'Clipped body'
 mapped=[[round(v) for v in point(g)] for g in grips]
 for center,patch in zip(mapped,patches):
  tl=point(patch[:2]);br=point(patch[2:]);bounds=tuple(round(v) for v in [*tl,*br]);piece=frame.crop(bounds)
  cell=Image.new('RGBA',(64,64));cell.alpha_composite(piece,(bounds[0]-center[0]+32,bounds[1]-center[1]+32));assert mass(cell)==mass(piece)
  hands.append(cell)
 frames.append(frame)
 assert math.dist(point(rear),[228,558])<8 and math.dist(point(front),[626,516])<8,'Foot registration exceeds envelope'
 spread=math.dist(*mapped);assert abs(spread-237)<5,(name,spread)
 poses.append({'name':name,'sourceBox':box,'uniformScale':scale,'pasteOffset':offset,'sourceGrips':grips,'grips':mapped,'fingerSourceBoxes':patches,'rearSole':point(rear),'frontSole':point(front),'gripSpread':spread,'frontRegistrationError':abs(spread-237)})
# Retain all alpha, including faint antialias pixels. The opaque spear spans x=9..2162.
wbox=weapon.getchannel('A').getbbox();weapon=weapon.crop(wbox)
weapon_meta={'sourceBox':wbox,'axisY':359-wbox[1],'axisLeft':9-wbox[0],'axisRight':2162-wbox[0],'sourceSize':list(weapon.size),'length':760,'rearGripFromButt':180,'gripDistance':237}
bytes_by_size={}
for suffix,ratio in [('-hd',1),('',.5)]:
 w,h=round(1024*ratio),round(640*ratio);atlas=Image.new('RGBA',(w*2,h*2))
 for i,f in enumerate(frames):atlas.paste(f.resize((w,h),Image.Resampling.LANCZOS),((i%2)*w,(i//2)*h))
 atlas.save(OUT/f'guard-body{suffix}.webp',lossless=True,method=6)
 hw=round(64*ratio);ha=Image.new('RGBA',(hw*4,hw*2))
 for i,f in enumerate(hands):ha.paste(f.resize((hw,hw),Image.Resampling.LANCZOS),((i%4)*hw,(i//4)*hw))
 ha.save(OUT/f'guard-hands{suffix}.webp',lossless=True,method=6)
 ww=round(1024*ratio);wh=round(weapon.height*ww/weapon.width);wa=weapon.resize((ww,wh),Image.Resampling.LANCZOS);wa.save(OUT/f'guard-yari{suffix}.webp',lossless=True,method=6)
 bytes_by_size[suffix or 'mobile']=sum(im.width*im.height*4 for im in [atlas,ha,wa])
baseline_marks=[[[358,230],[585,158]],[[353,289],[493,259]]]
meta={'baselineGripStudy':{'atlas':'guard-hd.webp','frameSize':[1024,640],'palmCenters':baseline_marks,'spreads':[math.dist(*m) for m in baseline_marks],'note':'Manual estimates on previous published body+weapon atlas; not automated pixel tracking.'},'firstStudy':{'path':str((SRC/'body-first-study.png').relative_to(ROOT)),'sha256':hashlib.sha256((SRC/'body-first-study.png').read_bytes()).hexdigest(),'generatedFile':'exec-72243455-d6d5-44f6-92cb-f5228e48fe60.png','status':'Rejected front-hand heights; superseded by bodies.png'},'referenceCommit':'833111fcbb9b7872efed08f00110cd9ab4b71b89','poses':poses,'weapon':weapon_meta,'rgba8Bytes':bytes_by_size,'sources':[{'path':str((SRC/n).relative_to(ROOT)),'sha256':hashlib.sha256((SRC/n).read_bytes()).hexdigest(),'generatedFile':g} for n,g in [('bodies.png','exec-c15ebaf5-04d7-46ba-a24a-695e52d85e29.png'),('yari.png','exec-bcdd9862-041d-45d8-8232-8c6008fac0a0.png')]],'method':'One new clean spear, one four-body study and one targeted front-arm correction via image_gen. Uniform sole registration, cropped foreground finger layers. Same 760 px spear and 237 px grip anchors at every guard pose; drawn palm centers differ from the front anchor by under 5 px. No stretching, independent body rotation or new Blender render. This is manually registered 2D art, not verified anatomical motion.'}
(OUT/'guard-rig.json').write_text(json.dumps(meta,indent=2)+'\n')
# Diagnostic layer sheet, showing body and fingers only; runtime comparison includes spear.
plate=Image.new('RGB',(1024,720),'#1b2328');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(f,p) in enumerate(zip(frames,poses)):
 small=f.resize((512,320),Image.Resampling.LANCZOS);x=i%2*512;y=i//2*360;plate.paste(small,(x,y),small);ImageDraw.Draw(plate).text((x+18,y+325),['提槍過渡','架槍','承力','放槍過渡'][i],font=font,fill='#e0c9a2')
plate.save(OUT/'guard-body-poses.jpg',quality=94)
print('Guard rig packed:',json.dumps({'palmSpreads':[p['gripSpread'] for p in poses],'RGBA8':bytes_by_size}))
