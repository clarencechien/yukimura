"""Validate declared source registration/masks and isolation from production."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-transition';m=json.loads((OUT/'transition.json').read_text());source=ROOT/m['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==m['sha256'];raw=Image.open(source).convert('RGBA');memory=0
for f in m['frames']:
 reg=f['registration']
 if 'existing' in reg:frame=Image.open(OUT/reg['existing']).convert('RGBA')
 else:
  crop=raw.crop(reg['box']);scale=reg['scale'];small=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,reg['offset'])
  assert sum(a*n for a,n in enumerate(frame.getchannel('A').histogram()))==sum(a*n for a,n in enumerate(small.getchannel('A').histogram()))
  projected=[reg['offset'][i]+(reg['sourceShoulder'][i]-reg['box'][i])*scale for i in range(2)];assert projected==f['shoulder']
 coverage=np.zeros((768,1152),dtype=np.uint8)
 for name,part in f['parts'].items():
  mask=Image.new('L',frame.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in part['polygon']],fill=255);expected=np.array(frame);expected[:,:,3]=np.minimum(expected[:,:,3],np.array(mask));expected=np.array(Image.fromarray(expected).crop(part['box']));actual=np.array(Image.open(OUT/part['url']).convert('RGBA'));assert actual.shape==expected.shape
  assert np.array_equal(actual[:,:,3],expected[:,:,3]),(f['id'],name,'alpha')
  visible=expected[:,:,3]>0;assert np.array_equal(actual[:,:,:3][visible],expected[:,:,:3][visible]),(f['id'],name,'visible RGB')
  if name in ['torso','lower']:
   x,y,r,b=part['box'];coverage[y:b,x:r]=np.maximum(coverage[y:b,x:r],actual[:,:,3])
  if not part['url'].startswith('../'):memory+=actual.shape[0]*actual.shape[1]*4
 alpha=np.array(frame)[:,:,3];assert not np.any((alpha>coverage)&(alpha>1)),f['id']
protected=['docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-parts','docs/routes/jigoku-2d/free-arm-support','src','public']
subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE)
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*protected],cwd=ROOT).strip()
report={'passed':True,'baselineCommit':m['baselineCommit'],'checks':['Generated sheet hash; uniform per-pose scale/translation and no canvas clipping','Every packed torso/lower/cap preserves source alpha and visible RGB under declared masks','Torso/lower union covers all source pixels with alpha > 1','Previous arm/support kit and production combat/src/public unchanged'],'newLoadedRGBA8MiB':memory/1048576,'limits':'Memory estimate excludes reused arm, palm, kneel textures and Canvas buffers. Source landmarks are manual; no anatomy or force validation.'}
(OUT/'art-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
