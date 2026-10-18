"""Actual before/after footage for the single redrawn crouch body cell."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/crouch-consistency';TMP.mkdir(exist_ok=True)
BASE='f97f3a1e63af572be6d4ea904e1de0ff07e2f4da'
old=lambda n:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
report={'baselineCommit':BASE,'source':'Previous committed MP4 vs current actual Phaser screenshots. Same reaction phase and nearest reaction age; offsets recorded.','artCheck':json.loads((OUT/'crouch-consistency-art-check.json').read_text()),'limits':'Only authored crouch body pose 4 is repainted. Detached sword arm remains shared. Other 11 authored frames are unchanged; knees/helmet/free-hand continuity is a visual judgement, not a biomechanical measurement.','attacks':{}}
for kind,video,meta,frames in [('thrust','combat-30fps.mp4','capture-timing.json','frames'),('sweep','low-hit-30fps.mp4','low-capture.json','low-frames')]:
 (TMP/f'{kind}-before.mp4').write_bytes(old(video));subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/f'{kind}-before.mp4'),'-start_number','0',str(TMP/f'{kind}-before-%03d.png')],check=True)
 previous=json.loads(old(meta));current=json.loads((OUT/meta).read_text());buckle=next(r for r in current if r['enemy']['phase']=='buckle');crouch=next(r for r in current if r['enemy']['phase']=='crouch');kneel=next(r for r in current if r['enemy']['phase']=='kneel');selected=[buckle,crouch,kneel]
 plate=Image.new('RGB',(1200,1500),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((18,12),'前輪 · 舊蹲低原畫',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 蹲低造型一致性修稿',font=font,fill='#e0c9a2');pairs=[]
 for i,(row,label) in enumerate(zip(selected,['屈膝：保留前輪修稿','蹲低：本輪只換這張身體圖','接續跪下：保留原關鍵圖'])):
  before=min((r for r in previous if r['hp']==0 and r['enemy']['phase']==row['enemy']['phase']),key=lambda r:abs(r['enemyAge']-row['enemyAge']));offset=row['enemyAge']-before['enemyAge'];assert abs(offset)<=34
  for x,p in [(0,TMP/f"{kind}-before-{before['sample']:03d}.png"),(600,ROOT/f".tmp/combat-check/{frames}/{row['sample']:03d}.png")]:
   im=Image.open(p).convert('RGB');assert im.size==(1200,750);crop=im.crop((760,170,1200,650));plate.paste(crop,(x+70,48+i*480))
  draw.text((18,494+i*480),f"{label} · {row['enemyAge']:.1f} ms",font=font,fill='#e0c9a2',stroke_width=1,stroke_fill='#11181b')
  pairs.append({'phase':row['enemy']['phase'],'beforeSample':before['sample'],'afterSample':row['sample'],'reactionAgeMS':row['enemyAge'],'sampleOffsetMS':offset,'body':row['body'],'arm':row['arm'],'weapon':row['weapon']})
 plate.save(OUT/f'crouch-consistency-{kind}-comparison.jpg',quality=95)
 strip=Image.new('RGB',(1320,530),'#1b2328');d=ImageDraw.Draw(strip)
 for i,r in enumerate(selected):
  im=Image.open(ROOT/f".tmp/combat-check/{frames}/{r['sample']:03d}.png").crop((760,170,1200,650));strip.paste(im,(i*440,0));d.text((i*440+10,490),f"{r['enemyAge']:.1f} ms · {['前輪屈膝','修稿蹲低','原畫跪下'][i]}",font=font,fill='#e0c9a2')
 strip.save(OUT/f'crouch-consistency-{kind}-sequence.jpg',quality=95)
 report['attacks'][kind]={'pairs':pairs}
(OUT/'crouch-consistency-check.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:[p['sampleOffsetMS'] for p in v['pairs']] for k,v in report['attacks'].items()})
