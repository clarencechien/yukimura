from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-parts';m=json.loads((OUT/'parts.json').read_text())
def same(a,b):
 a,b=np.array(a),np.array(b);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
for entry in [m['armSource'],{'path':m['body']['source'],'sha256':m['body']['sha256']}]:assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
im=Image.open(ROOT/m['armSource']['path']).convert('RGBA')
for name,p in m['parts'].items():
 expected=im.crop(p['box']).resize(tuple(p['size']),Image.Resampling.LANCZOS);same(expected,Image.open(OUT/f'{name}.webp').convert('RGBA'))
 assert p['displaySize']==[(p['box'][i+2]-p['box'][i])*p['scale'] for i in range(2)]
 if p['end']:assert abs(np.linalg.norm(np.array(p['end'])-p['pivot'])-{'upper':85,'fore':90}[name])<1e-6
b=m['body'];raw=Image.open(ROOT/b['source']).convert('RGBA');frame=Image.new('RGBA',(1152,768));frame.alpha_composite(raw.resize((round(raw.width*b['scale']),round(raw.height*b['scale'])),Image.Resampling.LANCZOS),tuple(b['offset']));same(frame,Image.open(OUT/'body.webp').convert('RGBA'))
c=m['cap'];cap=frame.crop(c['box']);mask=Image.new('L',cap.size);ImageDraw.Draw(mask).polygon([(x-c['box'][0],y-c['box'][1]) for x,y in c['polygon']],fill=255);a=np.array(cap);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));same(Image.fromarray(a),Image.open(OUT/'cap.webp').convert('RGBA'))
assert b['shoulder']==[b['offset'][i]+b['scale']*b['shoulderSource'][i] for i in range(2)]
subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--','docs/routes/jigoku-2d/combat','src','public'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','docs/routes/jigoku-2d/combat','src','public'],cwd=ROOT).strip()
report={'passed':True,'checks':['Four reused pieces retain visible source colors and alpha after declared uniform crop/resampling','Upper/fore endpoints match fixed 85/90 px attachment lengths','Generated body is registered uniformly; shoulder cap is an exact masked source crop','Production combat/src/public unchanged from baseline'],'baselineCommit':m['baselineCommit'],'reviewRGBA8MiB':m['reviewRGBA8Bytes']/1048576,'limits':'Pixel source and registration checks, not proof of anatomy, perfect visual seams or hardware memory usage.'}
(OUT/'art-check.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
