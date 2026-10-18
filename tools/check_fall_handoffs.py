"""Compare captured body-layer alpha and full-color handoffs, not joint continuity."""
from pathlib import Path
from PIL import Image
import numpy as np
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
rows=[];hashes={}
for time in [1220,1320,1440]:
 row={'time':time}
 for variant in ['baseline','current','rejected']:
  folder=OUT/'handoffs'/variant
  def read(suffix):
   p=folder/f'{time}-{suffix}.png';hashes[str(p.relative_to(OUT))]=hashlib.sha256(p.read_bytes()).hexdigest()
   return np.array(Image.open(p).convert('RGBA'))
  a=read('before-body')[:,:,3]>16;b=read('after-body')[:,:,3]>16
  before=read('before').astype(float);after=read('after').astype(float)
  assert before.shape==after.shape==(550,600,4)
  row[variant]={'bodyAlphaIoU':float((a&b).sum()/(a|b).sum()),'bodyAlphaXorPixels':int((a^b).sum()),'meanRGBDelta':float(abs(before[:,:,:3]-after[:,:,:3]).mean())}
 rows.append(row)
assert rows[0]['current']==rows[0]['baseline'], 'first handoff must be reported unchanged'
assert rows[1]['current']['bodyAlphaIoU']>rows[1]['baseline']['bodyAlphaIoU']+.04
assert rows[2]['current']['bodyAlphaIoU']>=rows[2]['baseline']['bodyAlphaIoU']
assert rows[1]['rejected']['bodyAlphaIoU']<rows[1]['baseline']['bodyAlphaIoU']
current=json.loads((OUT/'fall.json').read_text())
assert json.loads((OUT/'handoffs/current/registration.json').read_text())==current,'recapture after changing registration'
assert all(f['registration']['scale']==.70 for f in current['frames'])
report={'baselineCommit':'800ab1ff49c7314ba8aa9acf4d4cee0b044fb6a0','passed':True,'times':rows,'capture':{'beforeOffsetMs':-.001,'afterOffsetMs':.001,'canvasCrop':[600,65,600,550],'bodyMaskAlphaThreshold':16},'imageSHA256':hashes,'limits':'Body-layer alpha excludes separate arms, weapon and articulated leg draw calls. RGB uses the complete cropped render. Higher IoU does not validate anatomy, reduce all color changes, or imply continuous animation. Current first handoff is unchanged; later RGB differences increase despite improved normalized silhouette overlap. Rejected redraw is retained only for comparison.'}
(OUT/'handoff-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(rows,indent=2))
