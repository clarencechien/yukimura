"""Fitted cheek vent frames and central chin shield, with shared finish UVs."""
import math
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from trellis_nasal_repair import interp

CHIN=[(-.045,.383),(.045,.383),(.075,.345),(.109,.266),(.074,.218),(0,.205),(-.074,.218),(-.109,.266),(-.075,.345)]
INLAY=[(-.017,.352),(.017,.352),(.025,.307),(.046,.244),(0,.227),(-.046,.244),(-.025,.307)]

def chin_y(x,z):
    center=interp(z,np.array([.205,.22,.25,.28,.31,.34,.385]),np.array([-.450,-.494,-.542,-.562,-.546,-.535,-.536]))
    return center+.095*(abs(x)/.105)**1.4

def vent_center(z):return .202-.07*(z-.48)
def vent_y(x,z):return -.400+1.15*(abs(x)-.202)-.13*(z-.48)

def inside_polygon(x,z,polygon):
    inside=False
    for i,(ax,az) in enumerate(polygon):
        bx,bz=polygon[(i+1)%len(polygon)]
        if (az>z)!=(bz>z) and x<(bx-ax)*(z-az)/(bz-az)+ax:inside=not inside
    return inside

def remove_old_lower(bm):
    remove=[];counts={'vent_faces':0,'chin_faces':0};chin_outline=boundary(CHIN)
    for f in bm.faces:
        c=f.calc_center_median();x=abs(c.x)
        vent=(.365<c.z<.591 and .14<x<.265 and c.y<-.235
              and abs((x-vent_center(c.z))/.045)**4+abs((c.z-.48)/.101)**4<1)
        chin=(.19<c.z<.40 and x<.12 and c.y<-.30 and inside_polygon(c.x/.995,.294+(c.z-.294)/.995,chin_outline))
        if vent or chin:
            remove.append(f);counts['vent_faces' if vent else 'chin_faces']+=1
    bmesh.ops.delete(bm,geom=remove,context='FACES')
    return counts

def finish_uv(ob):
    uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='Shared menpo finish UV')
    for loop in ob.data.loops:
        co=ob.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x/.70+.5,co.z)

def boundary(points,steps=12):
    result=[];points=np.array(points)
    for i,p1 in enumerate(points):
        p0=points[(i-1)%len(points)];p2=points[(i+1)%len(points)];p3=points[(i+2)%len(points)]
        for j in range(steps):
            t=j/steps
            result.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    return result

def shield(name,points,depth,thickness,offset,object_mesh,material,surface=None,crown=.001):
    outline=boundary(points);n=len(outline);center=np.mean(points,axis=0);rings=12;verts=[];faces=[]
    edge_y=None
    if surface:
        raw=np.array([surface(x,z) for x,z in outline]);fallback=np.array([depth(x,z) for x,z in outline])
        raw=np.where((raw<-.30)&(raw>-.65),raw,fallback)
        raw=np.array([np.median([raw[(i+j)%n] for j in range(-3,4)]) for i in range(n)])
        edge_y=np.array([np.mean([raw[(i+j)%n] for j in range(-3,4)]) for i in range(n)])-.001
    # Two identical surfaces and a joined perimeter: no boolean slivers.
    for rear in [False,True]:
        verts.append((center[0],depth(*center)+offset+(thickness if rear else 0),center[1]))
        for j in range(1,rings+1):
            u=j/rings
            for index,p in enumerate(outline):
                x,z=center+(p-center)*u
                # A subtle crown makes the edge return meet the body smoothly.
                y=depth(x,z)
                if edge_y is not None:
                    blend=max(0,(u-.72)/.28);blend=blend*blend*(3-2*blend)
                    y=y*(1-blend)+edge_y[index]*blend
                y+=offset-crown*math.sin(math.pi*u)+(thickness if rear else 0)
                verts.append((x,y,z))
    count=1+n*rings
    for side in [0,1]:
        start=side*count
        for i in range(n):
            f=(start,start+1+i,start+1+(i+1)%n);faces.append(f if side==0 else f[::-1])
        for j in range(rings-1):
            for i in range(n):
                a=start+1+j*n+i;b=start+1+j*n+(i+1)%n
                f=(a,b,b+n,a+n);faces.append(f if side==0 else f[::-1])
    for i in range(n):
        a=1+(rings-1)*n+i;b=1+(rings-1)*n+(i+1)%n
        faces.append((a,a+count,b+count,b))
    ob=object_mesh(name,verts,faces,material);finish_uv(ob);return ob

def add_lower_parts(object_mesh,mat,red,surface):
    gold=mat('Menpo aged brass shared finish',(.32,.18,.050),.78,.44)
    dark=mat('Vent recessed cloth lining',(.009,.007,.005),0,.92)
    frames=[];vents=[]
    for sign in [-1,1]:
        n=128;vs=[];fs=[];bands=[]
        # Outer red return, softly rolled gold face, dark inner wall, rear.
        profile=[(.047,.103,.003),(.047,.103,-.002),(.045,.101,-.006),(.034,.088,-.006),(.030,.084,-.002),(.030,.084,.012),(.047,.103,.012)]
        for rx,rz,dy in profile:
            for i in range(n):
                a=2*math.pi*i/n;c=math.cos(a);s=math.sin(a)
                z=.48+rz*math.copysign(abs(s)**.5,s)
                x=sign*(vent_center(z)+rx*math.copysign(abs(c)**.5,c))
                vs.append((x,vent_y(x,z)+dy,z))
        for j in range(len(profile)):
            for i in range(n):
                fs.append((j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i));bands.append(j)
        name='Menpo cheek vent frame '+str(sign);ob=object_mesh(name,vs,fs,red);ob.data.materials.append(gold);ob.data.materials.append(dark)
        for f,band in zip(ob.data.polygons,bands):f.material_index=1 if band in (1,3) else (2 if band==4 else 0)
        finish_uv(ob);frames.append(name)
        # Separate cloth liner sits behind the aperture, not across its front.
        vs=[(sign*.202,vent_y(sign*.202,.48)+.048,.48)];fs=[]
        for i in range(n):
            a=2*math.pi*i/n;c=math.cos(a);s=math.sin(a);z=.48+.090*math.copysign(abs(s)**.5,s)
            x=sign*(vent_center(z)+.036*math.copysign(abs(c)**.5,c))
            vs.append((x,vent_y(x,z)+.048,z))
        for i in range(n):fs.append((0,1+i,1+(i+1)%n))
        object_mesh('Menpo recessed cheek cloth '+str(sign),vs,fs,dark)
        vents.append({'center_xz':[sign*.202,.48],'half_opening_xz':[.030,.084],'lining_depth':.048})
    # Keep a small fitted overlap beyond the source cut to cover its jagged triangulated edge.
    cover=[(x*1.07,.294+(z-.294)*1.07) for x,z in CHIN]
    chin=shield('Menpo reconstructed chin shield',cover,chin_y,.007,-.006,object_mesh,red,surface=surface)
    bm=bmesh.new();bm.from_mesh(chin.data);chin_bvh=BVHTree.FromBMesh(bm);bm.free()
    def fitted_chin(x,z):
        hit=chin_bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))[0]
        return hit.y if hit is not None else chin_y(x,z)
    inlay=shield('Menpo chin brass inlay',INLAY,fitted_chin,.004,-.0035,object_mesh,gold,crown=.0002)
    return {'vent_frames':frames,'vent_apertures':vents,'chin':chin.name,'inlay':inlay.name,
            'limits':['Local overlapping panels, not welded to the whole mask','Side jaw and helmet still contain generated geometry','Vent cloth backing is a separate recessed part']},gold
