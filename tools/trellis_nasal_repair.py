"""Local nasal shell and upper-lip replacement for the generated menpo.
Artist-directed shape fitted to inspected source landmarks; not a museum replica.
"""
import math
import bpy
import bmesh
import numpy as np

# Normalized Blender coordinates: front is -Y, up is Z.
Z=np.array([.495,.515,.54,.57,.60,.65,.70,.746])
WIDTH=np.array([.012,.052,.100,.118,.096,.068,.052,.035])
DEPTH=np.array([-.568,-.619,-.625,-.614,-.604,-.584,-.558,-.490])

def interp(value,keys,values):
    i=int(np.clip(np.searchsorted(keys,value)-1,0,len(keys)-2));h=keys[i+1]-keys[i]
    t=float(np.clip((value-keys[i])/h,0,1));slopes=np.gradient(values,keys)
    return ((2*t**3-3*t*t+1)*values[i]+(t**3-2*t*t+t)*h*slopes[i]
            +(-2*t**3+3*t*t)*values[i+1]+(t**3-t*t)*h*slopes[i+1])

def width(z):return interp(z,Z,WIDTH)
def depth(x,z):
    u=min(1,abs(x)/width(z))
    wing=.040*math.exp(-((abs(x)-.091)/.032)**2-((z-.566)/.025)**2)
    blend=float(np.clip((z-.56)/.06,0,1));blend=blend*blend*(3-2*blend)
    return interp(z,Z,DEPTH)+.062*u**(1.65-.40*blend)-wing

def lip_bounds(x):
    u=min(1,abs(x)/.137)
    top=.445+.075*(1-u**8)
    bottom=.441-.012*u*u
    return top,bottom

def remove_old_panels(bm):
    faces=[]
    for face in bm.faces:
        c=face.calc_center_median();x=abs(c.x)
        nose=.498<c.z<.742 and x<width(c.z)-.003 and c.y<-.38
        # Upper-lip band ends above the existing mouth aperture.
        top,bottom=lip_bounds(x)
        lip=x<.132 and bottom+.003<c.z<top-.003 and c.y<-.39
        if nose or lip:faces.append(face)
    bmesh.ops.delete(bm,geom=faces,context='FACES')
    return len(faces)

def uv_planar(ob):
    uv=ob.data.uv_layers.new(name='Repair local UV')
    for loop in ob.data.loops:
        co=ob.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=(co.x/.32+.5,(co.z-.40)/.38)

def shell(name,coords,nu,nv,object_mesh,material):
    faces=[]
    for j in range(nv-1):
        for i in range(nu-1):
            q=j*nu+i;faces.append((q,q+1,q+1+nu,q+nu))
    ob=object_mesh(name,coords,faces,material);uv_planar(ob)
    bpy.context.view_layer.objects.active=ob
    modifier=ob.modifiers.new('Physical lacquer plate thickness','SOLIDIFY')
    modifier.thickness=.006;modifier.offset=-1
    # Grid order faces the back. Reverse once to make front normals face -Y.
    bm=bmesh.new();bm.from_mesh(ob.data)
    for f in bm.faces:
        if f.normal.y>0:f.normal_flip()
    bm.to_mesh(ob.data);bm.free()
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return ob

def add_panels(object_mesh,mat):
    red=mat('Menpo repaired lacquer',(.125,.007,.004),0,.44,.18)
    dark=mat('Nostril recessed interior',(.009,.004,.003),0,.88)
    nu,nv=65,81;coords=[]
    for j in range(nv):
        z=Z[0]+(Z[-1]-Z[0])*j/(nv-1)
        for i in range(nu):
            x=width(z)*(2*i/(nu-1)-1);coords.append((x,depth(x,z),z))
    nose=shell('Menpo reconstructed nasal shell',coords,nu,nv,object_mesh,red)
    holes=[]
    # Elliptical through-cuts have a visible rim and an independently recessed
    # dark backing. The backing is not counted as part of the shell aperture.
    for sign in [-1,1]:
        cx=sign*.074;cz=.550;rx=.020;rz=.008;slope=sign*.40;n=96
        vs=[];fs=[]
        for y in [-.80,-.35]:
            for j in range(n):
                t=2*math.pi*j/n;dx=rx*math.cos(t)
                vs.append((cx+dx,y,cz+rz*math.sin(t)+slope*dx))
        for j in range(n):fs.append((j,(j+1)%n,(j+1)%n+n,j+n))
        fs.extend([tuple(range(n-1,-1,-1)),tuple(range(n,2*n))])
        cutter=object_mesh('Temporary nostril cutter',vs,fs,dark)
        bpy.context.view_layer.objects.active=nose
        boolean=nose.modifiers.new('Actual nostril opening','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
        bpy.ops.object.modifier_apply(modifier=boolean.name);bpy.data.objects.remove(cutter,do_unlink=True)
        backing=[]
        for j in range(n):
            t=2*math.pi*j/n;dx=rx*1.12*math.cos(t)
            backing.append((cx+dx,-.44,cz+rz*1.12*math.sin(t)+slope*dx))
        object_mesh('Nostril recessed backing '+str(sign),backing,[tuple(range(n))],dark)
        holes.append({'center_xz':[cx,cz],'radii_xz':[rx,rz],'slope':slope,'backing_y':-.44})
    # Bevel only the actual cut/plate edges, keeping the shaped front smooth.
    bevel=nose.modifiers.new('Soft machined nostril edges','BEVEL');bevel.width=.001;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.45
    bpy.context.view_layer.objects.active=nose;bpy.ops.object.modifier_apply(modifier=bevel.name)
    # Collapse slivers using topology-aware quadric simplification. Merging
    # nearby vertices directly can join the two sides of a thin bevel wall.
    before=len(nose.data.vertices)
    cleanup=nose.modifiers.new('Remove boolean bevel slivers','DECIMATE')
    cleanup.ratio=.80;cleanup.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=cleanup.name)
    bm=bmesh.new();bm.from_mesh(nose.data)
    assert all(e.is_manifold for e in bm.edges), 'Nasal cleanup opened the shell'
    cleanup_vertices=before-len(bm.verts);bm.free()
    coords=[];nu,nv=65,17
    for j in range(nv):
        t=j/(nv-1)
        for i in range(nu):
            x=.137*(2*i/(nu-1)-1);u=abs(x)/.137
            top,bottom=lip_bounds(x);z=top*(1-t)+bottom*t
            y=-.560+5.8*x*x-.006*math.sin(math.pi*t)+.003*math.exp(-(x/.018)**2)
            coords.append((x,y,z))
    lip=shell('Menpo reconstructed upper lip',coords,nu,nv,object_mesh,red)
    return {'nose_object':nose.name,'lip_object':lip.name,'nostrils':holes,
            'plate_thickness':.006,'cleanup_vertices':cleanup_vertices,'material':red.name,
            'limits':['Local overlapping repair, not welded to cheeks','Original cheek vents and lower jaw remain generated','Static model; no rig or collision certification']},red,nose,lip
