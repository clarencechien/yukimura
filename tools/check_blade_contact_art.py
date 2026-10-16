"""Check contact markers against opaque steel pixels in the unchanged blade texture."""
from pathlib import Path
import json,re,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
points=json.loads(re.search(r'BLADE_CONTACT_LINE=(\[[^;]+);',(OUT/'duel-contact.mjs').read_text()).group(1))
im=Image.open(OUT/'enemy-katana.webp').convert('RGBA');alpha=[]
for a,b in zip(points,points[1:]):
 for i in range(101):
  t=i/100;x=round(a[0]+(b[0]-a[0])*t);y=round(a[1]+(b[1]-a[1])*t);alpha.append(im.getpixel((x,y))[3])
assert min(alpha)>=240,min(alpha)
report={'passed':True,'source':'enemy-katana.webp','sha256':hashlib.sha256((OUT/'enemy-katana.webp').read_bytes()).hexdigest(),'size':im.size,'contactPolyline':points,'sampledPoints':len(alpha),'minimumAlpha':min(alpha),'method':'Manually marked visible steel polyline. 303 pixel samples verify opacity, not material recognition or a 3D collision surface.'}
(OUT/'blade-contact-art-check.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
