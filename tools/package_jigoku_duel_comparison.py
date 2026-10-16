"""Compare captured game frames against the previous published duel, not generated previews."""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/duel-check/frames';BASE='37e0c1293bd9b97d3a5fc76719f94498139635cb'
old=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/duel-preview.gif'],cwd=ROOT)))
previous=json.loads(subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/duel-capture.json'],cwd=ROOT));rows=json.loads((OUT/'duel-capture.json').read_text())
selected=[rows[0],next(r for r in rows if r['phase']=='attack' and 5<=r['frame']<=9),next(r for r in rows if r['phase']=='attack' and r['frame']==14),next(r for r in rows if r['phase']=='attack' and r['frame']==24)]
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1720),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((18,12),'前輪 · 待機與短刺使用舊圖集',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 同造型、固定雙臂與共用槍',font=font,fill='#e0c9a2')
report=[]
for i,(row,label) in enumerate(zip(selected,['同一待機造型','收槍蓄勢','送槍命中','回到戒備'])):
 sample=row['sample'];before=previous[sample];assert before['duel']['stage']==row['duel']['stage'];assert before['hp']==row['hp'] and before['duel']['playerHP']==row['duel']['playerHP']
 old.seek(sample);a=old.convert('RGB').resize((600,375),Image.Resampling.LANCZOS);b=Image.open(TMP/f'{sample:03}.png').convert('RGB').resize((600,375),Image.Resampling.LANCZOS)
 y=50+i*415;plate.paste(a,(0,y));plate.paste(b,(600,y));draw.text((18,y+378),label,font=font,fill='#e0c9a2')
 report.append({'sample':sample,'stage':row['duel']['stage'],'enemyPose':row['enemy']['pose'],'heroAction':row['heroArt']['action'],'heroFrame':row['frame'],'heroArms':row['heroArt'].get('arms'),'armOrder':row['armOrder'],'guardWeaponWidth':row['heroWeapon']['width'],'frontRegistrationError':row['heroWeapon']['pose']['registrationError']})
plate.save(OUT/'duel-motion-comparison.jpg',quality=94)
(OUT/'duel-motion-check.json').write_text(json.dumps({'baselineCommit':BASE,'source':'Previous committed GIF decoded at matching sample; new actual browser PNG resized identically. Same stage and health asserted, palette/noise can differ.','selected':report,'limits':'Idle, thrust and sweep share fixed-length arm/leg IK, planted feet and one spear; guard now uses the same continuous articulated rig. No 3D anatomy/force simulation.'},indent=2)+'\n')
print('Compared four actual gameplay samples against 37e0c12; matching rule stages and HP verified.')
