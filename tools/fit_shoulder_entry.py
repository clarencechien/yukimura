"""Read-only registration seed for the original plate versus the bridge plate."""
import json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import affine_transform
from scipy.optimize import differential_evolution
p=Path(__file__).resolve().parents[1]/'docs/routes/jigoku-2d/free-arm-settle';s=json.loads((p/'settle.json').read_text());f=json.loads((p/'bridge.json').read_text())['frames'][0]
src=np.array(Image.open(p/'cap.webp')).astype(float);source=((src[:,:,0]>100)&(src[:,:,0]>src[:,:,1]*1.2)&(src[:,:,1]>src[:,:,2]*1.5))*src[:,:,3]/255;target=np.zeros((240,240));part=f['parts']['cap'];dst=np.array(Image.open(p/part['url'])).astype(float);a=((dst[:,:,0]>100)&(dst[:,:,0]>dst[:,:,1]*1.2)&(dst[:,:,1]>dst[:,:,2]*1.5))*dst[:,:,3]/255
origin=np.array([390,450]);x,y=np.array(part['box'][:2])-origin;target[y:y+a.shape[0],x:x+a.shape[1]]=a
pivot=np.array(s['shoulder'])-s['parts']['cap']['box'][:2]
def transform(q):
 angle,dx,dy=q;angle=np.deg2rad(angle);c,s=np.cos(angle),np.sin(angle);R=np.array([[c,-s],[s,c]])
 point=np.array(f['shoulder'])+np.array([dx,dy])-origin
 offset=pivot-R.T@point;matrix=R.T
 return affine_transform(source,matrix[::-1,::-1],offset=offset[::-1],output_shape=target.shape,order=1)
def loss(q):
 a=transform(q);return 1-np.minimum(a,target).sum()/np.maximum(a,target).sum()
r=differential_evolution(loss,[(-65,10),(-65,40),(0,65)],seed=7,popsize=12,maxiter=80,tol=.00001)
print(json.dumps(dict(angle=round(r.x[0],2),offset=[round(v,2) for v in r.x[1:]],goldMaskIoU=1-r.fun,method='Rigid gold-edge alignment seed only; not an anatomy or quality score.'),indent=2))
