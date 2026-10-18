"""Validate candidate registration and prove that production combat was not edited."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm'
meta=json.loads((OUT/'provenance.json').read_text());entry=meta['candidate'];source=ROOT/entry['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256']
im=Image.open(source).convert('RGBA');s=entry['uniformScale'];small=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);expected=Image.new('RGBA',(1152,768));expected.alpha_composite(small,tuple(entry['offset']));actual=Image.open(OUT/'candidate.webp').convert('RGBA')
a,b=np.array(expected),np.array(actual);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
report=json.loads((OUT/'reach-report.json').read_text());project=lambda p:[p[i]*s+entry['offset'][i] for i in range(2)]
for key,sourcekey in [('shoulder','sourceNearShoulder'),('elbow','sourceElbow'),('wrist','sourceWrist')]:assert report['marks']['candidate'][key]==project(entry[sourcekey])
subprocess.run(['git','diff','--exit-code',meta['baselineCommit'],'--','docs/routes/jigoku-2d/combat','src','public'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--','docs/routes/jigoku-2d/combat','src','public'],cwd=ROOT).strip()
(OUT/'art-check.json').write_text(json.dumps({'passed':True,'checks':['Candidate original SHA matches; WebP is only uniform rescale/translation of generated PNG','Candidate joint marks map to registered frame coordinates','Production combat, src and public unchanged from baseline, including no untracked runtime assets'],'baselineCommit':meta['baselineCommit'],'limits':'Registration/source preservation only. Manual landmarks and reach limits are planning assumptions, not proof of anatomy.'},indent=2)+'\n');print('Candidate registration and production isolation checks passed.')
