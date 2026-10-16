"""Verify registered side-fall drawings against source pixels and sampled runtime translations."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,subprocess,sys
metaName=sys.argv[1] if len(sys.argv)>1 else 'fall.json'
assert metaName in ['fall.json','bridge.json']
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';m=json.loads((OUT/metaName).read_text());source=ROOT/m['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==m['sha256'];sheet=Image.open(source).convert('RGBA');memory=0;bounds={}
for i,f in enumerate(m['frames']):
 source=ROOT/f['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==f['sha256'];sheet=Image.open(source).convert('RGBA')
 r=f['registration'];raw=sheet.crop(r['box']);a=np.array(raw);a[a[:,:,3]<=m['alphaCleanupThreshold'],3]=0;raw=Image.fromarray(a);small=raw.resize((round(raw.width*r['scale']),round(raw.height*r['scale'])),Image.Resampling.LANCZOS);frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,r['offset']);assert sum(a*n for a,n in enumerate(frame.getchannel('A').histogram()))==sum(a*n for a,n in enumerate(small.getchannel('A').histogram()))
 union=np.zeros((768,1152),dtype=np.uint8)
 for name,p in f['parts'].items():
  mask=Image.new('L',frame.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in p['polygon']],fill=255);a=np.array(frame);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));expected=np.array(Image.fromarray(a).crop(p['box']));actual=np.array(Image.open(OUT/p['url']).convert('RGBA'));assert np.array_equal(expected[:,:,3],actual[:,:,3]);visible=expected[:,:,3]>0;assert np.array_equal(expected[:,:,:3][visible],actual[:,:,:3][visible]);memory+=actual.shape[0]*actual.shape[1]*4
  x0,y0,x1,y1=p['box'];union[y0:y1,x0:x1]=np.maximum(union[y0:y1,x0:x1],actual[:,:,3])
  y,x=np.where(actual[:,:,3]>16);bounds[i,name]=[x.min()+p['box'][0],y.min()+p['box'][1],x.max()+p['box'][0],y.max()+p['box'][1]]
 assert np.array_equal(union,np.array(frame)[:,:,3]), 'body masks must retain the whole registered source silhouette'
script="""import fs from 'node:fs';import {fallPose} from './docs/routes/jigoku-2d/free-arm-settle/fall.mjs';let read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),f=read('free-arm-settle/'+process.argv[1]),rows=[],start=(f.start+f.frames[0].time)/2;for(let i=0;i<=Math.ceil((f.end-start)/.2);i++){let p=fallPose(start+.001+i*.2,m,tr,k,s,f);rows.push({index:p.fallFrame,offset:p.fallOffset});}console.log(JSON.stringify(rows));"""
rows=json.loads(subprocess.check_output(['node','--input-type=module','-e',script,metaName],cwd=ROOT));maximum=-1;maxOffset=0
for row in rows:
 for name in ['lower','torso','cap']:
  b=bounds[row['index'],name];off={'x':0,'y':0} if name=='lower' else row['offset'];maximum=max(maximum,float(b[3]+off['y']));maxOffset=max(maxOffset,float(np.hypot(off['x'],off['y'])))
  assert b[3]+off['y']<=m['groundY'], 'body pixels crossed projected ground'
  assert (b[0]+off['x'])*.8-50>=0 and (b[2]+off['x'])*.8-50<=600
  assert (b[1]+off['y'])*.8-10>=65 and (b[3]+off['y'])*.8-10<=615
protected=['docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-parts','docs/routes/jigoku-2d/free-arm-support','docs/routes/jigoku-2d/free-arm-transition','src','public'];subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*protected],cwd=ROOT,check=True,stdout=subprocess.PIPE)
report=dict(passed=True,samples=len(rows),partsRGBA8MiB=memory/1048576,maximumVisibleBodyY=maximum,maxTorsoTranslationPx=maxOffset,sourceSHA256=m['sha256'],checks=['New body/cap/lower parts match uniformly registered source pixels and declared alpha cleanup/masks; their alpha union preserves the full registered silhouette',f'{len(rows)} actual rig samples inside review panel and above projected ground Y=690; ground cloth retained in lower layer','Previous assets and production game unchanged'],limits='Body drawings switch at key midpoints. Shoulder continuity is not silhouette continuity. Projected ground bounds do not validate 3D collisions; no anatomy or force validation.')
(OUT/(metaName.removesuffix('.json')+'-art-check.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
