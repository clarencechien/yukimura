"""Package rigid cutouts; no anatomical warp. Clean torso is image_gen-authored.
The original guard-lower legs, arms and gloves are retained as image cutouts.
"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';SRC=ROOT/'assets/source/jigoku-2d/thrust-rig'
original=Image.open(OUT/'guard-body-hd.webp').convert('RGBA').crop((1024,640,2048,1280))
clean=Image.open(SRC/'body-clean.png').convert('RGBA')
# Corresponding sole marks register the clean plate by one uniform scale only.
scale=398/(1045-346);offset=(round(228-346*scale),round(537-(890+845)/2*scale))
registered=Image.new('RGBA',(1024,640));registered.alpha_composite(clean.resize((round(clean.width*scale),round(clean.height*scale)),Image.Resampling.LANCZOS),offset)
polygons={
 'lower':[(0,330),(1024,330),(1024,640),(0,640)],
 'torso':[(0,0),(1024,0),(1024,350),(0,350)],
 'rearUpper':[(283,253),(344,237),(354,273),(323,298),(288,308),(270,288)],
 'rearFore':[(281,269),(315,276),(347,293),(347,324),(317,323),(286,308),(273,292)],
 'rearHand':[(342,289),(356,287),(371,304),(374,324),(360,339),(336,332),(329,314)],
 'frontUpper':[(502,260),(536,270),(551,286),(554,306),(532,318),(506,308),(488,286)],
 'frontFore':[(534,280),(568,262),(585,258),(599,278),(580,302),(549,316),(533,307)],
 'frontHand':[(580,250),(596,239),(610,247),(620,262),(609,279),(588,289),(576,276)]}
joints={'rear':{'shoulder':[325,255],'elbow':[295,288],'wrist':[343,309],'grip':[359,313],'bend':1},'front':{'shoulder':[505,268],'elbow':[544,300],'wrist':[582,276],'grip':[594,267],'bend':1}}
pivots={'lower':[0,0],'torso':[430,342]}
for side,j in joints.items():
 for part,joint in [('Upper','shoulder'),('Fore','elbow'),('Hand','wrist')]:pivots[side+part]=j[joint]
layers={};bytes_by_size={'hd':0,'mobile':0}
for name,poly in polygons.items():
 source=registered if name=='torso' else original
 mask=Image.new('L',source.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
 # Antialias cut boundaries; the lower body keeps original alpha exactly.
 if name not in ['lower','torso']:mask=mask.filter(ImageFilter.GaussianBlur(.35))
 rgba=np.array(source);rgba[:,:,3]=(rgba[:,:,3].astype(float)*np.array(mask)/255).round().astype('uint8')
 im=Image.fromarray(rgba);box=im.getchannel('A').getbbox();assert box
 cell=im.crop(box);layers[name]={'box':box,'pivot':pivots[name],'size':cell.size,'polygon':poly,'source':'clean-registered' if name=='torso' else 'guard-lower'}
 for suffix,ratio,key in [('-hd',1,'hd'),('',.5,'mobile')]:
  size=(max(1,round(cell.width*ratio)),max(1,round(cell.height*ratio)));copy=cell.resize(size,Image.Resampling.LANCZOS)
  copy.save(OUT/f'hero-{name}{suffix}.webp',lossless=True,method=6);bytes_by_size[key]+=size[0]*size[1]*4
# Exact copies of the two old sweep boundary cells, not the old 72-frame atlases.
boundary=[]
for suffix,w,h,cols in [('-hd',1024,640,4),('',512,320,6)]:
 atlas=Image.new('RGBA',(w*2,h))
 for i,(clip,index) in enumerate([('thrust',35),('idle',0)]):
  page='-2' if suffix and index>=24 else '';local=index%24 if suffix else index
  src=ROOT/f'docs/routes/jigoku-2d/yari-rigid/{clip}-warm-left{suffix}{page}.webp'
  image=Image.open(src).convert('RGBA');box=(local%cols*w,local//cols*h,(local%cols+1)*w,(local//cols+1)*h)
  crop=image.crop(box);atlas.paste(crop,(i*w,0));boundary.append({'resolution':suffix or 'mobile','source':str(src.relative_to(ROOT)),'frame':index,'box':box})
 atlas.save(OUT/f'sweep-boundary{suffix}.webp',lossless=True,method=6);bytes_by_size['hd' if suffix else 'mobile']+=atlas.width*atlas.height*4
meta={'referenceCommit':'37e0c1293bd9b97d3a5fc76719f94498139635cb','joints':joints,'hip':[430,342],'layers':layers,'registration':{'sourceSoles':[[346,890],[1045,845]],'uniformScale':scale,'offset':offset},'legacyBoundaryCells':boundary,'rgba8Bytes':bytes_by_size,'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':status} for p,status in [(SRC/'first-study.png','Rejected: open hands and varying grip spacing'),(SRC/'bodies-study.png','Rejected for runtime: different body heights and stance spans'),(SRC/'body-clean.png','Runtime clean torso; original guard-lower limbs and lower body retained')]],'generatedFiles':['exec-0c29c43a-f162-4c49-8b38-d3a2178e53d1.png','exec-efeee8ff-aa83-43cb-a485-cd32afbe92bc.png','exec-6690fe86-90e5-4610-a012-2579997d0d75.png'],'method':'Three image_gen calls including two rejected multi-pose studies. Runtime uses one clean torso plus original lower-body/arm/hand cutouts and the existing spear. Fixed-length projected two-link arm IK; rigid torso turn about waist, feet never transformed. No new Blender/Modal render. Not anatomical 3D or force simulation.'}
(OUT/'thrust-rig.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Packaged shared thrust rig:',bytes_by_size)
