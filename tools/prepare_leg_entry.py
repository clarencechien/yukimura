"""Release the original tucked calf before handing off to the common side-fall leg."""
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.spatial import ConvexHull
import numpy as np,json,hashlib,math
OUT=Path(__file__).resolve().parents[1]/'docs/routes/jigoku-2d/free-arm-settle'
settle=json.loads((OUT/'settle.json').read_text());seam=[[669,586],[684,616],[687,644],[680,655],[700,665],[725,670]];cropY=[586,670]
parts={}
waist=settle['parts']['waist'];waistImage=Image.open(OUT/waist['url']).convert('RGBA')
def preserve(size,box):
 mask=Image.new('L',size);mask.paste(waistImage.getchannel('A'),(waist['box'][0]-box[0],waist['box'][1]-box[1]));return np.array(mask)>16
def region(size,box,overlap=0):
 pts=[[x-box[0]-overlap,y-box[1]] for x,y in seam];poly=[*pts,[size[0]+100,pts[-1][1]],[size[0]+100,pts[0][1]]]
 mask=Image.new('L',size);ImageDraw.Draw(mask).polygon(poly,fill=255);return (np.array(mask)>0)&~preserve(size,box)
for name in ['lower']:
 p=settle['parts'][name];im=Image.open(OUT/p['url']).convert('RGBA');a=np.array(im);a[region(im.size,p['box']),3]=0;url=f'leg-entry-{name}.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
 parts[name]=dict(url=url,box=p['box'],source=p['url'],sourceSHA256=hashlib.sha256((OUT/p['url']).read_bytes()).hexdigest())
 if name=='lower':
  a=np.array(im);a[~region(im.size,p['box'],12),3]=0;a[a[:,:,3]<=16,3]=0;piece=Image.fromarray(a);box=piece.getbbox();piece=piece.crop(box);piece.save(OUT/'entry-calf.webp',lossless=True,method=6)
  box=[box[0]+p['box'][0],box[1]+p['box'][1],box[2]+p['box'][0],box[3]+p['box'][1]];pivot=[680,635];yy,xx=np.where(np.array(piece)[:,:,3]>16);points=np.concatenate([np.column_stack([xx+dx+box[0]-pivot[0],yy+dy+box[1]-pivot[1]]) for dx,dy in [(0,0),(1,0),(0,1),(1,1)]])
  hull=points[ConvexHull(points).vertices].tolist();angle=15;r=math.radians(angle);support=max(x*math.sin(r)+y*math.cos(r) for x,y in hull)
  calf=dict(url='entry-calf.webp',box=box,pivot=pivot,source=p['url'],sourceSHA256=parts[name]['sourceSHA256'],overlapPixels=12,alphaCutoff=16,hull=hull)
m=dict(baselineCommit='366ca9458d3db36c4ac2127540aea68565501572',start=1000,end=1200,groundY=690,target=dict(angle=angle,offset=[-8,681-support-pivot[1]]),parts=parts,calf=calf,preservedWaist=dict(source=waist['url'],box=waist['box'],alphaThreshold=16,sourceSHA256=hashlib.sha256((OUT/waist['url']).read_bytes()).hexdigest()),seam=seam,cropY=cropY,method='Original tucked calf and boot turn together before the first side-fall cut; 12 px thigh overlap, no resizing, repainting or blending. Authored 2D motion, not knee or ankle biomechanics.')
(OUT/'leg-entry.json').write_text(json.dumps(m,indent=2)+'\n')
