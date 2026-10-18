"""Validate cut-only source reuse and measure actual browser handoffs."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
OUT=Path('docs/routes/jigoku-2d/free-arm-settle');m=json.loads((OUT/'shared-rear-leg.json').read_text());pixels=0
for p in [m['leg'],*m['lowers'].values()]:
 assert hashlib.sha256((OUT/p['source']).read_bytes()).hexdigest()==p['sourceSHA256']
 im=Image.open(OUT/p['url']);pixels+=im.width*im.height
def expected_alpha(source,p,overlap=0):
 h,w=source.shape[:2];points=[[x-p['box'][0]-overlap,y-p['box'][1]] for x,y in p['seam']]
 polygon=[[points[0][0],-100],*points,[points[-1][0],h+100],[w+100,h+100],[w+100,-100]]
 mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon(polygon,fill=255);region=np.array(mask)>0
 if 'cropY' in p:
  yy,_=np.indices(region.shape);region &= (yy+p['box'][1]>=p['cropY'][0])&(yy+p['box'][1]<p['cropY'][1])
 return region
for p in m['lowers'].values():
 a=np.array(Image.open(OUT/p['source']).convert('RGBA'));b=np.array(Image.open(OUT/p['url']).convert('RGBA'))
 expected=a[:,:,3].copy();expected[expected_alpha(a,p)]=0
 assert a.shape==b.shape;assert np.array_equal(b[:,:,3],expected);visible=b[:,:,3]>0;assert visible.any();assert np.array_equal(a[visible],b[visible])
p=m['leg'];rest=m['lowers']['rest'];a=np.array(Image.open(OUT/p['source']).convert('RGBA'));b=np.array(Image.open(OUT/p['url']).convert('RGBA'))
expected=a[:,:,3].copy();expected[~expected_alpha(a,rest,p['overlapPixels'])]=0;expected[expected<=p['alphaCutoff']]=0
x=p['box'][0]-rest['box'][0];y=p['box'][1]-rest['box'][1];a=a[y:y+b.shape[0],x:x+b.shape[1]];expected=expected[y:y+b.shape[0],x:x+b.shape[1]]
visible=b[:,:,3]>0;assert visible.any();assert np.array_equal(a[visible],b[visible]);assert np.array_equal(b[:,:,3],expected)
assert p['box'][1]+np.where(visible)[0].max()+1==m['contactY']<m['groundY']
metrics=[]
for t in [1200,1240,1320,1440]:
 row={'time':t}
 for name,folder in [('previous',Path('.tmp/rear-leg-baseline')),('current',OUT/'handoffs/leg')]:
  before=np.array(Image.open(folder/f'{t}-before.png').convert('RGB'),dtype=float);after=np.array(Image.open(folder/f'{t}-after.png').convert('RGB'),dtype=float)
  row[name]={'fullRGBMeanDelta':float(np.abs(before-after).mean()),'lowerRegionRGBMeanDelta':float(np.abs(before[375:485,430:590]-after[375:485,430:590]).mean()),'captureSHA256':{suffix:hashlib.sha256((folder/f'{t}-{suffix}.png').read_bytes()).hexdigest() for suffix in ['before','after']}}
 metrics.append(row)
for row in metrics[1:]:assert row['current']['fullRGBMeanDelta']<row['previous']['fullRGBMeanDelta']
report=dict(passed=True,additionalRGBA8MiB=pixels*4/1048576,checks=['Source hashes match; retained pixels are exact original RGBA; no added alpha in trimmed lower drawings','One native-size rest calf/boot reused; no image generation, body stretch or image fade','Actual browser captures compare identical times and camera; later three drawing cuts improve'],contactY=m['contactY'],groundY=m['groundY'],lowerRegionInCapture=[430,375,590,485],handoffs=metrics,limits='First 1200 ms handoff is slightly worse; waist and thigh still change drawings. Pixel deltas measure discontinuity, not anatomy or visual realism. Contact is authored 2D projection, not physical ground.')
(OUT/'shared-rear-leg-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
