"""Compare actual Phaser footage; source sole landmarks are manually registered."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/enemy-footwork';TMP.mkdir(exist_ok=True)
BASE='78d090ccb51826fcaa4bbffee31b620a7f26c773'
old=lambda n:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
changed_textures=subprocess.check_output(['git','diff','--name-only',BASE,'--','docs/routes/jigoku-2d/combat/*.webp'],cwd=ROOT,text=True).splitlines()
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
soles={'left':(373,686),'right':(775,674)};boxes={'left':(315,610,445,700),'right':(685,615,815,700)}
rig=json.loads((OUT/'enemy-rig.json').read_text())
def mapped(row,side):
 p=row['enemyBodyParts'][side+'Foot'];b=boxes[side];v=soles[side];x=((v[0]-b[0])/(b[2]-b[0])-p['originX'])*p['width'];y=((v[1]-b[1])/(b[3]-b[1])-p['originY'])*p['height'];a=math.radians(p['angle'])
 return [p['x']+x*math.cos(a)-y*math.sin(a),p['y']+x*math.sin(a)+y*math.cos(a)]
def target(row,i):
 x,y=rig['bindings'][3]['footContacts'][i];return [row['target']['x']+(x-576)*.6,574+(y-690)*.6]
report={'baselineCommit':BASE,'source':'Previous committed MP4 and current actual Phaser screenshots. No synthesized or interpolated frames.','soleLandmarksHD':soles,'unchangedCharacterTextures':not changed_textures,'changedCharacterTextureFiles':changed_textures,'scope':'Manual source sole centers projected through actual sprite transforms. Not optical flow, actual pressure, contact dynamics, or physical phone FPS. Only fatal first 180 ms changes. Helmet/empty arm/silhouette and later authored collapse remain discontinuous.','attacks':{}}
for kind,video,meta,frames in [('thrust','combat-30fps.mp4','capture-timing.json','frames'),('sweep','low-hit-30fps.mp4','low-capture.json','low-frames')]:
 (TMP/f'{kind}-before.mp4').write_bytes(old(video));subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/f'{kind}-before.mp4'),'-start_number','0',str(TMP/f'{kind}-before-%03d.png')],check=True)
 previous=json.loads(old(meta));current=json.loads((OUT/meta).read_text());shared=[r for r in current if r['hp']==0 and r['enemyBodyPose']]
 plate=Image.new('RGB',(1200,1130),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((15,12),'前輪 · 腳固定，到交接才換位置',font=font,fill='#e0c9a2');draw.text((615,12),'本輪 · 交替收步，陰影跟隨',font=font,fill='#e0c9a2')
 pairs=[]
 for i,(age,label) in enumerate([(40,'先收右腳，左腳支撐'),(130,'右腳落穩，再收左腳'),(179,'交接前：腳位接近屈膝原畫')]):
  row=min(shared,key=lambda r:abs(r['enemyAge']-age));before=min((r for r in previous if r['hp']==0 and r['enemyBodyPose']),key=lambda r:abs(r['enemyAge']-row['enemyAge']));offset=row['enemyAge']-before['enemyAge'];assert abs(offset)<=17
  for x,p in [(0,TMP/f"{kind}-before-{before['sample']:03d}.png"),(600,ROOT/f".tmp/combat-check/{frames}/{row['sample']:03d}.png")]:
   image=Image.open(p).convert('RGB');assert image.size==(1200,750);crop=image.crop((760,345,1200,625)).resize((550,350),Image.Resampling.LANCZOS);plate.paste(crop,(x+25,45+i*360))
  draw.text((30,355+i*360),f"{label} · {row['enemyAge']:.1f} ms",font=font,fill='#e0c9a2',stroke_width=1,stroke_fill='#11181b')
  pairs.append({'beforeSample':before['sample'],'afterSample':row['sample'],'reactionAgeMS':row['enemyAge'],'sampleOffsetMS':offset,'feet':row['enemyBodyPose']['feet'],'shadowDrawCommands':row['enemyFootShadows']})
 plate.save(OUT/f'enemy-footwork-{kind}-comparison.jpg',quality=95)
 last=shared[-1];old_last=max((r for r in previous if r['hp']==0 and r['enemyBodyPose']),key=lambda r:r['enemyAge'])
 residual=lambda r:{side:math.dist(mapped(r,side),target(r,i)) for i,side in enumerate(['left','right'])}
 report['attacks'][kind]={'pairs':pairs,'lastSharedReactionAgeMS':last['enemyAge'],'lastSharedSoleDistanceToBuckleWorldPX':{'before':residual(old_last),'after':residual(last)}}
 # A 30 Hz capture may stop up to one frame before the 175 ms landing.
 assert 145<=last['enemyAge']<180
 for side in ['left','right']:assert residual(last)[side]<residual(old_last)[side]*.5
 b=next(r for r in current if r['enemy']['phase']=='buckle');strip=Image.new('RGB',(1000,550),'#1b2328');d=ImageDraw.Draw(strip)
 for i,r in enumerate([last,b]):
  im=Image.open(ROOT/f".tmp/combat-check/{frames}/{r['sample']:03d}.png").crop((760,170,1200,650));strip.paste(im,(i*500+30,30));d.text((i*500+15,510),f"{r['enemyAge']:.1f} ms · {'收步末段' if i==0 else '屈膝原畫'}",font=font,fill='#e0c9a2')
 strip.save(OUT/f'enemy-footwork-{kind}-handoff.jpg',quality=95)
(OUT/'enemy-footwork-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v['lastSharedSoleDistanceToBuckleWorldPX'] for k,v in report['attacks'].items()},indent=2))
