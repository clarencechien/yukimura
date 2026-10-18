"""Compare actual browser captures: old decoded GIF and current PNGs at equal size."""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/combat-check/combo-frames';BASE='21d8b539b1a2abc9c38d2f0b8c0fdaf104cdf0aa'
old=lambda name:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
prior=json.loads(old('combo-capture.json'));current=json.loads((OUT/'combo-capture.json').read_text())
oldgif=Image.open(io.BytesIO(old('combo-preview.gif')))
assert oldgif.n_frames==len(prior)
last_recover=max(r['sample'] for r in prior if r['enemy']['phase']=='leg-recover')
old_rows=[next(r for r in prior if r['enemy']['phase']=='low-stagger'),next(r for r in prior if r['enemy']['phase']=='leg-recover'),prior[last_recover],next(r for r in prior if r['sample']>last_recover and r['enemy']['phase']=='guard')]
for row in current:
 if row['enemy']['phase'] in ['leg-rise','guard-settle']:
  for name in ['shoulder','elbow']:
   actual,local=row['renderedArm'][name],row['arm'][name]
   assert abs(actual['x']-(row['body']['x']+(local['x']-576)*.6))<1e-6
   assert abs(actual['y']-(574+(local['y']-690)*.6))<1e-6
  assert row['hand']['texture']=='enemyGrip' and row['weapon']['held']
last_settle=max(r['sample'] for r in current if r['enemy']['phase']=='guard-settle')
new_rows=[next(r for r in current if r['enemy']['phase']==phase) for phase in ['low-stagger','leg-rise','guard-settle']]+[next(r for r in current if r['sample']>last_settle and r['enemy']['phase']=='guard')]
plate=Image.new('RGB',(1536,900),'#1b2328');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',21)
for line,rows in enumerate([old_rows,new_rows]):
 for col,row in enumerate(rows):
  if line==0:oldgif.seek(row['sample']);im=oldgif.convert('RGB')
  else:im=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').resize((640,400),Image.Resampling.LANCZOS)
  # Both use the same 640x400 review size and crop; no anatomy edits.
  thumb=im.crop((403,88,640,347)).resize((384,414),Image.Resampling.LANCZOS)
  x,y=col*384,line*450;plate.paste(thumb,(x,y))
  label=[['前輪：失衡','回放受擊圖','仍持有同圖','戒備'],['本輪：失衡','抬身回正','收手回防','戒備']][line][col]
  ImageDraw.Draw(plate).text((x+12,y+420),label,font=font,fill='#e0c9a2')
plate.save(OUT/'recovery-comparison.jpg',quality=94)
# A separate plate uses current native screenshots to inspect attachment points.
inspection=Image.new('RGB',(1440,450),'#1b2328')
for i,row in enumerate(new_rows):
 im=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').crop((755,165,1200,650)).resize((360,400),Image.Resampling.LANCZOS)
 inspection.paste(im,(i*360,0));ImageDraw.Draw(inspection).text((i*360+12,410),['失衡','抬身','回防','戒備'][i],font=font,fill='#e0c9a2')
inspection.save(OUT/'recovery-sequence.jpg',quality=94)
report={'baselineCommit':BASE,'beforeSource':'Decoded baseline combo-preview.gif, same sample indices as baseline combo-capture.json','afterSource':'Current actual Phaser PNG captures; downsampled to same 640x400 only for comparison','beforeSamples':[r['sample'] for r in old_rows],'afterSamples':[r['sample'] for r in new_rows],'afterRenderedBindings':[{'phase':r['enemy']['phase'],'texture':r['enemyTexture'],'frame':r['enemyFrame'],'shoulder':r['renderedArm']['shoulder'],'actualBodyParts':r['enemyBodyParts']} for r in new_rows],'scope':'Static comparison of previous authored silhouettes and current shared rigid parts; not optical flow or anatomy validation.'}
assert all(r['enemyBodyPose'] and not r['legacyBodyVisible'] for r in new_rows)
assert all(len(r['enemyBodyParts'])==8 and all(p['visible'] for p in r['enemyBodyParts'].values()) for r in new_rows)
assert [r['enemyTexture'] for r in new_rows]==['warrior']*4
(OUT/'recovery-preview-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared equal-size before/after recovery comparison and native runtime pose plate.')
