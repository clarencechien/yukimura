"""Compare captured game frames against the previous published duel, not generated previews."""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/duel-check/frames';BASE='833111fcbb9b7872efed08f00110cd9ab4b71b89'
old=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/duel-preview.gif'],cwd=ROOT)))
previous=json.loads(subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/duel-capture.json'],cwd=ROOT));rows=json.loads((OUT/'duel-capture.json').read_text())
selected=[next(r for r in rows if r['duel']['guardPose']==pose) for pose in range(4)]
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1720),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((18,12),'前輪 · 兩張整圖格擋',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 四姿勢與共用槍',font=font,fill='#e0c9a2')
report=[]
for i,(row,label) in enumerate(zip(selected,['抬槍交接','架槍','承力','放槍交接'])):
 sample=row['sample'];before=previous[sample];assert before['duel']['stage']==row['duel']['stage'];assert before['hp']==row['hp'] and before['duel']['playerHP']==row['duel']['playerHP']
 old.seek(sample);a=old.convert('RGB').resize((600,375),Image.Resampling.LANCZOS);b=Image.open(TMP/f'{sample:03}.png').convert('RGB').resize((600,375),Image.Resampling.LANCZOS)
 y=50+i*415;plate.paste(a,(0,y));plate.paste(b,(600,y));draw.text((18,y+378),label,font=font,fill='#e0c9a2')
 report.append({'sample':sample,'stage':row['duel']['stage'],'enemyPose':row['enemy']['pose'],'heroGuardPose':row['duel']['guardPose'],'armOrder':row['armOrder'],'guardWeaponWidth':row['guardWeapon']['width'],'frontRegistrationError':row['guardWeapon']['pose']['registrationError']})
plate.save(OUT/'duel-motion-comparison.jpg',quality=94)
(OUT/'duel-motion-check.json').write_text(json.dumps({'baselineCommit':BASE,'source':'Previous committed GIF decoded at matching sample; new actual browser PNG resized identically. Same stage and health asserted, palette/noise can differ.','selected':report,'limits':'Key poses, not continuous motion; body and shoulders can still change projection; the four guard poses now share a rigid spear, while idle/thrust/sweep still contain baked weapons.'},indent=2)+'\n')
print('Compared four actual gameplay samples against 833111f; matching rule stages and HP verified.')
