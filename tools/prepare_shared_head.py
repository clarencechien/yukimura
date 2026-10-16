"""Cut a reusable helmet/face and masked torso variants; preserve source RGB."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
settle=json.loads((OUT/'settle.json').read_text());bridge=json.loads((OUT/'bridge.json').read_text())
headPoly=[[330,330],[430,330],[455,365],[456,375],[503,396],[500,428],[475,455],[455,498],[375,500],[330,455]]
def split(name,part,polygon,extract=False):
 source=OUT/part['url'];raw=Image.open(source).convert('RGBA');mask=Image.new('L',raw.size);ImageDraw.Draw(mask).polygon([(x-part['box'][0],y-part['box'][1]) for x,y in polygon],fill=255)
 # Two source-pixel overlap at the internal neck cut prevents a filtering crack.
 removal=mask.filter(ImageFilter.MinFilter(5));a=np.array(raw);a[:,:,3]=np.minimum(a[:,:,3],255-np.array(removal));url=f'headless-{name}.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
 result=dict(url=url,box=part['box'],source=part['url'],sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),polygon=polygon,overlapPixels=2)
 if extract:
  a=np.array(raw);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));piece=Image.fromarray(a);box=piece.getbbox();piece.crop(box).save(OUT/'shared-head.webp',lossless=True,method=6)
  result['head']=dict(url='shared-head.webp',box=[box[0]+part['box'][0],box[1]+part['box'][1],box[2]+part['box'][0],box[3]+part['box'][1]],pivot=[470,430],polygon=polygon)
 return result
unload=split('unload',settle['parts']['torso'],headPoly,True);head=unload.pop('head');parts={'unload':unload}
# Polygons are in each full source sheet; they remove the painted head only.
polys={
 'bridge':[[0,300],[175,300],[215,385],[240,460],[190,570],[0,580]],
 'roll':[[0,260],[165,260],[215,340],[230,430],[180,540],[0,550]],
 'side':[[675,300],[845,300],[900,375],[915,455],[855,550],[675,570]],
 'rest':[[1408,320],[1588,320],[1648,400],[1663,475],[1598,570],[1408,590]]}
for f in bridge['frames']:
 r=f['registration'];poly=[[r['offset'][0]+(x-r['box'][0])*r['scale'],r['offset'][1]+y*r['scale']] for x,y in polys[f['id']]]
 parts[f['id']]=split(f['id'],f['parts']['torso'],poly)
meta=dict(baselineCommit='02c57d00ef3bdb94fe4f0fb2e6865f98beb7ae96',start=1180,end=1500,groundY=690,head=head,torsos=parts,keys=[dict(time=1220,point=[445,570],angle=-40),dict(time=1260,point=[459,576],angle=-30),dict(time=1380,point=[449.5,585],angle=-24),dict(time=1500,point=[441.9,590],angle=-20)],method='One existing helmet/face sprite, rigid rotation and translation only. Source RGB unchanged. Separate headless torso cutouts with two-pixel neck overlap. Hand-authored projected neck path; not anatomical or physical validation.')
(OUT/'shared-head.json').write_text(json.dumps(meta,indent=2)+'\n');print('Prepared shared helmet/face and five masked torso variants.')
