"""Package authored transparent sprites; crop/separate/scale only, no anatomy warping."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
enemy_path=ROOT/'assets/source/jigoku-2d/ghost-rig/duel-bodies.png';hero_path=ROOT/'assets/source/jigoku-2d/yari-guard-poses.png'
enemy_source=Image.open(enemy_path).convert('RGBA');hero_source=Image.open(hero_path).convert('RGBA')
def mass(im):return sum(i*n for i,n in enumerate(im.getchannel('A').histogram()))
def place(crop,scale,offset,size):
 crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 frame=Image.new('RGBA',size);frame.alpha_composite(crop,offset);assert mass(frame)==mass(crop),'Clipped sprite';return frame
# All separator paths lie entirely in transparent gutters, including overlapping X bounds of the spears.
a=hero_source.getchannel('A')
for box in [(1098,0,1102,300),(968,300,972,814),(970,298,1100,302)]:assert a.crop(box).getextrema()==(0,0)
hero_parts=[]
for index in range(2):
 part=Image.new('RGBA',hero_source.size)
 boxes=[(0,0,1100,300),(0,300,970,814)] if index==0 else [(1100,0,1932,300),(970,300,1932,814)]
 for box in boxes:part.paste(hero_source.crop(box),box[:2])
 hero_parts.append(part)
assert sum(mass(im) for im in hero_parts)==mass(hero_source),'Separator removed source pixels'
hero=[];hero_rows=[]
for i,(rear,front,tip) in enumerate([((133,757),(705,700),(1050,40)),((1062,757),(1631,700),(1915,216))]):
 scale=398/(front[0]-rear[0]);offset=(round(228-rear[0]*scale),round(558-rear[1]*scale))
 frame=place(hero_parts[i],scale,offset,(1024,640));hero.append(frame)
 point=lambda p:[offset[0]+p[0]*scale,offset[1]+p[1]*scale]
 assert math.dist(point(rear),[228,558])<1 and math.dist(point(front),[626,516])<4
 hero_rows.append({'pose':['raised-guard','absorb-lower'][i],'uniformScale':scale,'pasteOffset':offset,'sourceRearSole':rear,'sourceFrontSole':front,'rearSole':point(rear),'frontSole':point(front),'tip':point(tip)})
enemy=[];enemy_rows=[];bindings=[]
for name,box,rear,front,shoulder in [
 ('draw-cut',(0,0,790,724),(707,684),(210,695),(374,177)),
 ('committed-cut',(790,0,1480,724),(1390,684),(888,695),(957,258)),
 ('cut-recover',(1480,0,2172,724),(2080,684),(1602,695),(1700,195))]:
 scale=.82;offset=(round(750-(rear[0]-box[0])*scale),round(680-(rear[1]-box[1])*scale))
 frame=place(enemy_source.crop(box),scale,offset,(1152,768));enemy.append(frame)
 point=lambda p:[offset[0]+(p[0]-box[0])*scale,offset[1]+(p[1]-box[1])*scale]
 socket=point(shoulder);bindings.append({'pose':name,'shoulder':socket,'wrist':[socket[0]+3,socket[1]+110],'sourceShoulder':shoulder,'footContacts':[point(front),point(rear)]})
 enemy_rows.append({'pose':name,'sourceBox':box,'uniformScale':scale,'pasteOffset':offset,'rearSole':point(rear),'frontSole':point(front)})
checks=[]
for name,frames,hd,mobile,root,scale,origin in [('enemy-duel',enemy,(1152,768),(768,512),(970,574),.6,(576,690)),('guard',hero,(1024,640),(512,320),(35,90),1,(0,0))]:
 for suffix,size in [('-hd',hd),('',mobile)]:
  atlas=Image.new('RGBA',(size[0]*len(frames),size[1]));assert max(atlas.size)<=4096
  for i,f in enumerate(frames):
   cell=f.resize(size,Image.Resampling.LANCZOS);atlas.paste(cell,(i*size[0],0))
   bounds=cell.getchannel('A').point(lambda a:255 if a>16 else 0).getbbox();ratio=size[0]/hd[0]
   world=[root[0]+(bounds[0]/ratio-origin[0])*scale,root[1]+(bounds[1]/ratio-origin[1])*scale,root[0]+(bounds[2]/ratio-origin[0])*scale,root[1]+(bounds[3]/ratio-origin[1])*scale]
   assert 0<=world[0]<world[2]<=1200 and 0<=world[1]<world[3]<=750,(name,i,world)
   checks.append({'atlas':name+suffix,'pose':i,'worldBounds':world})
  atlas.save(OUT/f'{name}{suffix}.webp',lossless=True,method=6)
meta={'referenceCommit':'d496634a164677c94131b900d51d535ab56c10fb','sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generatedFile':g} for p,g in [(enemy_path,'exec-1164ef98-bb11-4649-a5e7-417612b2f255.png'),(hero_path,'exec-7d4614e0-3390-4176-8916-c25161c123d9.png')]],'method':'Two image_gen reference edits. Transparent-gutter sprite extraction and uniform sole registration only; no body rotation, stretching, interpolation or new Blender rendering. Enemy uses existing 65/75 px arm segments, hand and katana. Hero yari is painted into each guard pose, not a shared rigid weapon. Foot/shoulder marks are manual; projection and armor vary between drawings.','enemy':{'poses':enemy_rows,'bindings':bindings},'hero':{'poses':hero_rows},'addedRGBA8Bytes':{'hd':15859712,'mobile':6029312},'boundaryChecks':checks}
(OUT/'duel-art.json').write_text(json.dumps(meta,indent=2)+'\n')
plate=Image.new('RGB',(1152,1240),'#1b2328');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',23)
for i,(f,label) in enumerate(zip(enemy,['鬼武者 · 蓄刀','鬼武者 · 斬下','鬼武者 · 收刀'])):
 small=f.resize((384,256),Image.Resampling.LANCZOS);plate.paste(small,(i*384,0),small);ImageDraw.Draw(plate).text((i*384+12,268),label,font=font,fill='#e0c9a2')
for i,(f,label) in enumerate(zip(hero,['幸村 · 架槍','幸村 · 承力收勢'])):
 small=f.resize((768,480),Image.Resampling.LANCZOS);y=310+i*460;plate.paste(small,(192,y),small);ImageDraw.Draw(plate).text((18,y+30),label,font=font,fill='#e0c9a2')
plate.save(OUT/'duel-poses.jpg',quality=94)
print('Packed 3 enemy / 2 hero poses, transparent gutters preserve source alpha, 10 viewport checks passed.')
