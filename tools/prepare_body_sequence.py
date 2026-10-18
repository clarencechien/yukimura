"""Register a three-pose sheet with one scale and fixed correspondence anchors."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,math
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parents[1];O=R/'docs/routes/jigoku-2d/free-arm-settle';source=R/'assets/source/jigoku-2d/ghost-rig/body-sequence.png'
im=Image.open(source).convert('RGBA');raw=np.array(im);raw[raw[:,:,3]<=16]=0;im=Image.fromarray(raw);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scale=.46;angle=10;r=math.radians(angle);c,s=math.cos(r),math.sin(r)
frames=[]
for name,cell,anchor,target,time in [('bridge',[0,0,693,724],[180,350],[494,541],1220),('roll',[693,0,1385,724],[870,342],[494,541],1260),('side',[1385,0,2172,724],[1550,402],[469.1,560],1380)]:
 x,y=anchor;u,v=target;inverse=[c/scale,s/scale,x-cell[0]-(c*u+s*v)/scale,-s/scale,c/scale,y-cell[1]-(-s*u+c*v)/scale]
 world=im.crop(cell).transform((1152,768),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC);a=np.array(world);a[a[:,:,3]<=16]=0;world=Image.fromarray(a);box=world.getbbox();url=f'sequence-{name}.webp';world.crop(box).save(O/url,lossless=True,method=6)
 ys,xs=np.nonzero(a[:,:,3]>0);cells=np.concatenate([np.column_stack([xs+dx,ys+dy]) for dx,dy in [(0,0),(1,0),(1,1),(0,1)]]);hull=cells[ConvexHull(cells).vertices].tolist()
 frames.append(dict(pivot=target,supportHull=hull,id=name,time=time,part=dict(url=url,box=list(box)),registration=dict(cell=cell,sourceShoulder=anchor,targetShoulder=target,inverseAffine=inverse)))
m=dict(adopted=False,query='body=sequence',baselineCommit='14d9e7bf5280d1bece37b601b24ef98361ba6850',source=str(source.relative_to(R)),sourceSHA256=sha(source),sourceSize=list(im.size),generatedFile='exec-443e12af-0e96-4fe3-a9fb-c729b95a17d4.png',references=[dict(path=p,sha256=sha(R/p)) for p in ['assets/source/jigoku-2d/ghost-rig/body-transition-folded.png','assets/source/jigoku-2d/ghost-rig/side-fall-breakdowns.png']],scale=scale,angle=angle,groundY=687,rotationLimit=12,alphaCutoff=16,interval=dict(after=1200,through=1440),frames=frames,method='Three body poses generated together; shared uniform scale and rigid rotation, individual shoulder anchors. Replace bridge/roll/side chest and lower body as one sprite each. Runtime rotates each rigid body around its shoulder while its actual alpha cell hull stays on y=687. Head, arms, cap, calf and sword use the original rig. No mesh warp, morph, image fade or interpolated drawings.')
m['textureRGBA8MiB']=sum((f['part']['box'][2]-f['part']['box'][0])*(f['part']['box'][3]-f['part']['box'][1])*4/1048576 for f in frames)
(O/'body-sequence.json').write_text(json.dumps(m,indent=2)+'\n');print([(f['id'],f['part']['box']) for f in frames])
