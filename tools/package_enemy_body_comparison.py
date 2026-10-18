"""Match actual browser frames by rule stage/age, and expose the timing offsets."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/enemy-body-comparison';TMP.mkdir(exist_ok=True)
BASE='2f8de54071a44c6159c2a2b18f98092c2d5aca66'
def old(n):return subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
(TMP/'before.mp4').write_bytes(old('duel-30fps.mp4'))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/'before.mp4'),'-start_number','0',str(TMP/'before-%03d.png')],check=True)
before=json.loads(old('duel-capture.json'));after=json.loads((OUT/'duel-capture.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1305),'#1b2328');draw=ImageDraw.Draw(plate)
draw.text((18,12),'前輪 · 切換三張整身圖',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 同一軀幹帶動肩臂',font=font,fill='#e0c9a2')
selected=[]
for i,(stage,age,label) in enumerate([('windup',700,'蓄刀：收身與持刀手一同移動'),('strike',120,'斬下：胸甲連續前傾，雙腳留在原位'),('recovery',240,'收刀：同一軀幹回正，不換人物圖')]):
 row=min((r for r in after if r['duel']['stage']==stage and r['enemy'].get('intent')==stage and r['hp']==3),key=lambda r:abs(r['duel']['age']-age))
 candidates=[r for r in before if r['duel']['stage']==stage and r['hp']==row['hp'] and r['duel']['playerHP']==row['duel']['playerHP'] and r['duel']['blocks']==row['duel']['blocks']]
 prev=min(candidates,key=lambda r:abs(r['duel']['age']-row['duel']['age']));offset=row['duel']['age']-prev['duel']['age'];assert abs(offset)<=17
 for x,p in [(0,TMP/f"before-{prev['sample']:03d}.png"),(600,ROOT/f".tmp/duel-check/frames/{row['sample']:03d}.png")]:
  im=Image.open(p).convert('RGB');assert im.size==(1200,750);plate.paste(im.resize((600,375),Image.Resampling.LANCZOS),(x,50+i*415))
 draw.text((18,428+i*415),label,font=font,fill='#e0c9a2')
 selected.append({'stage':stage,'beforeSample':prev['sample'],'afterSample':row['sample'],'beforeStageAgeMS':prev['duel']['age'],'afterStageAgeMS':row['duel']['age'],'sampleOffsetMS':offset,'beforeShoulder':prev['arm']['shoulder'],'afterShoulder':row['arm']['shoulder'],'actualTorso':row['enemyBodyParts']['torso']})
def largest(rows):
 changes=[]
 for a,b in zip(rows,rows[1:]):
  if a['enemy'].get('phase')==b['enemy'].get('phase')=='guard' and a['hp']==b['hp']==3:
   changes.append(math.hypot(a['arm']['shoulder']['x']-b['arm']['shoulder']['x'],a['arm']['shoulder']['y']-b['arm']['shoulder']['y'])*.6)
 return max(changes)
plate.save(OUT/'enemy-body-comparison.jpg',quality=94)
(OUT/'enemy-body-comparison.json').write_text(json.dumps({'baselineCommit':BASE,'selected':selected,'maxShoulderStepWorldPXAt30Hz':{'before':largest(before),'after':largest(after)},'source':'Before: committed real Phaser MP4. After: actual browser PNGs. Same stage, health and block count; stage-time offsets recorded, <=17 ms. Both resized equally.','limits':'Maximum shoulder step is a 30 Hz sample metric for this captured attack, not a general animation quality score. Hit/death retain authored silhouettes; no general physics.'},indent=2)+'\n')
print({'beforeMaxShoulderStep':largest(before),'afterMaxShoulderStep':largest(after),'stageOffsetsMS':[s['sampleOffsetMS'] for s in selected]})
