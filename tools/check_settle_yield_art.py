"""Check reused near-hand source and actual torso/cap pixels over the unloading curve."""
from pathlib import Path
from PIL import Image
import numpy as np
import hashlib,json,subprocess,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';meta=json.loads((OUT/'yield.json').read_text());settle=json.loads((OUT/'settle.json').read_text())
source=(OUT/meta['nearHand']['url']).resolve();assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['nearHand']['sha256']
script="""import fs from 'node:fs';import {yieldPose,YIELD} from './docs/routes/jigoku-2d/free-arm-settle/yield.mjs';const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rows=[];for(let i=0;i<=1000;i++)rows.push(yieldPose(860+i*.32,m,tr,k,s).torso);console.log(JSON.stringify({parameters:YIELD,rows}));"""
result=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));assert result['parameters']==meta['parameters']
maximum=-math.inf;left=math.inf;right=-math.inf
for name in ['torso','cap']:
 p=settle['parts'][name];a=np.array(Image.open(OUT/p['url']).convert('RGBA'))[:,:,3];y,x=np.where(a>16);points=np.stack([x+p['box'][0],y+p['box'][1]])
 for h in result['rows']:
  r=math.radians(h['angle']);rot=np.array([[math.cos(r),-math.sin(r)],[math.sin(r),math.cos(r)]]);pivot=np.array([h['pivot']['x'],h['pivot']['y']])[:,None];offset=np.array([h['offset']['x'],h['offset']['y']])[:,None];world=rot@(points-pivot)+pivot+offset
  maximum=max(maximum,float(world[1].max()));left=min(left,float(world[0].min()));right=max(right,float(world[0].max()))
  assert world[1].max()<=690, 'visible chest/helmet pixels cross projected ground'
  assert (world[0]*.8-50).min()>=0 and (world[0]*.8-50).max()<=600
  assert (world[1]*.8-10).min()>=65 and (world[1]*.8-10).max()<=615
subprocess.run(['git','diff','--exit-code',meta['baselineCommit'],'--','docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-parts','docs/routes/jigoku-2d/free-arm-support','docs/routes/jigoku-2d/free-arm-transition','src','public'],cwd=ROOT,check=True,stdout=subprocess.PIPE)
report=dict(passed=True,samples=len(result['rows']),torsoCapMaximumY=maximum,torsoCapXRange=[left,right],nearHandSha256=meta['nearHand']['sha256'],newTextureBytes=0,checks=['Existing open hand unchanged','1001 actual torso/cap transforms: visible alpha > 16 pixels stay above Y=690 and inside review panel','Parameters match runtime export; previous prototypes and game unchanged'],limits='Checks torso/cap projected pixels, not full-character collisions, anatomy or weight transfer. Existing waist overlap and hand-image switch remain visible limitations.')
(OUT/'yield-art-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
