"""Offline winter battlefield surfaces: no per-frame canvas generation or CDN.
Linear pigment, OpenGL tangent normals and packed roughness/metallic; Blender NumPy.
"""
import bpy
import numpy as np
import math,json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent.parent/'public/environment';OUT.mkdir(exist_ok=True)
rng=np.random.default_rng(1614);report={}
def save(name,data,space):
    h,w=data.shape[:2];rgba=np.ones((h,w,4),np.float32);rgba[:,:,:3]=np.clip(data,0,1)
    im=bpy.data.images.new(name,w,h,alpha=False);im.colorspace_settings.name=space;im.pixels.foreach_set(rgba.ravel())
    path=OUT/(name+'.png');im.filepath_raw=str(path);im.file_format='PNG';im.save();bpy.data.images.remove(im)
    raw=path.read_bytes();report[path.name]={'bytes':len(raw),'width':w,'height':h,'sha256':hashlib.sha256(raw).hexdigest()}
def normals(height,dx,dy):
    y,x=np.gradient(height,dy,dx);n=np.stack((-x,-y,np.ones_like(x)),axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True);return n*.5+.5
def emit(name,color,height,rough,metal=0,scale=(1,1)):
    h,w=height.shape;save(name+'-color',color,'sRGB');save(name+'-normal',normals(height,scale[0]/w,scale[1]/h),'Non-Color')
    surface=np.zeros((h,w,3));surface[:,:,0]=1;surface[:,:,1]=rough;surface[:,:,2]=metal;save(name+'-surface',surface,'Non-Color')
def wash(x,y):return .48+.20*np.sin(x*.61+np.sin(y*.47)*1.8)+.14*np.sin(y*1.31-x*.87)+.09*np.sin(x*3.7+y*2.8)
# Ground UV covers exactly x=-50..50 and z=-25..185, without repeated road tiles.
n=2048;v,u=np.mgrid[0:n,0:n].astype(np.float32)/(n-1);x=(u-.5)*100;z=v*210-25
noise=wash(x,z);fine=rng.random((n,n),dtype=np.float32)
center=1.9*np.sin(z*.08);road=np.exp(-((x-center)/(3.7+noise*1.8))**2)
ruts=np.maximum(np.exp(-((x-center-1.25)/.25)**2),np.exp(-((x-center+1.25)/.25)**2))
trampled=np.clip((road+noise*.47-.39)*1.7,0,1)
scorch=np.zeros_like(u)
for zz in (6,43,88,138):
    for xx in (-8.6,8.6):scorch=np.maximum(scorch,np.exp(-((x-xx)**2+(z-zz)**2)/5))
# Irregular dirty snow collects around the defensive lines, with dark thawed feet.
defence=np.exp(-((abs(x)-15.2)/3.2)**2)*(.28+.22*np.sin(z*.48)**2)
packed_snow=np.clip((noise-.57)*2.5,0,.34)*road
dirty=np.clip(trampled+defence*.5+scorch*.7+ruts*.5-packed_snow,0,.94)
wet=np.clip((noise-.44)*2.7,0,1)*trampled*.85
snow=np.stack((.65+noise*.16,.71+noise*.15,.75+noise*.13),axis=-1)
mud=np.stack((.22+noise*.11,.16+noise*.09,.105+noise*.065),axis=-1)
color=snow*(1-dirty[:,:,None])+mud*dirty[:,:,None]
color*=1-scorch[:,:,None]*.30;color*=1-wet[:,:,None]*.10
color+=(fine[:,:,None]-.5)*.025
height=.07*(1-dirty)+noise*.019-ruts*.025+(fine-.5)*.0015
rough=.96-dirty*.19-wet*.48
# Alternating boot impressions along the road and flanking troop approaches.
for lane in (-5,-2.9,3.2,6.1):
    for zz in np.arange(-18,180,.86):
        if rng.random()<.18:continue
        xx=lane+math.sin(zz*.16)*.7+(.17 if int(zz/.86)%2 else -.17)+rng.uniform(-.15,.15)
        zz+=rng.uniform(-.18,.18)
        cx=int((xx/100+.5)*(n-1));cy=int((zz+25)/210*(n-1));rx=3;ry=2
        ys=slice(max(0,cy-ry),min(n,cy+ry+1));xs=slice(max(0,cx-rx),min(n,cx+rx+1))
        yy,xxi=np.mgrid[ys,xs];mask=np.exp(-((xxi-cx)/1.35)**4-((yy-cy)/1.35)**4)
        color[ys,xs]*=1-mask[:,:,None]*rng.uniform(.24,.43);height[ys,xs]-=mask*.015;rough[ys,xs]-=mask*.12
save('terrain-color',color,'sRGB')
# Surface maps need less resolution than the painted route and boot marks.
save('terrain-normal',normals(height[::2,::2],100/1024,210/1024),'Non-Color')
surface=np.zeros((1024,1024,3));surface[:,:,0]=1;surface[:,:,1]=rough[::2,::2];save('terrain-surface',surface,'Non-Color')
del u,v,x,z,color,height,snow,mud,fine,noise,road,ruts,trampled,scorch,defence,dirty,wet,rough
n=512;v,u=np.mgrid[0:n,0:n].astype(np.float32)/(n-1);noise=wash(u*23,v*23);grain=rng.random((n,n),dtype=np.float32)-.5
for kind in ('wood','stone','plaster','roof','snow'):
    h=np.zeros((n,n));metal=0
    if kind=='wood':
        fiber=np.sin(u*190+np.sin(v*13)*2);split=np.exp(-(np.sin(u*57+np.sin(v*9)*.14)/.055)**2)
        damp=np.exp(-v*5)*.45;burn=np.exp(-((u-.67)/.12)**2)*np.exp(-v*3)*.5
        shade=np.clip(.75+noise*.4+fiber*.10-split*.42-damp-burn,.18,1.2)
        color=shade[:,:,None]*np.array([.19,.115,.063]);h=fiber*.0006-split*.003
        rough=.80-damp*.5
    elif kind=='stone':
        row=(v*7)%1;col=(u*5+(np.floor(v*7)%2)*.5)%1
        edge=np.minimum(np.minimum(row,1-row),np.minimum(col,1-col));joint=np.exp(-edge*55)
        shade=.68+noise*.35-joint*.42-np.exp(-v*6)*.20
        color=shade[:,:,None]*np.array([.29,.32,.33]);h=.013*(1-joint)+noise*.002;rough=.89
    elif kind=='plaster':
        damp=np.exp(-v*5)*(.5+noise*.4);streak=np.exp(-(np.sin(u*49+v*3)/.13)**2)*(.5+.5*v)
        crack=np.exp(-(np.sin(u*57+np.sin(v*21)*.4)/.04)**2)*.20
        shade=.85+noise*.17-damp*.44-streak*.12-crack
        color=shade[:,:,None]*np.array([.68,.64,.53]);h=noise*.0015-crack*.006;rough=.92
    elif kind=='roof':
        rib=(np.cos(u*math.tau*14)+1)*.5;seam=np.exp(-((v*7)%1)*60)
        snow=np.clip((noise+v*.65-.94)*2.7,0,.75)
        dark=(.7+rib*.25-seam*.3)[:,:,None]*np.array([.035,.05,.068])
        color=dark*(1-snow[:,:,None])+np.array([.58,.65,.70])*snow[:,:,None]
        h=rib*.005-seam*.0015;rough=.66+snow*.3;metal=.08
    else:
        shade=.86+noise*.12+grain*.025;color=shade[:,:,None]*np.array([.72,.78,.82]);h=noise*.004+grain*.0005;rough=.98
    emit(kind,color,h,rough,metal)
(OUT/'manifest.json').write_text(json.dumps({'generator':'Blender NumPy / weathered winter v1','files':report,'bytes':sum(v['bytes'] for v in report.values())},indent=2)+'\n')
print('Environment maps:',len(report),'bytes',sum(v['bytes'] for v in report.values()))
