"""Prepare cloth-backed original torsos for an earlier rigid shoulder-plate drop."""
from pathlib import Path
from PIL import Image
import json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
read=lambda name:json.loads((OUT/name).read_text())
settle=read('settle.json');head=read('shared-head.json');shared=read('shared-shoulder.json');cap=settle['parts']['cap'];lining=shared['lining'];tile=np.array(Image.open(OUT/lining['source']).crop(lining['box']).convert('RGBA'))
parts={}
donor=shared['torsos']['bridge'];donorImage=Image.open(OUT/donor['url']).convert('RGBA');angle=math.radians(-49.329225410141966);c,s=math.cos(angle),math.sin(angle)
# Register the bridge collar to the original chest in the final unload orientation.
# This is a rigid texture-space rotation; output alpha remains the original torso.

for name,p in [('headed',settle['parts']['torso']),('headless',head['torsos']['unload'])]:
 raw=Image.open(OUT/p['url']).convert('RGBA');a=np.array(raw);mask=Image.new('L',raw.size);mask.paste(Image.open(OUT/cap['url']).getchannel('A'),(cap['box'][0]-p['box'][0],cap['box'][1]-p['box'][1]))
 region=np.array(mask)>=250;yy,xx=np.indices(region.shape);cloth=tile[yy%tile.shape[0],xx%tile.shape[1],:3];a[region,:3]=cloth[region]
 dx,dy=p['box'][0]-settle['shoulder'][0],p['box'][1]-settle['shoulder'][1]
 transform=(c,-s,c*dx-s*dy+494-donor['box'][0],s,c,s*dx+c*dy+541-donor['box'][1])
 projected=np.array(donorImage.transform(raw.size,Image.Transform.AFFINE,transform,resample=Image.Resampling.BICUBIC))
 alpha=projected[:,:,3:]/255;backing=np.rint(projected[:,:,:3]*alpha+cloth*(1-alpha)).astype(np.uint8)
 a[region,:3]=backing[region]
 url=f'entry-{name}.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
 parts[name]=dict(url=url,box=p['box'],source=p['url'],sourceSHA256=hashlib.sha256((OUT/p['url']).read_bytes()).hexdigest(),maskAlphaThreshold=250)
m=dict(baselineCommit='dbb559d49f57f1836b181cc1f4545c325fb38dae',start=1000,end=1200,cap={**cap,'pivot':settle['shoulder']},target=dict(angle=-24.65,offset=[-18.55,43.64]),lining=lining,collar=dict(source=donor['url'],sourceSHA256=hashlib.sha256((OUT/donor['url']).read_bytes()).hexdigest(),box=donor['box'],shoulder=[494,541],referenceTorsoAngle=-49.329225410141966),torsos=parts,method='Drop the original rigid cap after palm lift; start in its exact torso transform and approach the first side-fall plate before body handoff. Target fitted by gold-edge registration against fall-bridge-cap.webp, reviewed visually. No scale, morph, or crossfade; torso alpha retained with a rigidly registered existing bridge collar and quilted lining fallback restricted to the vacated plate footprint.')
(OUT/'shoulder-entry.json').write_text(json.dumps(m,indent=2)+'\n');print('Prepared two cloth-backed entry torsos; original cap reused.')
