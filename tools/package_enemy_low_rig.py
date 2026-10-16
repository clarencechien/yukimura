"""Compare real low-hit footage at matched attack frames and health."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/enemy-low-rig';TMP.mkdir(exist_ok=True)
BASE='0891c0d04344f84124d893fdcdd925bbae815d16'
old=lambda n:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
(TMP/'before.mp4').write_bytes(old('combo-30fps.mp4'))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/'before.mp4'),'-start_number','0',str(TMP/'before-%03d.png')],check=True)
previous=json.loads(old('combo-capture.json'));current=json.loads((OUT/'combo-capture.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22);plate=Image.new('RGB',(1200,1305),'#1b2328');draw=ImageDraw.Draw(plate)
draw.text((18,12),'前輪 · 四張整身低掃反應圖',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 同一腰胯雙腿，腳底固定',font=font,fill='#e0c9a2')
selected=[]
for i,(age,label) in enumerate([(0,'命中：從當下姿勢接續'),(140,'承重：腰胯下沉，雙膝彎曲'),(320,'回穩：原腳位上起身回防')]):
 row=min((r for r in current if r['enemy'].get('bodyReaction',{}).get('kind')=='sweep'),key=lambda r:abs(r['enemyAge']-age))
 candidates=[r for r in previous if r['enemy'].get('reaction')=='sweep' and r['hp']==row['hp'] and r['phase']==row['phase'] and r['attackKind']==row['attackKind'] and r['frame']==row['frame']]
 before=min(candidates,key=lambda r:abs(r['enemyAge']-row['enemyAge']));offset=row['enemyAge']-before['enemyAge'];assert abs(offset)<=17
 for x,p in [(0,TMP/f"before-{before['sample']:03d}.png"),(600,ROOT/f".tmp/combat-check/combo-frames/{row['sample']:03d}.png")]:
  im=Image.open(p).convert('RGB');assert im.size==(1200,750);plate.paste(im.resize((600,375),Image.Resampling.LANCZOS),(x,50+i*415))
 draw.text((18,428+i*415),label,font=font,fill='#e0c9a2')
 selected.append({'beforeSample':before['sample'],'afterSample':row['sample'],'attackFrame':row['frame'],'beforeReactionAgeMS':before['enemyAge'],'afterReactionAgeMS':row['enemyAge'],'sampleOffsetMS':offset,'actualParts':row['enemyBodyParts'],'legs':row['enemyBodyPose']['legs']})
 if i==1:
  Image.open(ROOT/f".tmp/combat-check/combo-frames/{row['sample']:03d}.png").crop((790,390,1170,610)).resize((1140,660),Image.Resampling.LANCZOS).save(OUT/'enemy-low-rig-detail.jpg',quality=95)
plate.save(OUT/'enemy-low-rig-comparison.jpg',quality=94)
rest=current[0]['enemyBodyParts'];drift={side:max(math.hypot(r['enemyBodyParts'][side+'Foot']['x']-rest[side+'Foot']['x'],r['enemyBodyParts'][side+'Foot']['y']-rest[side+'Foot']['y']) for r in current) for side in ['left','right']}
assert max(drift.values())<1e-6
drop=max(r['enemyBodyParts']['lower']['y']-rest['lower']['y'] for r in current)
assert drop>10
(OUT/'enemy-low-rig-comparison.json').write_text(json.dumps({'baselineCommit':BASE,'selected':selected,'actualFootAnchorDriftWorldPX':drift,'actualPelvisDropWorldPX':drop,'source':'Prior committed MP4 vs current real Phaser PNG; same attack frame, attack kind and health. Reaction time offsets <=17 ms, recorded per pair. Detail is an enlarged screenshot crop.','limits':'Rigid planar cutouts and fixed-length two-bone legs. No contact dynamics, stepping or three-dimensional anatomical reconstruction. Fatal hits use a shared 180 ms bridge, then authored silhouettes; this comparison only measures nonfatal low hits.'},indent=2)+'\n')
print({'actualFootAnchorDriftPX':drift,'actualPelvisDropPX':drop,'comparisonOffsetsMS':[r['sampleOffsetMS'] for r in selected]})
