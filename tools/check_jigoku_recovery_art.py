"""Verify unchanged low-hit cells and compare manually authored recovery landmarks."""
from pathlib import Path
import io,json,math,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';BASE='21d8b539b1a2abc9c38d2f0b8c0fdaf104cdf0aa'
old=lambda name:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
checks=[]
for suffix,w,h in [('-hd',1152,768),('',768,512)]:
 before=Image.open(io.BytesIO(old(f'enemy-low{suffix}.webp'))).convert('RGBA')
 after=Image.open(OUT/f'enemy-low{suffix}.webp').convert('RGBA')
 assert after.size==(w*2,h*2) and max(after.size)<=4096
 for i in range(2):
  a=np.array(before.crop((i*w,0,(i+1)*w,h)));b=np.array(after.crop((i*w,0,(i+1)*w,h)))
  assert np.array_equal(a[:,:,3],b[:,:,3]);mask=(a[:,:,3]>0)|(b[:,:,3]>0)
  assert np.array_equal(a[mask],b[mask]),'Existing hit pose changed'
  checks.append({'resolution':suffix or 'mobile','pose':12+i,'visiblePixelMismatch':0,'alphaMismatch':0})
rig=json.loads((OUT/'enemy-rig.json').read_text());prior=json.loads(old('enemy-rig.json'));assert rig['bindings'][:14]==prior['bindings']
assert rig['parts']==prior['parts'] and rig['armLengths']==prior['armLengths']
paths={'previous':[13,12,0],'current':[13,14,15,0]}
guardFeet=[[370,688],[750,675]] # Manual sole-center estimates; not a runtime constraint.
report={'passed':True,'baselineCommit':BASE,'preservedCells':checks,'paths':{},'guardSoleMarkersHD':guardFeet,'scope':'Manually registered shoulder and sole-center projections, world scale 0.6. Not pixel tracking, anatomical validation, no-slip feet or continuous torso animation. Original 14 bindings and shared component metadata unchanged.'}
for name,path in paths.items():
 shoulders=[rig['bindings'][i]['shoulder'] for i in path]
 feet=[rig['bindings'][i].get('footContacts',guardFeet) for i in path]
 report['paths'][name]={'poses':path,'shoulderStepsWorld':[math.dist(a,b)*.6 for a,b in zip(shoulders,shoulders[1:])],'soleStepsWorld':[[math.dist(a,b)*.6 for a,b in zip(x,y)] for x,y in zip(feet,feet[1:])]}
a=report['paths']['previous'];b=report['paths']['current']
assert max(b['shoulderStepsWorld'])<max(a['shoulderStepsWorld'])
assert max(map(max,b['soleStepsWorld']))<max(map(max,a['soleStepsWorld']))
(OUT/'recovery-art-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('4 existing-cell pixel checks passed; old bindings/parts unchanged.')
print('Manual maximum shoulder step:',round(max(a['shoulderStepsWorld']),2),'->',round(max(b['shoulderStepsWorld']),2),'px')
print('Manual maximum sole step:',round(max(map(max,a['soleStepsWorld'])),2),'->',round(max(map(max,b['soleStepsWorld'])),2),'px')
