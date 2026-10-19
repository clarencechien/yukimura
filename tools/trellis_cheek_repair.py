"""Continuous cheek and jaw return plates fitted to the generated mask.

Coordinates use the normalized head: front -Y, up Z. Parts intentionally
lap beneath existing repair pieces; this is not a welded full-head retopology.
"""
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
from trellis_mask_rim import contour
from trellis_nasal_repair import interp
from trellis_lower_mask import finish_uv


def bounds(kind,x):
    if kind=='cheek':
        low=interp(x,np.array([.056,.10,.17,.23,.307]),np.array([.680,.607,.573,.584,.674]))
        return low,contour(x)-.038
    low=interp(x,np.array([.075,.125,.19,.245,.285]),np.array([.215,.242,.279,.333,.402]))
    high=interp(x,np.array([.075,.125,.19,.245,.285]),np.array([.331,.372,.395,.415,.470]))
    return low,high


def remove_old_cheeks(bm):
    selected=[];counts={'cheek':0,'jaw':0}
    for f in bm.faces:
        c=f.calc_center_median();x=abs(c.x)
        if c.y>=-.20:continue
        for kind,lo,hi in [('cheek',.061,.302),('jaw',.080,.280)]:
            if not lo<x<hi:continue
            bottom,top=bounds(kind,x)
            if bottom+.004<c.z<top-.004:
                selected.append(f);counts[kind]+=1;break
    bmesh.ops.delete(bm,geom=selected,context='FACES')
    return counts


def add_cheeks(object_mesh,red,gold,surface):
    objects=[];studs=[]
    covers=[]
    for name in ['Menpo continuous eye rim and return','Menpo reconstructed nasal shell','Menpo reconstructed chin shield','Menpo cheek vent frame -1','Menpo cheek vent frame 1']:
        bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);covers.append(BVHTree.FromBMesh(bm));bm.free()
    def under_existing(x,y,z):
        for tree in covers:
            hit=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))[0]
            if hit is not None:y=max(y,hit.y+.003)
        return y
    for kind,lo,hi in [('cheek',.056,.307),('jaw',.075,.285)]:
        nu,nv=81,17
        xs=np.linspace(lo,hi,nu);zs=np.zeros((nv,nu));ys=np.zeros_like(zs)
        for j in range(nv):
            t=j/(nv-1)
            for i,x in enumerate(xs):
                bottom,top=bounds(kind,x);z=bottom+(top-bottom)*t;zs[j,i]=z
                # Robustly sample both sides, avoiding isolated relief spikes.
                hits=[surface(s*(x+dx),z+dz) for s in [-1,1] for dx,dz in [(0,0),(-.003,0),(.003,0),(0,-.003),(0,.003)]]
                ys[j,i]=np.median(hits)
        # A robust cubic surface retains broad curvature without copying pits,
        # rivet relief or the generated vent's depth discontinuity.
        xx=np.broadcast_to(xs,(nv,nu));u=(xx-.18)/.15;v=(zs-zs.mean())/.10
        design=np.stack([(u**i*v**j).ravel() for i in range(4) for j in range(4-i)],axis=1)
        target=ys.ravel();weights=np.ones(len(target))
        for _ in range(4):
            fit=np.linalg.lstsq(design*weights[:,None],target*weights,rcond=None)[0]
            residual=abs(target-design@fit);scale=max(.003,float(np.median(residual))*1.4826)
            weights=np.minimum(1,1.5*scale/np.maximum(residual,1e-8))
        ys=(design@fit).reshape(nv,nu)-.006
        if kind=='cheek':
            # Continue the existing rim's lower surface smoothly rather than
            # forcing only overlapping vertices behind it (which leaves a ledge).
            anchors=[]
            for i,x in enumerate(xs):
                seam=contour(x)-.058
                hit=covers[0].ray_cast(Vector((float(x),-2,seam)),Vector((0,1,0)))[0]
                t=(seam-zs[0,i])/(zs[-1,i]-zs[0,i])
                anchor=hit.y+.003 if hit is not None else float(np.interp(seam,zs[:,i],ys[:,i]))
                anchors.append(anchor)
            anchors=np.convolve(np.pad(anchors,2,mode='edge'),np.ones(5)/5,mode='valid')
            for i,x in enumerate(xs):
                seam=contour(x)-.058;t=(seam-zs[0,i])/(zs[-1,i]-zs[0,i])
                if t>.15:
                    bottom=ys[0,i]
                    ys[:,i]=bottom+(anchors[i]-bottom)*np.linspace(0,1,nv)/t
        for sign in [-1,1]:
            vs=[];fs=[];count=nu*nv
            for rear in [False,True]:
                for j in range(nv):
                    for i,x in enumerate(xs):vs.append((sign*x,under_existing(sign*x,float(ys[j,i]),float(zs[j,i]))+(.006 if rear else 0),float(zs[j,i])))
            for rear in [0,1]:
                for j in range(nv-1):
                    for i in range(nu-1):
                        q=rear*count+j*nu+i;f=(q,q+1,q+nu+1,q+nu);fs.append(f if not rear else f[::-1])
            perimeter=list(range(nu))+[j*nu+nu-1 for j in range(1,nv)]+list(range(count-2,count-nu-1,-1))+[j*nu for j in range(nv-2,0,-1)]
            for i,a in enumerate(perimeter):
                b=perimeter[(i+1)%len(perimeter)];fs.append((a,a+count,b+count,b))
            ob=object_mesh('Menpo continuous '+kind+' plate '+str(sign),vs,fs,red);finish_uv(ob);objects.append(ob.name)
            if kind=='jaw':
                # Three restrained rivets on the new lower rail, with shared brass.
                for k,x in enumerate([.135,.190,.245]):
                    i=int(round((x-lo)/(hi-lo)*(nu-1)));j=5
                    cy=float(ys[j,i])-.002;cz=float(zs[j,i]);cx=sign*float(xs[i]);rx=.006;ry=.004;rz=.006
                    n=24;rings=8;v=[(cx,cy-ry,cz)];f=[]
                    for r in range(1,rings):
                        theta=math.pi*r/rings
                        for q in range(n):
                            a=2*math.pi*q/n;v.append((cx+rx*math.sin(theta)*math.cos(a),cy-ry*math.cos(theta),cz+rz*math.sin(theta)*math.sin(a)))
                    v.append((cx,cy+ry,cz));end=len(v)-1
                    for q in range(n):f.append((0,1+q,1+(q+1)%n))
                    for r in range(rings-2):
                        for q in range(n):
                            a=1+r*n+q;b=1+r*n+(q+1)%n;f.append((a,a+n,b+n,b))
                    for q in range(n):f.append((end,1+(rings-2)*n+(q+1)%n,1+(rings-2)*n+q))
                    stud=object_mesh('Menpo jaw rivet '+str(sign)+' '+str(k),v,f,gold);finish_uv(stud);studs.append(stud.name)
    return {'plates':objects,'rivets':studs,'thickness':.006,'surface_sampling':'Bilateral median samples, robust cubic fit and overlap beneath existing repairs',
            'limits':['Overlapping repair pieces, not a welded mask','Outer side hardware and helmet remain generated','Static fit; no animation certification']}
