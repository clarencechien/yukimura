"""Compare actual before/after blocking footage at equal remaining guard time and health."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/blade-contact-comparison';TMP.mkdir(exist_ok=True)
BASE='8a6cfb0c8fd9e98967edbd26d7ae75a9927b94ab'
def old(name):return subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
(TMP/'before.mp4').write_bytes(old('duel-30fps.mp4'))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/'before.mp4'),'-start_number','0',str(TMP/'before-%03d.png')],check=True)
previous=json.loads(old('duel-capture.json'));rows=json.loads((OUT/'duel-capture.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1305),'#1b2328');draw=ImageDraw.Draw(plate)
draw.text((18,12),'前輪 · 火星位於槍上，敵刀未接觸',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 刀刃與槍身交會，再退刀',font=font,fill='#e0c9a2')
report=[]
for i,(age,label) in enumerate([(10,'格擋接觸'),(50,'承力，刀槍仍相抵'),(150,'刀勢退開')]):
 row=min((r for r in rows if r['contact'] and r['duel']['blockAge'] is not None),key=lambda r:abs(r['duel']['blockAge']-age))
 matches=[b for b in previous if b['duel']['guard']==row['duel']['guard'] and b['duel']['stage']==row['duel']['stage'] and abs(b['duel']['blockAge']-row['duel']['blockAge'])<=16 and b['hp']==row['hp'] and b['duel']['playerHP']==row['duel']['playerHP'] and b['duel']['blocks']==row['duel']['blocks']]
 assert matches,age
 before=matches[0]
 for x,path in [(0,TMP/f"before-{before['sample']:03d}.png"),(600,ROOT/f".tmp/duel-check/frames/{row['sample']:03d}.png")]:
  im=Image.open(path).convert('RGB');assert im.size==(1200,750)
  plate.paste(im.resize((600,375),Image.Resampling.LANCZOS),(x,50+i*415))
 draw.text((18,428+i*415),label,font=font,fill='#e0c9a2')
 report.append({'beforeSample':before['sample'],'afterSample':row['sample'],'beforeBlockAge':before['duel']['blockAge'],'afterBlockAge':row['duel']['blockAge'],'blockSampleOffsetMS':row['duel']['blockAge']-before['duel']['blockAge'],'remainingGuardMS':row['duel']['guard'],'hp':row['hp'],'playerHP':row['duel']['playerHP'],'contact':row['contact'],'clashEvent':row['lastClash']})
 if i==0:
  target=row['contact']['target'];box=(round(target['x'])-160,round(target['y'])-120,round(target['x'])+260,round(target['y'])+210)
  Image.open(ROOT/f".tmp/duel-check/frames/{row['sample']:03d}.png").crop(box).resize((840,660),Image.Resampling.LANCZOS).save(OUT/'blade-contact-detail.jpg',quality=95)
plate.save(OUT/'blade-contact-comparison.jpg',quality=94)
(OUT/'blade-contact-comparison.json').write_text(json.dumps({'baselineCommit':BASE,'selected':report,'source':'Previous committed MP4 and new actual browser PNG, matched at identical remaining guard time, rule stage, block count and health. Block-event sample times may differ by up to 16 ms and are recorded per pair; resized identically. Detail is an enlarged crop of the same screenshot.','limits':'Authored planar geometric contact after rule timing determines a block. No general collision/force solver. Torso still uses discrete poses.'},indent=2)+'\n')
print('Compared real blade contact, load and deflection at matching remaining guard time and health, with block-event sample offsets recorded.')
