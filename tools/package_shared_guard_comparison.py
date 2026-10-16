"""Compare actual guard captures at equal elapsed guard time and health."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/shared-guard-comparison';TMP.mkdir(exist_ok=True)
BASE='cd2ae3687948a846f80318c167f1cf5a37fa4a0a'
def old(name):return subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
(TMP/'before.mp4').write_bytes(old('duel-30fps.mp4'))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/'before.mp4'),'-start_number','0',str(TMP/'before-%03d.png')],check=True)
previous=json.loads(old('duel-capture.json'));rows=json.loads((OUT/'duel-capture.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1720),'#1b2328');draw=ImageDraw.Draw(plate)
draw.text((18,12),'前輪 · 四張全身格擋圖',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 同一人物連續架槍',font=font,fill='#e0c9a2')
report=[]
for i,(elapsed,label) in enumerate([(33,'抬槍'),(140,'架槍'),(350,'擋中後承力'),(530,'收槍回防')]):
 row=min((r for r in rows if r['heroArt']['action']=='guard'),key=lambda r:abs(r['heroArt']['guard']['elapsed']-elapsed))
 matches=[b for b in previous if b['duel']['guard']==row['duel']['guard'] and b['duel']['blocks']==row['duel']['blocks'] and b['hp']==row['hp'] and b['duel']['playerHP']==row['duel']['playerHP']]
 assert matches,elapsed
 before=matches[0]
 for x,path in [(0,TMP/f"before-{before['sample']:03d}.png"),(600,ROOT/f".tmp/duel-check/frames/{row['sample']:03d}.png")]:
  im=Image.open(path).convert('RGB');assert im.size==(1200,750)
  plate.paste(im.resize((600,375),Image.Resampling.LANCZOS),(x,50+i*415))
 draw.text((18,428+i*415),label,font=font,fill='#e0c9a2')
 report.append({'beforeSample':before['sample'],'afterSample':row['sample'],'elapsedMS':row['heroArt']['guard']['elapsed'],'guard':row['heroArt']['guard'],'hp':row['hp'],'playerHP':row['duel']['playerHP'],'arms':row['heroArt']['arms']})
plate.save(OUT/'shared-guard-comparison.jpg',quality=94)
(OUT/'shared-guard-comparison.json').write_text(json.dumps({'baselineCommit':BASE,'selected':report,'source':'Baseline committed MP4 decoded and new actual browser PNG, matched at equal remaining guard time, block count and health. Identical resize; baseline video compression may differ.','limits':'Planar rig, not 3D anatomy or force simulation. Block timing/range drives the authored planar blade/shaft alignment; this is not a general collision or force solver.'},indent=2)+'\n')
print('Compared four actual guard phases at matching guard time, blocks and health.')
