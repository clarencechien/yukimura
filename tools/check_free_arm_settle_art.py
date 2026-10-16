"""Verify source pixels and actual shoe alpha clearance along the JS rig path."""
from pathlib import Path
import hashlib,json,math,subprocess
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((OUT/'settle.json').read_text());frames={};memory=0
for key,sourceKey in [('original','source'),('restored','restored')]:
 spec=m[sourceKey];source=ROOT/spec['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['sha256'];raw=Image.open(source).convert('RGBA')
 if 'box' in spec:raw=raw.crop(spec['box'])
 small=raw.resize((round(raw.width*spec['scale']),round(raw.height*spec['scale'])),Image.Resampling.LANCZOS);frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,spec['offset']);frames[key]=frame
 assert sum(a*n for a,n in enumerate(frame.getchannel('A').histogram()))==sum(a*n for a,n in enumerate(small.getchannel('A').histogram()))
def polygon_mask(points):
 mask=Image.new('L',(1152,768));ImageDraw.Draw(mask).polygon([tuple(v) for v in points],fill=255);return np.array(mask)
removed=np.minimum(polygon_mask(m['vacatedLegPolygon']),255-polygon_mask(m['preservedKneePolygon']))
assert {name for name,p in m['parts'].items() if p['source']=='restored'}=={'restore'}
for name,p in m['parts'].items():
 frame=frames[p['source']];mask=Image.new('L',frame.size);ImageDraw.Draw(mask).polygon([tuple(v) for v in p['polygon']],fill=255);a=np.array(frame);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));
 if name in ['lower','waist']:
  assert p['source']=='original' and p['legMaskRule']=='subtract';a[:,:,3]=np.minimum(a[:,:,3],255-removed)
 if name=='restore':
  assert p['legMaskRule']=='inside';a[:,:,3]=np.minimum(a[:,:,3],removed)
 expected=np.array(Image.fromarray(a).crop(p['box']));actual=np.array(Image.open(OUT/p['url']).convert('RGBA'));assert actual.shape==expected.shape;assert np.array_equal(actual[:,:,3],expected[:,:,3]);visible=expected[:,:,3]>0;assert np.array_equal(actual[:,:,:3][visible],expected[:,:,:3][visible]),name;memory+=actual.shape[0]*actual.shape[1]*4
# The only generated pixels must be inside the removed-leg region and outside the retained knee.
r=m['parts']['restore'];patch=np.zeros((768,1152),dtype=np.uint8);x0,y0,x1,y1=r['box'];patch[y0:y1,x0:x1]=np.array(Image.open(OUT/r['url']))[:,:,3];assert not np.any((patch>0)&(removed==0));assert not np.any((patch>0)&(polygon_mask(m['preservedKneePolygon'])>0))
p=m['parts']['shoe'];alpha=np.array(Image.open(OUT/p['url']))[:,:,3];y,x=np.where(alpha>16);xy=np.stack([x-p['pivot'][0],y-p['pivot'][1]]);initial=m['ankle'][1]+xy[1].max()
script="""import fs from 'node:fs';import {settlePose} from './docs/routes/jigoku-2d/free-arm-settle/rig.mjs';const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json');const rows=[];for(let i=0;i<=1000;i++){const p=settlePose(400+i/10,m,tr,k,s);rows.push({t:p.age,leg:p.leg,torso:p.torso});}process.stdout.write(JSON.stringify(rows));"""
rows=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));maximum=-math.inf
for row in rows:
 leg=row['leg'];r=math.radians(leg['shoeAngle']);rot=np.array([[math.cos(r),-math.sin(r)],[math.sin(r),math.cos(r)]]);pixels=rot@xy+np.array([leg['ankle']['x'],leg['ankle']['y']])[:,None];maximum=max(maximum,float(pixels[1].max()))
assert maximum<=initial+1e-6
protected=['docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-parts','docs/routes/jigoku-2d/free-arm-support','docs/routes/jigoku-2d/free-arm-transition','src','public']
subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE);assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*protected],cwd=ROOT).strip()
weapon=json.loads((OUT/'sword-kit.json').read_text());weaponMemory=0
for asset in [weapon['rig'],*weapon['textures']]:
 path=(OUT/asset['url']).resolve();assert path.is_relative_to(ROOT)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256'],asset['url']
 if 'size' in asset:
  im=Image.open(path);assert list(im.size)==asset['size'];weaponMemory+=im.width*im.height*4
subprocess.run(['git','diff','--exit-code',weapon['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE)
release=json.loads((OUT/'release.json').read_text());handMemory=0
for asset in release['textures']:
 path=(OUT/asset['url']).resolve();assert path.is_relative_to(ROOT)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256']
 im=Image.open(path);assert list(im.size)==asset['size'];handMemory+=im.width*im.height*4
blade=OUT.parent/'combat/enemy-katana.webp';assert hashlib.sha256(blade.read_bytes()).hexdigest()==release['bladeSha256']
alpha=np.array(Image.open(blade).convert('RGBA'))[:,:,3];y,x=np.where(alpha>0)
# Use all four pixel-cell corners, including translucent edge pixels, not just marked hull points.
points=np.concatenate([np.stack([x+dx,y+dy]) for dx,dy in [(0,0),(1,0),(0,1),(1,1)]],axis=1)
hull=np.array(release['bladeHull'])
for a,b in zip(hull,np.roll(hull,-1,axis=0)):
 assert np.all((b[0]-a[0])*(points[1]-a[1])-(b[1]-a[1])*(points[0]-a[0])>=0), 'hull must contain every visible pixel cell'
rig=json.loads((OUT.parent/'combat/enemy-rig.json').read_text());points=points-np.array(rig['parts']['katana']['pivot'])[:,None]
releaseScript="""import fs from 'node:fs';import {settlePose} from './docs/routes/jigoku-2d/free-arm-settle/rig.mjs';import {releasingSword} from './docs/routes/jigoku-2d/free-arm-settle/release.mjs';const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rig=read('combat/enemy-rig.json'),meta=read('free-arm-settle/release.json'),rows=[];for(let i=0;i<=1000;i++){const t=540+i*.46;rows.push(releasingSword(t,settlePose(t,m,tr,k,s),m,rig,meta));}process.stdout.write(JSON.stringify(rows));"""
releaseRows=json.loads(subprocess.check_output(['node','--input-type=module','-e',releaseScript],cwd=ROOT));bladeMax=-math.inf
for pose in releaseRows:
 angle=math.radians(pose['bladeAngle']);bottom=points[0]*math.sin(angle)+points[1]*math.cos(angle)+pose['grip']['y'];bladeMax=max(bladeMax,float(bottom.max()))
 assert bottom.max()<=release['groundY']+1e-6
 if pose['grounded']:assert abs(float(bottom.max())-release['groundY'])<1e-6
report={'passed':True,'baselineCommit':m['baselineCommit'],'checks':['Original torso/cap/lower/waist/shin/shoe pixels retained; generated pixels only in the vacated leg region, never on the retained knee','Uniform source registration with no canvas clipping','1001 actual JS rig samples: all shoe pixels alpha > 16 stay above initial bottom in projected screen Y','Existing sword-side and two release-hand texture hashes and dimensions verified; no new images or modified production assets','1001 release samples: all visible katana pixel-cell corners above projected ground, contact matches bottom edge','Previous prototypes, production combat/src/public unchanged'],'shoeStartBottomY':float(initial),'shoeMaximumBottomY':maximum,'maxWaistTranslationPx':max(math.hypot(r['torso']['offset']['x'],r['torso']['offset']['y']) for r in rows),'settlePartsRGBA8MiB':memory/1048576,'reusedSwordPartsRGBA8MiB':weaponMemory/1048576,'swordSourceHashesVerified':True,'releaseHandPartsRGBA8MiB':handMemory/1048576,'bladeMaximumBottomY':bladeMax,'releasePixelSamples':len(releaseRows),'restoredVisiblePixels':int(np.count_nonzero(patch>16)),'limits':'Projected sprite clearance only, not 3D ground contact or collision physics. Memory excludes reused textures and Canvas buffers.'}
(OUT/'art-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
