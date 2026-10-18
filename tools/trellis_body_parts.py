"""Reusable armor surfaces, hardware and shared procedural PBR tiles."""
import math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector

REGIONS={}
def mesh(name,verts,faces,material,region):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);data.materials.append(material)
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(data);bm.free()
    for f in data.polygons:f.use_smooth=True
    ob['refinement_region']=region;REGIONS.setdefault(region,[]).append(name)
    return ob

def uv_world(ob):
    uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='Shared finish')
    for loop in ob.data.loops:
        p=ob.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((p.x+.6)/1.2,p.z/2)

def panel(name,fn,material,region,nu=25,nv=9,thickness=.006):
    """Closed sampled shell, with UVs and normals from the broad surface."""
    front=np.array([[fn(i/(nu-1),j/(nv-1)) for i in range(nu)] for j in range(nv)],dtype=float)
    du=np.gradient(front,axis=1);dv=np.gradient(front,axis=0);normals=np.cross(du,dv);normals/=np.maximum(np.linalg.norm(normals,axis=2,keepdims=True),1e-12)
    vertices=np.concatenate([front.reshape(-1,3),(front-normals*thickness).reshape(-1,3)]).tolist();faces=[];count=nu*nv
    for side in [0,1]:
        for j in range(nv-1):
            for i in range(nu-1):
                q=side*count+j*nu+i;f=(q,q+1,q+nu+1,q+nu);faces.append(f if not side else f[::-1])
    perimeter=list(range(nu))+[j*nu+nu-1 for j in range(1,nv)]+list(range(count-2,count-nu-1,-1))+[j*nu for j in range(nv-2,0,-1)]
    for i,a in enumerate(perimeter):
        b=perimeter[(i+1)%len(perimeter)];faces.append((a,a+count,b+count,b))
    ob=mesh(name,vertices,faces,material,region);uv=ob.data.uv_layers.new(name='Panel finish UV')
    for loop in ob.data.loops:
        n=loop.vertex_index%count;uv.data[loop.index].uv=(.02+.96*(n%nu)/(nu-1),.02+.96*(n//nu)/(nv-1))
    return ob

def stud(name,point,material,region,r=.0035):
    n=12;rings=6;cx,cy,cz=point;v=[(cx,cy,cz+r)];f=[]
    for j in range(1,rings):
        t=math.pi*j/rings
        for i in range(n):
            a=math.tau*i/n;v.append((cx+r*math.sin(t)*math.cos(a),cy+r*math.sin(t)*math.sin(a),cz+r*math.cos(t)))
    end=len(v);v.append((cx,cy,cz-r))
    for i in range(n):f.append((0,1+i,1+(i+1)%n))
    for j in range(rings-2):
        for i in range(n):
            a=1+j*n+i;b=1+j*n+(i+1)%n;f.append((a,a+n,b+n,b))
    for i in range(n):f.append((end,1+(rings-2)*n+(i+1)%n,1+(rings-2)*n+i))
    o=mesh(name,v,f,material,region);uv_world(o);return o

def cord(name,points,material,region,r=.0017):
    # Closed mesh tube, avoiding export-time curve tessellation differences.
    points=[Vector(p) for p in points];n=8;v=[];f=[]
    for j,p in enumerate(points):
        tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();a=tangent.cross(Vector((0,0,1)))
        if a.length<.01:a=tangent.cross(Vector((0,1,0)))
        a.normalize();b=tangent.cross(a).normalized()
        for i in range(n):v.append(p+r*(math.cos(math.tau*i/n)*a+math.sin(math.tau*i/n)*b))
    for j in range(len(points)-1):
        for i in range(n):q=j*n+i;s=j*n+(i+1)%n;f.append((q,s,s+n,q+n))
    f.extend([tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+i for i in range(n))])
    ob=mesh(name,v,f,material,region);uv_world(ob);return ob

def material(name,color,rough,metal=0,coat=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;return m

def baked_finish(name,color,rough,metal,out,leather=False):
    """Deterministic embedded 512² color, roughness and tangent-normal tiles."""
    m=material(name,color,rough,metal,.16 if metal==0 and not leather else 0)
    n=512;y,x=np.mgrid[0:n,0:n]/n;rng=np.random.default_rng(1615);noise=rng.random((n,n))
    grain=.5+.16*np.sin(x*math.tau*73)*np.sin(y*math.tau*89)+.2*(noise-.5)
    edge=np.minimum.reduce([x,1-x,y,1-y]);wear=np.clip((.03-edge)/.03,0,1)*(.6+.4*noise)
    rgb=np.array(color)[None,None,:]*(.92+.16*grain[:,:,None]);rgb+=wear[:,:,None]*np.array([.015,.011,.006])
    roughness=np.clip(rough+.08*(grain-.5)+.07*wear,0,1)
    h=(noise-.5)*(.0006 if leather else .00015);dy,dx=np.gradient(h);normal=np.stack([-dx*90,-dy*90,np.ones_like(dx)],axis=2);normal/=np.linalg.norm(normal,axis=2,keepdims=True);normal=normal*.5+.5
    nodes=m.node_tree.nodes;links=m.node_tree.links;shader=nodes.get('Principled BSDF')
    for label,array,space,target in [('color',rgb,'sRGB','Base Color'),('roughness',np.repeat(roughness[:,:,None],3,2),'Non-Color','Roughness'),('normal',normal,'Non-Color',None)]:
        if space=='sRGB':array=np.where(array<=.0031308,array*12.92,1.055*np.maximum(array,0)**(1/2.4)-.055)
        image=bpy.data.images.new(name+' '+label,n,n,alpha=False);image.colorspace_settings.name=space
        rgba=np.concatenate([array,np.ones((n,n,1))],axis=2).astype(np.float32);image.pixels.foreach_set(rgba.ravel());image.filepath_raw=str((out/(name.replace(' ','-')+'-'+label+'.png')).resolve());image.file_format='PNG';image.save();image.pack()
        node=nodes.new('ShaderNodeTexImage');node.image=image
        if target:links.new(node.outputs['Color'],shader.inputs[target])
        else:
            bump=nodes.new('ShaderNodeNormalMap');links.new(node.outputs['Color'],bump.inputs['Color']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    return m
