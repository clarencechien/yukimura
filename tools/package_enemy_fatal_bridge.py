"""Actual browser contact/loading/handoff samples against the committed baseline."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/enemy-fatal-bridge';TMP.mkdir(exist_ok=True)
BASE='5d33b8ca302ec51822f83b5e2e8470782843223c'
changed_textures=subprocess.check_output(['git','diff','--name-only',BASE,'--','docs/routes/jigoku-2d/combat/*.webp'],cwd=ROOT,text=True).splitlines();assert not changed_textures,changed_textures
old=lambda n:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
dist=lambda a,b:math.hypot(a['x']-b['x'],a['y']-b['y'])
report={'baselineCommit':BASE,'changedCharacterTextureFiles':changed_textures,'source':'Committed baseline MP4 vs actual current Phaser screenshots. No generated/interpolated frames.','limits':'Only impact and first 180 ms use shared body. At 180 ms shoulder/arm/weapon agree, but authored buckle silhouette, knees, feet and empty arm still differ. Later collapse remains authored.','attacks':{}}
for kind,video,meta,frames in [('thrust','combat-30fps.mp4','capture-timing.json','frames'),('sweep','low-hit-30fps.mp4','low-capture.json','low-frames')]:
 (TMP/f'{kind}-before.mp4').write_bytes(old(video));subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/f'{kind}-before.mp4'),'-start_number','0',str(TMP/f'{kind}-before-%03d.png')],check=True)
 before=json.loads(old(meta));after=json.loads((OUT/meta).read_text());first=next(r for r in after if r['hp']==0);old_first=next(r for r in before if r['hp']==0)
 selected=[first,max((r for r in after if r['hp']==0 and r['enemyBodyPose']),key=lambda r:r['enemyAge']),next(r for r in after if r['enemy']['phase']=='buckle')]
 plate=Image.new('RGB',(1000,1400),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((15,12),'前輪 · 命中立刻換整身圖',font=font,fill='#e0c9a2');draw.text((515,12),'本輪 · 保留原姿勢，再下沉',font=font,fill='#e0c9a2')
 pairs=[]
 for i,(row,label) in enumerate(zip(selected,['命中停頓','部件下沉末段','接回屈膝原畫：腿形仍有差異'])):
  elapsed=row['time']-first['time'];b=min((r for r in before if r['hp']==0),key=lambda r:abs(r['time']-old_first['time']-elapsed));offset=elapsed-(b['time']-old_first['time']);assert abs(offset)<=34
  for x,p in [(0,TMP/f"{kind}-before-{b['sample']:03d}.png"),(500,ROOT/f".tmp/combat-check/{frames}/{row['sample']:03d}.png")]:
   im=Image.open(p).convert('RGB');assert im.size==(1200,750);crop=im.crop((720,170,1200,660));crop.thumbnail((490,400),Image.Resampling.LANCZOS);plate.paste(crop,(x+45,50+i*450))
  draw.text((15,455+i*450),f"{label} · 受擊 {row['enemyAge']:.1f} ms",font=font,fill='#e0c9a2')
  pairs.append({'beforeSample':b['sample'],'afterSample':row['sample'],'reactionAgeMS':row['enemyAge'],'relativeHitSampleOffsetMS':offset,'sharedBody':bool(row['enemyBodyPose'])})
 plate.save(OUT/f'enemy-fatal-{kind}-comparison.jpg',quality=94)
 def jump(rows):
  n=next(i for i,r in enumerate(rows) if r['hp']==0);a,b=rows[n-1],rows[n]
  return {k:dist(a['arm'][k],b['arm'][k])*.6 for k in ['shoulder','elbow','wrist']}
 report['attacks'][kind]={'pairs':pairs,'impactJumpWorldPX':{'before':jump(before),'after':jump(after)}}
 assert max(jump(after).values())<1e-6
 # Explicit adjacent-frame handoff plate, including the remaining silhouette change.
 a,b=selected[1:];strip=Image.new('RGB',(1000,550),'#1b2328');draw=ImageDraw.Draw(strip)
 for i,r in enumerate([a,b]):
  im=Image.open(ROOT/f".tmp/combat-check/{frames}/{r['sample']:03d}.png").crop((760,170,1200,650));strip.paste(im,(i*500+30,30));draw.text((i*500+15,510),f"{r['enemyAge']:.1f} ms · {'共用部件' if i==0 else '屈膝原畫'}",font=font,fill='#e0c9a2')
 strip.save(OUT/f'enemy-fatal-{kind}-handoff.jpg',quality=95)
(OUT/'enemy-fatal-bridge-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v['impactJumpWorldPX'] for k,v in report['attacks'].items()},indent=2))
