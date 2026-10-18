"""Verify retained source pixels, exact sweep boundary copies, and loaded texture budget."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
rig=json.loads((OUT/'thrust-rig.json').read_text());checks=[]
def same(a,b):
 a,b=np.array(a),np.array(b);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
original=Image.open(OUT/'guard-body-hd.webp').convert('RGBA').crop((1024,640,2048,1280))
leg_names=['rearFoot','frontFoot','rearShin','frontShin','rearThigh','frontThigh','lower']
assembled=Image.new('RGBA',original.size)
for name in leg_names:
 layer=rig['layers'][name];mask=Image.new('L',original.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in layer['polygon']],fill=255)
 if name!='lower':mask=mask.filter(ImageFilter.GaussianBlur(.35))
 rgba=np.array(original);rgba[:,:,3]=(rgba[:,:,3].astype(float)*np.array(mask)/255).round().astype('uint8')
 expected=Image.fromarray(rgba).crop(tuple(layer['box']));actual=Image.open(OUT/f'hero-{name}-hd.webp').convert('RGBA');same(expected,actual)
 assembled.alpha_composite(actual,tuple(layer['box'][:2]))
a,b=np.array(original),np.array(assembled);missing=(a[:,:,3]>240)&(b[:,:,3]<128);missing[:330]=False
assert not missing.any(),f'{missing.sum()} opaque lower-body pixels lost at rest'
checks.append('Seven rigid lower-body cutouts retain source colors and declared masks; no opaque lower silhouette holes at rest')
for row in rig['legacyBoundaryCells']:
 suffix=row['resolution'] if row['resolution']!='mobile' else '';w,h=(1024,640) if suffix else (512,320);i=0 if row['frame']==35 else 1
 expected=Image.open(ROOT/row['source']).convert('RGBA').crop(tuple(row['box']));actual=Image.open(OUT/f'sweep-boundary{suffix}.webp').convert('RGBA').crop((i*w,0,(i+1)*w,h));same(expected,actual)
checks.append('All four desktop/mobile legacy sweep boundary cells preserve visible pixels and alpha')
budget={}
for suffix,name in [('-hd','desktop'),('','mobile')]:
 names=[f'hero-{n}{suffix}.webp' for n in rig['layers']]+[f'{n}{suffix}.webp' for n in ['guard-yari','enemy-low','ghost-warrior']+['enemy-body-'+n for n in json.loads((OUT/'enemy-body-art.json').read_text())['layers']]]+[f'enemy-{n}.webp' for n in ['upper','fore','relax','open','katana','grip']]
 rows=[]
 for n in names:
  im=Image.open(OUT/n);assert max(im.size)<=4096;rows.append({'path':n,'size':im.size,'rgba8Bytes':im.width*im.height*4,'downloadBytes':(OUT/n).stat().st_size})
 current=sum(r['rgba8Bytes'] for r in rows)
 previous=json.loads(subprocess.check_output(['git','show','0891c0d:docs/routes/jigoku-2d/combat/shared-hero-art-check.json'],cwd=ROOT))['memory'][name]['currentRGBA8Bytes']
 budget[name]={'currentRGBA8Bytes':current,'previousRGBA8Bytes':previous,'savedRGBA8Bytes':previous-current,'loadedTextures':rows}
assert "this.load.spritesheet('enemyDuel'" not in (OUT/'game.mjs').read_text()
checks.append('All active texture dimensions <=4096; no legacy idle/thrust/sweep/boundary/guard atlases loaded by game.mjs')
code=(OUT/'game.mjs').read_text();assert '../yari-rigid/' not in code and "this.load.spritesheet('sweep'," not in code and "this.load.spritesheet('sweepBoundary'," not in code
assert "this.load.spritesheet('guardBody'" not in code and "this.load.spritesheet('guardHands'" not in code
baseline='0891c0d04344f84124d893fdcdd925bbae815d16'
for row in budget.values():
 for texture in row['loadedTextures']:
  name=OUT/texture['path']
  texture['sha256']=hashlib.sha256(name.read_bytes()).hexdigest()
  if texture['path'].startswith(('enemy-body-','ghost-warrior')):continue # Independently verified by check_enemy_body_art.py / check_buckle_consistency_art.py / check_crouch_consistency_art.py
  before=subprocess.check_output(['git','show',f'{baseline}:{name.relative_to(ROOT)}'],cwd=ROOT)
  assert name.read_bytes()==before,texture['path']
  texture['sha256']=hashlib.sha256(before).hexdigest()
checks.append('Retained hero/arm/weapon textures are byte-identical to baseline; shared body cutouts and the redrawn buckle/crouch atlas cells are verified separately')
report={'baselineCommit':baseline,'passed':True,'checks':checks,'memory':budget,'scope':'RGBA8 character texture estimate only; excludes background, render targets, driver overhead and mipmaps. Not a hardware GPU measurement.'}
(OUT/'shared-hero-art-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(checks);print({k:{n:round(v/1048576,3) for n,v in row.items() if n.endswith('Bytes')} for k,row in budget.items()})
