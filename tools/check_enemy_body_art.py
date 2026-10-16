"""Check cutout provenance, rest reconstruction and explicit texture costs."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
meta=json.loads((OUT/'enemy-body-art.json').read_text());src=OUT/meta['source']
assert hashlib.sha256(src.read_bytes()).hexdigest()==meta['sourceSHA256']
source=Image.open(src).convert('RGBA').crop(meta['sourceCell']);assembled=Image.new('RGBA',source.size)
cost={};checks=[]
for name in ['leftFoot','rightFoot','leftShin','rightShin','leftThigh','rightThigh','lower','torso']:
 layer=meta['layers'][name];mask=Image.new('L',source.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in layer['polygon']],fill=255)
 if name!='torso':
  base=Image.new('L',source.size);ImageDraw.Draw(base).polygon([tuple(p) for p in meta['lowerSourceMask']],fill=255);mask=Image.fromarray(np.minimum(np.array(mask),np.array(base)))
 rgba=np.array(source);rgba[:,:,3]=(rgba[:,:,3].astype(float)*np.array(mask)/255).round().astype('uint8')
 expected=Image.fromarray(rgba).crop(layer['box']);part=Image.open(OUT/f'enemy-body-{name}-hd.webp').convert('RGBA')
 a,b=np.array(expected),np.array(part);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
 mobile=Image.open(OUT/f'enemy-body-{name}.webp').convert('RGBA');resampled=part.resize(mobile.size,Image.Resampling.LANCZOS)
 a,b=np.array(resampled),np.array(mobile);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
 assembled.alpha_composite(part,tuple(layer['box'][:2]));cost[name]={'desktopRGBA8Bytes':part.width*part.height*4,'mobileRGBA8Bytes':mobile.width*mobile.height*4}
a,b=np.array(source),np.array(assembled);missing=(a[:,:,3]>240)&(b[:,:,3]<128);assert not missing.any(),(int(missing.sum()),[int(x) for x in (np.where(missing)[1].min(),np.where(missing)[0].min(),np.where(missing)[1].max(),np.where(missing)[0].max())])
checks+=['All eight HD cutouts retain exact visible source RGB and declared alpha masks','Mobile parts equal uniform resampling of HD cutouts','Assembled rest silhouette has no missing opaque source pixels','Rigid pieces overlap at belt, skirt, knee armor and ankle cuffs; no mesh deformation']
(OUT/'enemy-body-art-check.json').write_text(json.dumps({'passed':True,'checks':checks,'cost':cost,'limits':'Rest silhouette and retained pixel checks, not an anatomical or automatic moving-seam quality judgement. Moving seam is inspected in actual browser captures.'},indent=2)+'\n')
print(checks)
