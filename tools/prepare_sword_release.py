"""Record existing hand textures and an alpha-derived katana contact hull; no image edits."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';COMBAT=OUT.parent/'combat'
im=Image.open(COMBAT/'enemy-katana.webp').convert('RGBA');alpha=im.getchannel('A')
points=set()
for y in range(im.height):
 xs=[x for x in range(im.width) if alpha.getpixel((x,y))>0]
 if xs:
  for x in [min(xs),max(xs)+1]:
   points.update([(x,y),(x,y+1)])
def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
def half(points):
 out=[]
 for p in points:
  while len(out)>1 and cross(out[-2],out[-1],p)<=0:out.pop()
  out.append(p)
 return out
points=sorted(points);hull=half(points)[:-1]+half(points[::-1])[:-1]
textures=[]
for name in ['relax','open']:
 p=COMBAT/f'enemy-{name}.webp';textures.append(dict(name=name,url=f'../combat/enemy-{name}.webp',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=list(Image.open(p).size)))
meta=dict(releaseAge=540,openAge=600,landAge=860,endAge=1000,groundY=690,driftX=140,fallDistance=220,handReturn=[12,16],handReturnMs=220,bladeHull=hull,bladeSha256=hashlib.sha256((COMBAT/'enemy-katana.webp').read_bytes()).hexdigest(),textures=textures,method='Held transform at 540 ms is the release origin. Authored fall and rotation, alpha-hull ground constraint, then horizontal rest. Hand returns independently. Projected contact only, no rigid-body dynamics or new artwork.')
(OUT/'release.json').write_text(json.dumps(meta,indent=2)+'\n')
