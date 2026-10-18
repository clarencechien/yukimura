"""Split existing lower drawings; reuse rest shin/boot without repaint or scaling."""
from pathlib import Path
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull
import numpy as np
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle'
fall=json.loads((OUT/'bridge.json').read_text())
seams={
 'bridge':[[654,580],[674,603],[682,625],[681,649],[665,668],[645,685]],
 'roll':[[653,585],[671,610],[676,636],[670,658],[651,676]],
 'side':[[646,583],[664,605],[670,629],[667,650],[650,669],[630,681]],
 'rest':[[645,580],[659,601],[669,622],[668,646],[658,663],[638,680]],
}
lowers={}
def mask(size,box,seam,overlap=0):
 points=[[x-box[0]-overlap,y-box[1]] for x,y in seam]
 polygon=[[points[0][0],-100],*points,[points[-1][0],size[1]+100],[size[0]+100,size[1]+100],[size[0]+100,-100]]
 m=Image.new('L',size);ImageDraw.Draw(m).polygon(polygon,fill=255);return np.array(m)>0
for frame in fall['frames']:
 name=frame['id'];p=frame['parts']['lower'];a=np.array(Image.open(OUT/p['url']).convert('RGBA'))
 original=a.copy();region=mask(a.shape[1::-1],p['box'],seams[name]);yy,_=np.indices(region.shape)
 if name=='rest':region &= (yy+p['box'][1]>=595)&(yy+p['box'][1]<681)
 a[region,3]=0
 url=f'legless-{name}.webp';Image.fromarray(a).save(OUT/url,lossless=True,method=6)
 lowers[name]=dict(url=url,box=p['box'],source=p['url'],sourceSHA256=hashlib.sha256((OUT/p['url']).read_bytes()).hexdigest(),seam=seams[name])
 if name=='rest':
  lowers[name]['cropY']=[595,681]
  a=original.copy();region=mask(a.shape[1::-1],p['box'],seams[name],12);yy,_=np.indices(region.shape);region &= (yy+p['box'][1]>=595)&(yy+p['box'][1]<681)
  a[~region,3]=0;a[a[:,:,3]<=16,3]=0
  im=Image.fromarray(a);bbox=im.getbbox();im=im.crop(bbox);im.save(OUT/'shared-rear-leg.webp',lossless=True,method=6)
  box=[bbox[0]+p['box'][0],bbox[1]+p['box'][1],bbox[2]+p['box'][0],bbox[3]+p['box'][1]];pivot=[660,630]
  yy,xx=np.where(np.array(im)[:,:,3]>16);points=np.concatenate([np.column_stack([xx+dx+box[0]-pivot[0],yy+dy+box[1]-pivot[1]]) for dx,dy in [(0,0),(1,0),(0,1),(1,1)]])
  hull=points[ConvexHull(points).vertices].tolist();contactY=box[1]+int(yy.max())+1
  leg=dict(url='shared-rear-leg.webp',box=box,pivot=pivot,source=p['url'],sourceSHA256=lowers[name]['sourceSHA256'],overlapPixels=12,cropY=[595,681],alphaCutoff=16,hull=hull)
m=dict(baselineCommit='54fabf5e0860f13403d25f1d801b19b527bcc156',start=1200,end=1500,groundY=690,contactY=contactY,leg=leg,lowers=lowers,keys=[dict(time=1200,x=-37,angle=0),dict(time=1260,x=-32,angle=0),dict(time=1380,x=-7,angle=0),dict(time=1500,x=0,angle=0)],method='Existing rest shin and boot, rigid horizontal translation with zero rotation behind four trimmed thigh drawings. Contact height derives from final sprite alpha hull, not 3D ground or knee biomechanics. No new art or image blending.')
(OUT/'shared-rear-leg.json').write_text(json.dumps(m,indent=2)+'\n');print('Prepared shared rear leg; contact Y',contactY)
