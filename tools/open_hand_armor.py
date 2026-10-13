"""Fitted editable kote for the CC0 hand study; no downloaded addon code."""
import math
import random
import bpy
import numpy as np
from mathutils import Vector, Matrix


def build_armor(hand,rig,scene):
    random.seed(1620)
    owned=[]
    def shader(name,c1,c2,rough,metal=0,grain=.0002):
        m=bpy.data.materials.new(name);m.use_nodes=True
        n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
        p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        co=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=85;noise.inputs['Detail'].default_value=4
        l.new(co.outputs['Object'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*c1,1);ramp.color_ramp.elements[1].color=(*c2,1)
        l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
        fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=1700;fine.inputs['Detail'].default_value=2;l.new(co.outputs['Object'],fine.inputs['Vector'])
        b=n.new('ShaderNodeBump');b.inputs['Distance'].default_value=grain;b.inputs['Strength'].default_value=.3
        l.new(fine.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
        roughmap=n.new('ShaderNodeMapRange');roughmap.inputs['To Min'].default_value=rough*.8;roughmap.inputs['To Max'].default_value=min(1,rough*1.15)
        l.new(noise.outputs['Fac'],roughmap.inputs[0]);l.new(roughmap.outputs[0],p.inputs['Roughness'])
        return m
    leather=shader('smoked deer leather — fine grain',(.020,.008,.004),(.13,.062,.024),.82,grain=.00015)
    crimson=shader('worn crimson lacquer',(.025,.001,.002),(.15,.004,.008),.48,.03)
    p=crimson.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.32;p.inputs['Coat Roughness'].default_value=.30
    cloth=shader('indigo cloth lining',(.007,.013,.020),(.035,.049,.060),.94,grain=.00025)
    silk=shader('burgundy silk lacing',(.08,.014,.009),(.28,.07,.026),.9)
    gold=shader('aged brass hardware',(.08,.041,.009),(.34,.23,.065),.48,.8)
    iron=shader('exposed black iron',(.008,.010,.012),(.045,.05,.05),.61,.8)
    linen=shader('waxed seam thread',(.16,.11,.053),(.30,.23,.14),.93)
    def mesh(name,v,f,mat,thickness=0):
        d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update()
        o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);d.materials.append(mat);owned.append(o)
        for p in d.polygons:p.use_smooth=True
        if thickness:
            mod=o.modifiers.new('physical forged thickness','SOLIDIFY');mod.thickness=thickness;mod.offset=0
            mod=o.modifiers.new('soft worn metal edge','BEVEL');mod.width=.00035;mod.segments=2
        return o
    def cord(name,points,r,mat):
        d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=4;d.bevel_depth=r;d.bevel_resolution=2
        s=d.splines.new('POLY');s.points.add(len(points)-1)
        for p,v in zip(s.points,points):p.co=(*v,1)
        o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);d.materials.append(mat);owned.append(o);return o
    scene.frame_set(1);bpy.context.view_layer.update()
    source=hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    verts=[v.co.copy() for v in source.data.vertices]
    stations=np.linspace(-.18,-.018,23);sections=[]
    for yy in stations:
        band=[v for v in verts if abs(v.y-yy)<.005]
        x0=min(v.x for v in band);x1=max(v.x for v in band);z0=min(v.z for v in band);z1=max(v.z for v in band)
        sections.append(((x0+x1)/2,(z0+z1)/2,(x1-x0)/2,(z1-z0)/2))
    fits=[np.polyfit(stations,np.array(sections)[:,i],3) for i in range(4)]
    def radial(y,a,offset=0):
        cx,cz,rx,rz=[float(np.polyval(fit,y)) for fit in fits]
        return Vector((cx+(rx+offset)*math.cos(a),y,cz+(rz+offset)*math.sin(a)))
    # Fabric shell wraps the actual anatomical cross-sections.
    v=[];f=[];nx=64;ny=50
    for j in range(ny+1):
        y=-.178+j/ny*.158
        for k in range(nx):
            a=k*math.tau/nx
            offset=.0025+.0008*math.sin(y*310+a*4)+.0005*math.cos(y*490-a*5)
            v.append(radial(y,a,offset))
    for j in range(ny):
        for k in range(nx):a=j*nx+k;b=j*nx+(k+1)%nx;f.append((a,a+nx,b+nx,b))
    mesh('fitted indigo kote lining',v,f,cloth,.0006)
    # Seven longitudinal splints, actual holes and a restrained rolled border.
    count=7
    for col in range(count):
        a0=math.pi+.12+col*(math.pi-.24)/count+.025
        a1=math.pi+.12+(col+1)*(math.pi-.24)/count-.025
        nu=8;nv=32;v=[];f=[]
        for j in range(nv+1):
            y=-.171+j/nv*.143
            for k in range(nu+1):v.append(radial(y,a0+(a1-a0)*k/nu,.0055))
        holes=[(3,4),(26,27)]
        for j in range(nv):
            for k in range(nu):
                if k in (3,4) and any(j in rows for rows in holes):continue
                a=j*(nu+1)+k;f.append((a,a+nu+1,a+nu+2,a+1))
        plate=mesh('perforated red shino splint '+str(col),v,f,crimson,.0015)
        for a in (a0,a1):cord('thin rolled splint edge',[radial(-.171+j/40*.143,a,.0057) for j in range(41)],.00045,gold)
        # Eyelets encircle the opening; braided ties actually dive through the plate.
        for row in (4,27):
            y=-.171+row/nv*.143;ac=(a0+a1)/2
            pts=[radial(y+math.sin(t*math.tau/32)*.0042,ac+math.cos(t*math.tau/32)*(a1-a0)*.12,.0065) for t in range(33)]
            cord('raised eyelet',pts,.00045,iron)
            if col<count-1:
                other=ac+(math.pi-.24)/count
                points=[]
                for k in range(25):
                    t=k/24;off=.0025+.006*math.sin(math.pi*t)
                    points.append(radial(y+.001*math.sin(t*math.tau),ac+(other-ac)*t,off))
                cord('silk through paired eyelets',points,.0009,silk)
                cord('twisted silk filament',[p+Vector((0,.00055*math.sin(k*2),.00055*math.cos(k*2))) for k,p in enumerate(points)],.00018,linen)
    for y in (-.176,-.023):
        cord('bound cuff',[radial(y,k*math.tau/96,.0034) for k in range(97)],.0021,leather)
        for k in range(64):
            a=k*math.tau/64
            cord('cuff running stitch',[radial(y-.001,a,.0052),radial(y+.001,a+.012,.0052)],.00028,linen)
    # A fitted dorsal hand plate follows the body surface and wrist pose.
    def dorsal(x,y,offset=.002):
        hit,p,n,index=source.ray_cast(Vector((x,y,-.2)),Vector((0,0,1)))
        if not hit:raise ValueError(('hand surface missing',x,y))
        return p+n*offset
    v=[];f=[];nx=14;ny=18
    for j in range(ny+1):
        t=j/ny;y=.013+t*.067;width=.020+.012*math.sin(t*math.pi*.80)
        for k in range(nx+1):v.append(dorsal((k/nx*2-1)*width,y,.003))
    for j in range(ny):
        for k in range(nx):a=j*(nx+1)+k;f.append((a,a+nx+1,a+nx+2,a+1))
    tekko=mesh('fitted crimson tekko',v,f,crimson,.0013)
    for row in range(2):
        for col in range(3):
            x=(col-1)*.014;y=.037+row*.017
            cord('six coin tekko crest',[dorsal(x+.0045*math.cos(k*math.tau/32),y+.0045*math.sin(k*math.tau/32),.0042) for k in range(33)],.00065,gold)
    for sign in (-1,1):
        for j in range(18):
            y=.013+j/18*.061;width=.022+.012*math.sin((y-.013)/.067*math.pi*.8)
            cord('tekko leather seam',[dorsal(sign*width,y,.0014),dorsal(sign*(width+.001),y+.0017,.0014)],.0003,linen)
    # Short sewn panels follow each phalanx; the original hand weights still
    # deform the continuous glove, rather than separate finger primitives.
    for digit in range(2,6):
        for segment in range(1,4):
            bone=rig.data.bones[f'finger{digit}-{segment}.R']
            for side in (-1,1):
                for stitch in range(5):
                    pts=[]
                    for t in (.16+stitch*.13,.20+stitch*.13):
                        mid=bone.head_local.lerp(bone.tail_local,t)+Vector((side*.006,0,0))
                        hit,p,n,index=source.ray_cast(mid+Vector((0,0,-.08)),Vector((0,0,1)))
                        if hit:pts.append(p+n*.0005)
                    if len(pts)==2:
                        o=cord('finger panel stitching',pts,.00020,linen)
                        o['attach_bone']=bone.name
    for o in owned:
        o['study_component']='open-source-hand-kote'
        name=o.name
        bone=o.get('attach_bone','wrist.R' if any(k in name for k in ('tekko','hand plate')) else 'lowerarm02.R')
        o.parent=rig;o.parent_type='BONE';o.parent_bone=bone
    bpy.context.view_layer.update()
    for o in owned:o.matrix_world=Matrix.Identity(4)
    bpy.context.view_layer.update()
    return owned,leather
