"""Local menpo opening trim, preserving source face UV interpolation.

Only the eye-opening boundary is rebuilt. The generated lower mask is not
claimed to be retopologized or watertight.
"""
import bmesh
import numpy as np

XS=np.array([0,.04,.065,.10,.17,.23,.29,.32])
ZS=np.array([.765,.753,.721,.682,.659,.676,.738,.795])
SLOPES=np.gradient(ZS,XS);SLOPES[0]=0

def contour(x):
    x=min(abs(float(x)),XS[-1]);i=min(np.searchsorted(XS,x,side='right')-1,len(XS)-2)
    h=XS[i+1]-XS[i];t=(x-XS[i])/h
    return ((2*t**3-3*t*t+1)*ZS[i]+(t**3-2*t*t+t)*h*SLOPES[i]
            +(-2*t**3+3*t*t)*ZS[i+1]+(t**3-t*t)*h*SLOPES[i+1])

def trim_opening(bm,skin_index):
    """Clip crossing triangles at the curve, interpolating each loop's UV.

    Unlike a face-center delete, this puts every newly cut vertex on the
    lower edge of the replacement strip instead of retaining triangle tips.
    """
    uv=bm.loops.layers.uv.active;remove=[];patches=[];crossings=0
    for f in list(bm.faces):
        c=f.calc_center_median();ax=abs(c.x)
        region=ax<.312 and .59<c.z<.865 and -.60<c.y<-.20 and (c.z<.79 or c.y>-.48)
        bridge=ax<.10 and .67<c.z<.82 and -.59<c.y<-.20
        residual=f.material_index==skin_index and ax<.31 and .63<c.z<.84 and -.48<c.y<-.20
        if not (region or bridge or residual):continue
        # Replace the full strip beneath the old gold lip, not just cover it.
        values=[v.co.z-(contour(v.co.x)-.055) for v in f.verts]
        if max(values)<=0 and not residual:continue
        remove.append(f)
        if min(values)>=0 or residual:continue
        polygon=[];loops=list(f.loops)
        for i,loop in enumerate(loops):
            nxt=loops[(i+1)%len(loops)];d=values[i];dn=values[(i+1)%len(loops)]
            if d<=0:polygon.append((loop.vert.co.copy(),loop[uv].uv.copy()))
            if (d<=0)!=(dn<=0):
                t=d/(d-dn);co=loop.vert.co.lerp(nxt.vert.co,t)
                co.z=contour(co.x)-.055
                polygon.append((co,loop[uv].uv.lerp(nxt[uv].uv,t)));crossings+=1
        if len(polygon)>=3:patches.append((polygon,f.material_index,f.smooth))
    bmesh.ops.delete(bm,geom=remove,context='FACES')
    for polygon,material,smooth in patches:
        face=bm.faces.new([bm.verts.new(co) for co,uvco in polygon]);face.material_index=material;face.smooth=smooth
        for loop,(_,uvco) in zip(face.loops,polygon):loop[uv].uv=uvco
    return {'removed_faces':len(remove),'clipped_faces':len(patches),'boundary_intersections':crossings}

def add_rim(surface,object_mesh,mat):
    """Continuous rolled edge and lacquer return, not a flat pasted eye strip."""
    xs=np.linspace(-.307,.307,193);zs=np.array([contour(x) for x in xs])
    ys=np.array([surface(x,z-.012) for x,z in zip(xs,zs)])
    # Remove single-triangle depth spikes without flattening the nose's volume.
    ys=np.array([np.median(ys[max(0,i-4):min(len(ys),i+5)]) for i in range(len(ys))])
    ys=np.convolve(np.pad(ys,(5,5),mode='edge'),np.ones(11)/11,mode='valid')-.004
    red=mat('Menpo edge / oxblood lacquer',(.16,.009,.005),0,.39,.22)
    gold=mat('Menpo rolled lip / muted brass',(.30,.17,.045),.75,.42)
    # Closed cross section with recessed rear lip and a tapered lower overlap.
    profile=[(-.004,0),(-.006,-.004),(-.005,-.016),(-.004,-.040),(-.001,-.061),(.009,-.061),(.010,-.006),(.003,0)]
    verts=[];faces=[];bands=[]
    depths=[]
    for dy,dz in profile:
        raw=np.array([surface(x,z+dz) for x,z in zip(xs,zs)])
        smooth=np.array([np.median(raw[max(0,i-3):min(len(raw),i+4)]) for i in range(len(raw))])
        smooth=np.convolve(np.pad(smooth,(3,3),mode='edge'),np.ones(7)/7,mode='valid')
        blend=min(1,abs(dz)/.061)
        depths.append(ys*(1-blend)+smooth*blend+dy)
    for i,(x,z) in enumerate(zip(xs,zs)):
        for j,(dy,dz) in enumerate(profile):verts.append((float(x),float(depths[j][i]),float(z+dz)))
    n=len(profile)
    for i in range(len(xs)-1):
        for j in range(n):
            faces.append((i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n));bands.append(j)
    faces.extend([tuple(range(n-1,-1,-1)),tuple((len(xs)-1)*n+j for j in range(n))]);bands.extend([-1,-1])
    ob=object_mesh('Menpo continuous eye rim and return',verts,faces,red);ob.data.materials.append(gold)
    for face,band in zip(ob.data.polygons,bands):face.material_index=1 if band in (0,7) else 0
    return {'object':ob.name,'stations':len(xs),'closed_cross_section':True,'scope':'Upper eye-opening rim only; lower generated mask is retained'}
