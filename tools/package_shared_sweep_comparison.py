"""Compare actual old/new combo captures at equal sweep frame and health."""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/combat-check/combo-frames';BASE='d44c03f275e5e4749c0edbfbfe2d6f36067edd48'
old=lambda name:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
gif=Image.open(io.BytesIO(old('combo-preview.gif')));previous=json.loads(old('combo-capture.json'));rows=json.loads((OUT/'combo-capture.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1720),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((18,12),'前輪 · 橫掃切換另一批人物圖',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 同一身體、雙臂與槍',font=font,fill='#e0c9a2')
report=[]
for i,(phase,label) in enumerate([(1,'下槍'),(2,'掃中脛甲'),(3,'隨勢'),(5,'收槍回到同一造型')]):
 matches=[(r,b) for r in rows if r['sweepPose']==phase for b in previous if b['phase']=='attack' and b['attackKind']=='sweep' and b['frame']==r['frame'] and b['hp']==r['hp']]
 assert matches,phase
 row,before=matches[0];assert row['heroWeapon']['visible'] and row['heroArt']['action']=='sweep'
 gif.seek(before['sample']);a=gif.convert('RGB').resize((600,375),Image.Resampling.LANCZOS)
 b=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').resize((600,375),Image.Resampling.LANCZOS)
 y=50+i*415;plate.paste(a,(0,y));plate.paste(b,(600,y));draw.text((18,y+378),label,font=font,fill='#e0c9a2')
 report.append({'beforeSample':before['sample'],'afterSample':row['sample'],'sharedAttackFrame':row['frame'],'hp':row['hp'],'timingPhase':phase,'arms':row['heroArt']['arms'],'tip':row['collisionTip']})
plate.save(OUT/'shared-sweep-comparison.jpg',quality=94)
(OUT/'shared-sweep-comparison.json').write_text(json.dumps({'baselineCommit':BASE,'selected':report,'source':'Baseline committed actual GIF and new browser PNG, matched at identical attack frame and health; resized identically. Palette/noise can differ.','limits':'Fixed-camera planar low arc, not a complete lateral 3D sweep. Feet are planted; small pelvis/leg loading is authored, without stepping or force simulation.'},indent=2)+'\n')
print('Compared four actual low-sweep frames against d44c03f at identical attack frame and HP.')
