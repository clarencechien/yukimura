"""Reuse the earlier bowed-head candidate as an extra key, not a replacement pose."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,copy
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
base=json.loads((OUT/'fall.json').read_text())
frame=copy.deepcopy(json.loads((OUT/'handoffs/rejected/registration.json').read_text())['frames'][0])
frame.update(id='bridge',time=1220,label='低頭過渡')
source=ROOT/frame['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==frame['sha256']
r=frame['registration'];raw=Image.open(source).convert('RGBA').crop(r['box']);a=np.array(raw);a[a[:,:,3]<=base['alphaCleanupThreshold'],3]=0
small=Image.fromarray(a).resize((round(raw.width*r['scale']),round(raw.height*r['scale'])),Image.Resampling.LANCZOS)
canvas=Image.new('RGBA',(1152,768));canvas.alpha_composite(small,r['offset'])
for name,p in frame['parts'].items():
 mask=Image.new('L',canvas.size);ImageDraw.Draw(mask).polygon([tuple(q) for q in p['polygon']],fill=255)
 a=np.array(canvas);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));im=Image.fromarray(a);box=im.getbbox()
 assert list(box)==p['box'];p['url']=f'fall-bridge-{name}.webp';im.crop(box).save(OUT/p['url'],lossless=True,method=6)
base.update(baselineCommit='a639af6bb3ae0ca0aa4c0ae7a835e98eb6312912',comparison='fall.json',comparisonSHA256=hashlib.sha256((OUT/'fall.json').read_bytes()).hexdigest(),method='Reuse the previously rejected first bowed-head drawing only as a 1220 ms bridge key. Keep the original roll/side/rest keys and their timing. Nearest-key image selection; no crossfade, morph, or new image generation. Continuous shared arms do not imply continuous body silhouettes.')
base['frames'].insert(0,frame)
(OUT/'bridge.json').write_text(json.dumps(base,indent=2)+'\n')
print('Prepared three bridge parts; original three keys unchanged.')
