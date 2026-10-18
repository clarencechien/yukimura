"""Verify the crouch repair and every retained cell against the immediately preceding commit."""
from pathlib import Path
from io import BytesIO
import json,subprocess,hashlib,math
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';BASE='f97f3a1e63af572be6d4ea904e1de0ff07e2f4da'
old=lambda n:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
art=json.loads((OUT/'enemy-art.json').read_text());meta=art['crouchConsistency'];source=ROOT/meta['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['source']['sha256']
im=Image.open(source).convert('RGBA');scale=meta['uniformScale'];frame=Image.new('RGBA',(1152,768));frame.alpha_composite(im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS),tuple(meta['offsetHD']))
def same(a,b):
 a,b=np.array(a),np.array(b);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
for suffix,(w,h) in [('-hd',(1152,768)),('',(768,512))]:
 atlas=Image.open(OUT/f'ghost-warrior{suffix}.webp').convert('RGBA');baseline=Image.open(BytesIO(old(f'ghost-warrior{suffix}.webp'))).convert('RGBA');assert atlas.size==baseline.size
 for i in range(12):
  box=(i%3*w,i//3*h,(i%3+1)*w,(i//3+1)*h);actual=atlas.crop(box)
  same(actual,frame.resize((w,h),Image.Resampling.LANCZOS) if i==4 else baseline.crop(box))
rig=json.loads((OUT/'enemy-rig.json').read_text());previous=json.loads(old('enemy-rig.json'));b=rig['bindings'][4];a=previous['bindings'][4]
for i,(current,prior) in enumerate(zip(rig['bindings'],previous['bindings'])):
 if i!=4:assert current==prior
assert len(rig['bindings'])==len(previous['bindings'])
assert {k:v for k,v in rig.items() if k!='bindings'}=={k:v for k,v in previous.items() if k!='bindings'}
project=lambda p:[meta['offsetHD'][i]+p[i]*meta['uniformScale'] for i in range(2)]
assert b['shoulder']==project(meta['sourceShoulder'])
assert b['footContacts']==[project(p) for p in meta['sourceSoleCenters']]
assert b['sourceWrist'] is None # The independently attached far arm is absent in the source.
shoulder_shift=math.dist(b['shoulder'],a['shoulder']);sole_shifts=[math.dist(x,y) for x,y in zip(b['footContacts'],a['footContacts'])]
assert shoulder_shift<12 and max(sole_shifts)<5
for i in range(2):assert abs((b['wrist'][i]-b['shoulder'][i])-(a['wrist'][i]-a['shoulder'][i]))<1e-6
report={'passed':True,'baselineCommit':BASE,'checks':['Only pose 4 changed in both atlases; all 22 retained cells including repaired pose 3 preserve visible RGB and alpha.','HD cell matches uniform source resize and translation; mobile matches HD resample','All other bindings and shared arm/weapon metadata unchanged','New shoulder and soles manually registered; previous detached-arm local reach retained'],'shoulderShiftHD':shoulder_shift,'soleShiftsHD':sole_shifts,'source':meta,'limits':'Pixel preservation and manual registration checks, not proof of anatomy or silhouette continuity.'}
(OUT/'crouch-consistency-art-check.json').write_text(json.dumps(report,indent=2)+'\n');print({'passed':True,'shoulderShiftHD':shoulder_shift,'soleShiftsHD':sole_shifts})
