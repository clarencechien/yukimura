"""Register one complete painted torso/pelvis/knee, without deforming its anatomy."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';SRC=ROOT/'assets/source/jigoku-2d/ghost-rig'
source=SRC/'body-transition-folded.png';raw=Image.open(source).convert('RGBA');a=np.array(raw);a[a[:,:,3]<=16]=0;raw=Image.fromarray(a)
scale=.26;angle=-3;anchor=[520,390];target=[494,541];r=math.radians(angle);co=math.cos(r);si=math.sin(r)
# Inverse of one uniform scale + rigid rotation + anchor placement.
affine=[co/scale,si/scale,anchor[0]-(co*target[0]+si*target[1])/scale,-si/scale,co/scale,anchor[1]-(-si*target[0]+co*target[1])/scale]
world=raw.transform((1152,768),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC);a=np.array(world);a[a[:,:,3]<=16]=0;world=Image.fromarray(a);box=world.getbbox();part=world.crop(box);part.save(OUT/'body-transition.webp',lossless=True,method=6)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=dict(adopted=False,query='body=paint',baselineCommit='e2ae328281df070e0e6cc58fa59b9dd48a8ab61a',source=str(source.relative_to(ROOT)),sourceSHA256=sha(source),generatedFile='exec-89c595a1-b373-4f06-bad0-93b8a21a1051.png',sourceSize=list(raw.size),alphaCutoff=16,part=dict(url='body-transition.webp',box=list(box)),registration=dict(scale=scale,angle=angle,sourceShoulder=anchor,targetShoulder=target,inverseAffine=affine),interval=dict(after=1200,through=1240),references=[dict(path=str((SRC/f'body-transition-reference-{name}.png').relative_to(ROOT)),sha256=sha(SRC/f'body-transition-reference-{name}.png'),age=t) for name,t in [('before',1199.999),('after',1240.001)]],referenceCapture=dict(sourceCanvasRect=[850,350,300,200],outputSize=[600,400],includedBodyLayers=['torso','lower','waist','restore']),method='One generated chest/pelvis/thigh/knee assembly. Uniform scale and rigid rotation, no body morph or crossfade. Replace bridge torso AND lower body with one transparent sprite; retain shared head, arms, cap, rear calf and sword. Manual projected shoulder registration, not anatomical validation.',textureRGBA8MiB=part.width*part.height*4/1048576)
m['earlierStudy']=dict(path=str((SRC/'body-transition-study.png').relative_to(ROOT)),sha256=sha(SRC/'body-transition-study.png'),generatedFile='exec-3ba8f6fe-2092-4a3a-bc29-bbb85bbab158.png',reason='Raised neck collar protruded above the shared helmet; not used at runtime.')
m['revisionReferences']=[m['earlierStudy'],dict(path=str((OUT/'handoffs/body-baseline/1200-after.png').relative_to(ROOT)),sha256=sha(OUT/'handoffs/body-baseline/1200-after.png'),note='Existing assembled pose used to show that the shared helmet lies lower-left of the chest.')]
(OUT/'body-transition.json').write_text(json.dumps(m,indent=2)+'\n');print(box,m['textureRGBA8MiB'])
