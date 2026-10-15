"""Compare captured game frames against the previous published duel, not generated previews."""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/duel-check/frames';BASE='d496634a164677c94131b900d51d535ab56c10fb'
old=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/duel-preview.gif'],cwd=ROOT)))
previous=json.loads(subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/duel-capture.json'],cwd=ROOT));rows=json.loads((OUT/'duel-capture.json').read_text())
selected=[next(r for r in rows if r['enemy']['pose']==16 and r['duel']['guardPose'] is None),next(r for r in rows if r['duel']['guardPose']==0),next(r for r in rows if r['enemy']['pose']==17 and r['duel']['blocks']==1),next(r for r in rows if r['enemy']['pose']==18)]
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
plate=Image.new('RGB',(1200,1720),'#1b2328');draw=ImageDraw.Draw(plate);draw.text((18,12),'前輪 · 共用站姿',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 新增出刀／架槍姿勢',font=font,fill='#e0c9a2')
report=[]
for i,(row,label) in enumerate(zip(selected,['蓄刀收身','幸村架槍','斬下與承力','鬼武者收刀'])):
 sample=row['sample'];before=previous[sample];assert before['duel']['stage']==row['duel']['stage'];assert before['hp']==row['hp'] and before['duel']['playerHP']==row['duel']['playerHP']
 old.seek(sample);a=old.convert('RGB').resize((600,375),Image.Resampling.LANCZOS);b=Image.open(TMP/f'{sample:03}.png').convert('RGB').resize((600,375),Image.Resampling.LANCZOS)
 y=50+i*415;plate.paste(a,(0,y));plate.paste(b,(600,y));draw.text((18,y+378),label,font=font,fill='#e0c9a2')
 report.append({'sample':sample,'stage':row['duel']['stage'],'enemyPose':row['enemy']['pose'],'heroGuardPose':row['duel']['guardPose'],'armOrder':row['armOrder']})
plate.save(OUT/'duel-motion-comparison.jpg',quality=94)
(OUT/'duel-motion-check.json').write_text(json.dumps({'baselineCommit':BASE,'source':'Previous committed GIF decoded at matching sample; new actual browser PNG resized identically. Same stage and health asserted, palette/noise can differ.','selected':report,'limits':'Key poses, not continuous motion; shoulders and painted hero yari can change projection between drawings.'},indent=2)+'\n')
print('Compared four actual gameplay samples against d496634; matching rule stages and HP verified.')
