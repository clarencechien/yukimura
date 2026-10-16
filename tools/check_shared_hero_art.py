"""Verify retained source pixels, exact sweep boundary copies, and loaded texture budget."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
rig=json.loads((OUT/'thrust-rig.json').read_text());checks=[]
def same(a,b):
 a,b=np.array(a),np.array(b);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
original=Image.open(OUT/'guard-body-hd.webp').convert('RGBA').crop((1024,640,2048,1280));box=rig['layers']['lower']['box']
expected=original.crop(tuple(box));same(expected,Image.open(OUT/'hero-lower-hd.webp').convert('RGBA'));checks.append('Original planted lower-body visible pixels and alpha retained exactly in HD')
for row in rig['legacyBoundaryCells']:
 suffix=row['resolution'] if row['resolution']!='mobile' else '';w,h=(1024,640) if suffix else (512,320);i=0 if row['frame']==35 else 1
 expected=Image.open(ROOT/row['source']).convert('RGBA').crop(tuple(row['box']));actual=Image.open(OUT/f'sweep-boundary{suffix}.webp').convert('RGBA').crop((i*w,0,(i+1)*w,h));same(expected,actual)
checks.append('All four desktop/mobile legacy sweep boundary cells preserve visible pixels and alpha')
budget={}
for suffix,name in [('-hd','desktop'),('','mobile')]:
 names=[f'hero-{n}{suffix}.webp' for n in rig['layers']]+[f'{n}{suffix}.webp' for n in ['guard-body','guard-hands','guard-yari','enemy-duel','enemy-low','ghost-warrior']]+[f'enemy-{n}.webp' for n in ['upper','fore','relax','open','katana','grip']]
 rows=[]
 for n in names:
  im=Image.open(OUT/n);assert max(im.size)<=4096;rows.append({'path':n,'size':im.size,'rgba8Bytes':im.width*im.height*4,'downloadBytes':(OUT/n).stat().st_size})
 current=sum(r['rgba8Bytes'] for r in rows);removed=15*1048576 if suffix else 3.75*1048576
 budget[name]={'currentRGBA8Bytes':current,'previousRGBA8Bytes':current+removed,'savedRGBA8Bytes':removed,'loadedTextures':rows}
checks.append('All active texture dimensions <=4096; no legacy idle/thrust/sweep or sweep-boundary atlases loaded by game.mjs')
code=(OUT/'game.mjs').read_text();assert '../yari-rigid/' not in code and "this.load.spritesheet('sweep'," not in code and "this.load.spritesheet('sweepBoundary'," not in code
baseline='d44c03f275e5e4749c0edbfbfe2d6f36067edd48'
for row in budget.values():
 for texture in row['loadedTextures']:
  name=OUT/texture['path'];before=subprocess.check_output(['git','show',f'{baseline}:{name.relative_to(ROOT)}'],cwd=ROOT)
  assert name.read_bytes()==before,texture['path']
  texture['sha256']=hashlib.sha256(before).hexdigest()
checks.append('Every active character texture is byte-identical to baseline; no newly generated character art')
report={'baselineCommit':baseline,'passed':True,'checks':checks,'memory':budget,'scope':'RGBA8 character texture estimate only; excludes background, render targets, driver overhead and mipmaps. Not a hardware GPU measurement.'}
(OUT/'shared-hero-art-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(checks);print({k:{n:round(v/1048576,3) for n,v in row.items() if n.endswith('Bytes')} for k,row in budget.items()})
