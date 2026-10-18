"""Register a local generated waist study, keeping the original silhouette and all exterior pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
base=json.loads((OUT/'shared-rear-leg.json').read_text())['lowers']['bridge'];source=ROOT/'assets/source/jigoku-2d/ghost-rig/waist-transition-upright.png'
original=Image.open(OUT/base['url']).convert('RGBA');raw=Image.open(source).convert('RGBA');scale=original.width/raw.width
small=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS);registered=Image.new('RGBA',original.size);registered.alpha_composite(small)
# Interior-only artwork replacement. Preserve the existing knee outline, ground
# cloth, torso seam and alpha; no RGB replacement on faint generated cut edges.
polygon=[[565,532],[626,530],[666,558],[679,604],[626,633],[568,624],[541,580]]
mask=Image.new('L',original.size);ImageDraw.Draw(mask).polygon([(x-base['box'][0],y-base['box'][1]) for x,y in polygon],fill=255)
a=np.array(original);b=np.array(registered);region=(np.array(mask)>0)&(a[:,:,3]>=250)&(b[:,:,3]>=250);a[region,:3]=b[region,:3]
url='waist-transition-bridge.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
m=dict(baselineCommit='2bf6c569fe5a7dafa91af9ac37a1fc4550d1efe1',source=str(source.relative_to(ROOT)),sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),generatedFile='exec-8bd538a8-c204-487a-a0df-d6421c07e8dd.png',registration=dict(scale=scale,offset=base['box'][:2],sourceSize=list(raw.size),resizedSize=list(small.size)),part=dict(url=url,box=base['box'],original=base['url'],originalSHA256=hashlib.sha256((OUT/base['url']).read_bytes()).hexdigest()),polygon=polygon,alphaThreshold=250,replacedPixels=int(region.sum()),method='Uniformly registered imagegen waist study; replace opaque interior RGB only in the bridge lower-body image. Keep original alpha, exterior pixels, source images and all existing rig transforms. Hard image key, no image fade or morph.')
world=Image.new('RGBA',(1152,768));world.alpha_composite(small,tuple(base['box'][:2]));parts={}
for label,metadata in [('headless','shared-head.json'),('shoulderless','shared-shoulder.json')]:
 old=json.loads((OUT/metadata).read_text())['torsos']['bridge'];im=Image.open(OUT/old['url']).convert('RGBA');a=np.array(im);b=np.array(world.crop(old['box']));mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([(x-old['box'][0],y-old['box'][1]) for x,y in polygon],fill=255);region=(np.array(mask)>0)&(a[:,:,3]>=250)&(b[:,:,3]>=250);a[region,:3]=b[region,:3];url=f'waist-transition-{label}.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
 parts[label]=dict(url=url,box=old['box'],original=old['url'],originalSHA256=hashlib.sha256((OUT/old['url']).read_bytes()).hexdigest(),replacedPixels=int(region.sum()))
m['torsos']=parts
m['adopted']=False
m['query']='hip=paint'
m['references']=[dict(path=str((OUT/name).relative_to(ROOT)),sha256=hashlib.sha256((OUT/name).read_bytes()).hexdigest()) for name in ['legless-bridge.webp','waist.webp']]
m['earlierStudy']=dict(path='assets/source/jigoku-2d/ghost-rig/waist-transition-study.png',sha256=hashlib.sha256((ROOT/'assets/source/jigoku-2d/ghost-rig/waist-transition-study.png').read_bytes()).hexdigest(),generatedFile='exec-f95b20de-3367-4f4c-9128-e2654bcf0e3f.png',note='Earlier diagonal design retained as source reference only; not used by the runtime candidate.')
m['method']='Uniformly registered imagegen waist study; replace opaque interior RGB in bridge lower body and its two overlapping torso variants. Preserve original alpha and visible exterior pixels, source images and rig transforms. Hard image key, no fade or morph. Opt-in only.'
(OUT/'waist-transition.json').write_text(json.dumps(m,indent=2)+'\n');print(m['replacedPixels'])
