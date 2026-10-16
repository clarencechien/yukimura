"""Mechanical crop/register only; preserve generated candidate and production art."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm';OUT.mkdir(exist_ok=True)
source=ROOT/'assets/source/jigoku-2d/ghost-rig/kneel-reach-candidate.png'
im=Image.open(source).convert('RGBA');small=im.resize((1152,768),Image.Resampling.LANCZOS)
# Move only horizontally to align the visible support fingertips, no warp.
frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,(-12,0))
mass=lambda x:sum(a*n for a,n in enumerate(x.getchannel('A').histogram()))
assert mass(frame)==mass(small)
frame.save(OUT/'candidate.webp',lossless=True,method=6)
meta={'baselineCommit':'494bdc135e901e01831c0baccbfbf6da3791d2bd','candidate':{'path':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'generatedFile':'exec-7e083747-c160-473d-929f-53cc4d476368.png','uniformScale':.75,'offset':[-12,0],'sourceNearShoulder':[710,635],'sourceElbow':[708,765],'sourceWrist':[653,875]},'references':{'atlas':'docs/routes/jigoku-2d/combat/ghost-warrior-hd.webp','frames':[5,4]},'landmarks':'Manual projected estimates inside armor; not motion capture, 3D joint centers or a biomechanical measurement. Approximate marking uncertainty +/-8 source-frame pixels per endpoint.','method':'One image_gen kneel repair aimed at lowering shoulder and shortening near arm. Candidate remains outside the proposed fixed-arm reach and is not installed into the game. Review only: uniform resize and translation, no stretching. Green skeleton is a shoulder-lowering authoring target, not a repainted or animated body.','runtimeChanged':False}
(OUT/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Prepared independent reach candidate; no combat asset changed.')
