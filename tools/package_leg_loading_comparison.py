"""Compare actual baseline/current runtime frames at the same attack frame and HP."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/leg-loading-comparison';TMP.mkdir(exist_ok=True)
BASE='a972f3ec02cf9d57e3831f52f18988b1c57de772'
def old(name):return subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
(TMP/'before.mp4').write_bytes(old('shared-sweep-30fps.mp4'))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/'before.mp4'),'-start_number','0',str(TMP/'before-%03d.png')],check=True)
previous=json.loads(old('shared-sweep-capture.json'));rows=json.loads((OUT/'shared-sweep-capture.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1080,1110),'#1b2328');draw=ImageDraw.Draw(plate)
draw.text((16,12),'前輪 · 下半身固定',font=font,fill='#e0c9a2');draw.text((556,12),'本輪 · 落胯、屈膝、雙腳踏穩',font=font,fill='#e0c9a2')
report=[]
for i,(frame,label) in enumerate([(9,'低掃命中 · 下沉 8 px'),(16,'隨勢收力 · 向前 5 px、下沉 6 px')]):
 matches=[(r,b) for r in rows if r['phase']=='attack' and r['frame']==frame for b in previous if b['phase']=='attack' and b['frame']==frame and b['hp']==r['hp']]
 assert matches,frame
 row,before=matches[0]
 for x,path in [(0,TMP/f"before-{before['sample']:03d}.png"),(540,ROOT/f".tmp/shared-sweep-check/frames/{row['sample']:03d}.png")]:
  im=Image.open(path).convert('RGB');assert im.size==(1200,750)
  plate.paste(im.crop((190,175,730,665)),(x,52+i*528))
 draw.text((16,544+i*528),label,font=font,fill='#e0c9a2')
 report.append({'beforeSample':before['sample'],'afterSample':row['sample'],'sharedAttackFrame':frame,'hp':row['hp'],'root':row['heroArt']['root'],'legs':row['heroArt']['legs']})
plate.save(OUT/'leg-loading-comparison.jpg',quality=94)
(OUT/'leg-loading-comparison.json').write_text(json.dumps({'baselineCommit':BASE,'selected':report,'source':'Previous committed MP4 decoded and current browser PNG, identical 540x490 crops at matched attack frame/HP. Baseline video compression may differ.','limits':'Small planar pelvis translation with fixed-length legs, not mass/force simulation or a stepping animation.'},indent=2)+'\n')
print('Compared real low-sweep contact and follow-through at matching attack frame and health.')
