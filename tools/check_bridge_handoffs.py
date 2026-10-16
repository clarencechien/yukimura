"""Compare both new cuts with the old single cut and require later render equality."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
hashes={}
def read(variant,t,suffix):
 p=OUT/'handoffs'/variant/f'{t}-{suffix}.png';hashes[str(p.relative_to(OUT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return np.array(Image.open(p).convert('RGBA'))
def measure(variant,t):
 a=read(variant,t,'before-body')[:,:,3]>16;b=read(variant,t,'after-body')[:,:,3]>16
 x=read(variant,t,'before').astype(float);y=read(variant,t,'after').astype(float)
 return dict(time=t,bodyAlphaIoU=float((a&b).sum()/(a|b).sum()),bodyAlphaXorPixels=int((a^b).sum()),meanRGBDelta=float(abs(x[:,:,:3]-y[:,:,:3]).mean()))
old=measure('current',1220);new=[measure('bridge',t) for t in [1200,1240]]
assert min(r['bodyAlphaIoU'] for r in new)>old['bodyAlphaIoU']
assert max(r['bodyAlphaXorPixels'] for r in new)<old['bodyAlphaXorPixels']
for t in [1320,1440]:
 for suffix in ['before','after','before-body','after-body']:
  assert np.array_equal(read('current',t,suffix),read('bridge',t,suffix)),f'later rendered handoff changed: {t} {suffix}'
meta=json.loads((OUT/'bridge.json').read_text());assert json.loads((OUT/'handoffs/bridge/registration.json').read_text())==meta
assert hashlib.sha256((OUT/'fall.json').read_bytes()).hexdigest()==meta['comparisonSHA256']
report=dict(passed=True,baselineCommit=meta['baselineCommit'],oldCut=old,newCuts=new,laterHandoffPixelsIdentical=[1320,1440],imageSHA256=hashes,limits='Same Canvas crop and body-layer alpha threshold as handoff-check.json. Body overlap improves modestly and one cut becomes two. Peak mean RGB delta increases slightly. This does not prove smooth helmet motion, anatomy or physical weight transfer; still four discrete body drawings.')
(OUT/'bridge-handoff-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='imageSHA256'},indent=2))
