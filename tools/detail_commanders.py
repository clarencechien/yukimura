"""v16: double the v15 wrist girth and add surface-fitted armour construction.

Reads immutable v15 authoring scenes. Shared detail textures + one extra material
section; all new fittings inherit nearby skin weights and work with GPU animation.
"""
import bpy, math, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gltf_assets import share_images
from refine_commander_physique import smooth, profile
from samurai_rig import point

ROOT=Path(__file__).resolve().parent.parent
STAGE=ROOT/'.tmp/detail-v16';OUT=STAGE/'models';OUT.mkdir(parents=True,exist_ok=True)
LOOK=STAGE/'look';LOOK.mkdir(exist_ok=True)

def image(name,data,path=None):
    im=bpy.data.images.new(name,data.shape[1],data.shape[0],alpha=True)
    im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(data.astype(np.float32).ravel())
    if path:im.filepath_raw=str(path);im.file_format='PNG';im.save()
    im.pack();return im

def textures():
    n=512;y,x=np.mgrid[:n,:n]/(n/2);u=x%1;v=y%1;tile=(x>=1).astype(int)+2*(y>=1)
    h=np.zeros((n,n));rough=np.full((n,n),.68);metal=np.zeros((n,n))
    # Relief is UV-space; geometry carries the large-scale rope and plate shape.
    braid=np.sin((u*28+v*22)*math.tau)*np.sin((u*28-v*22)*math.tau)
    hammered=np.sin(u*math.tau*41+np.sin(v*29))*np.sin(v*math.tau*37+np.sin(u*23))
    engraving=np.exp(-(np.sin((u*4+np.sin(v*math.tau*2)*.1)*math.tau)/.15)**2)
    h[tile==0]=braid[tile==0]*.28;rough[tile==0]=.87
    h[tile==1]=hammered[tile==1]*.09;rough[tile==1]=.51+.08*hammered[tile==1];metal[tile==1]=.65
    h[tile==2]=(-engraving*.25+hammered*.025)[tile==2];rough[tile==2]=(.36+.20*engraving)[tile==2];metal[tile==2]=.78
    h[tile==3]=(hammered*.06)[tile==3];rough[tile==3]=(.35+.09*hammered)[tile==3];metal[tile==3]=.10
    dy,dx=np.gradient(h);norm=np.stack((-dx*2,-dy*2,np.ones_like(h)),axis=-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
    normal=np.ones((n,n,4));normal[:,:,:3]=norm*.5+.5
    orm=np.ones((n,n,4));orm[:,:,1]=rough;orm[:,:,2]=metal
    # Babylon detail map packing: R albedo, G normal Y, B roughness, A normal X.
    for name,cloth in [('forged-detail',False),('woven-detail',True)]:
        yy,xx=np.mgrid[:512,:512]/512
        wave=np.sin(xx*math.tau*47+np.sin(yy*31))*np.sin(yy*math.tau*43)
        surface=(np.sin((xx+yy)*math.tau*64)*np.sin((xx-yy)*math.tau*64)*.09 if cloth else wave*.035)
        dy,dx=np.gradient(surface);d=np.ones((512,512,4))*.5
        d[:,:,0]=.5+surface*(.24 if cloth else .18)
        d[:,:,1]=.5-dy*2;d[:,:,2]=.5+surface*.55;d[:,:,3]=.5-dx*2
        image(name,np.clip(d,0,1),LOOK/(name+'.png'))
    return image('fittings normal',normal),image('fittings surface',orm)

def material(normal,orm):
    m=bpy.data.materials.new('samurai woven cords and fittings');m.use_nodes=True
    ns=m.node_tree.nodes;ls=m.node_tree.links;bs=ns.get('Principled BSDF')
    vc=ns.new('ShaderNodeVertexColor');vc.layer_name='Color';ls.new(vc.outputs['Color'],bs.inputs['Base Color'])
    tex=ns.new('ShaderNodeTexImage');tex.image=orm;s=ns.new('ShaderNodeSeparateColor');ls.new(tex.outputs['Color'],s.inputs[0]);ls.new(s.outputs['Green'],bs.inputs['Roughness']);ls.new(s.outputs['Blue'],bs.inputs['Metallic'])
    tex=ns.new('ShaderNodeTexImage');tex.image=normal;b=ns.new('ShaderNodeNormalMap');b.inputs['Strength'].default_value=.85;ls.new(tex.outputs['Color'],b.inputs['Color']);ls.new(b.outputs['Normal'],bs.inputs['Normal'])
    return m

def wrists(mesh,rig):
    names={g.index:g.name for g in mesh.vertex_groups};before=[v.co.copy() for v in mesh.data.vertices]
    ids={i for p in mesh.data.polygons if p.material_index in (1,2) for i in p.vertices}
    measures={}
    for side in ('L','R'):
        b=rig.data.bones['forearm.'+side];a=b.head_local;axis=b.tail_local-a
        candidates=[]
        for i in ids:
            vertex=mesh.data.vertices[i]
            if not any(names[g.group].endswith('.'+side) and g.weight>.01 for g in vertex.groups):continue
            p=before[i];t=(p-a).dot(axis)/axis.length_squared
            # A real 2x cross-section at the wrist, not a radius parameter hidden
            # by skin-weight blending. The palm heel eases back into the old grip.
            gain=profile(t,[(0,1.08),(.35,1.34),(.70,1.72),(.93,2),(1.07,2),(1.48,1)])
            if t>=1.48:continue
            center=a+axis*t;vertex.co=center+(p-center)*gain
            if .96<t<1.04:candidates.append(((p-center).length,(vertex.co-center).length))
        assert candidates, 'No wrist section to measure'
        ratios=[new/old for old,new in candidates if old>1e-5]
        assert min(ratios)>1.99 and max(ratios)<2.01
        measures[side]={'samples':len(ratios),'min_radius_ratio':min(ratios),'max_radius_ratio':max(ratios),
                        'diameter_before_m':max(x for x,y in candidates)*2,'diameter_after_m':max(y for x,y in candidates)*2}
    mesh.data.update();return measures

class Surface:
    def __init__(self,mesh,group,material_indices=(0,)):
        self.mesh=mesh
        names={g.index:g.name for g in mesh.vertex_groups}
        self.weights=[{names[g.group]:g.weight for g in v.groups} for v in mesh.data.vertices]
        def influence(i):
            return sum(w for n,w in self.weights[i].items() if group(n)) if callable(group) else self.weights[i].get(group,0)
        self.polys=[p for p in mesh.data.polygons if p.material_index in material_indices and
                    sum(influence(i) for i in p.vertices)/len(p.vertices)>.5]
        self.tree=BVHTree.FromPolygons([v.co for v in mesh.data.vertices],[list(p.vertices) for p in self.polys])
    def at(self,p,direction):
        direction=Vector(direction);origin=Vector(p)-direction*1.5
        hit,normal,index,distance=self.tree.ray_cast(origin,direction,3)
        if hit is None:raise ValueError('No armour surface '+str(p))
        poly=self.polys[index];ws={};total=0
        for i in poly.vertices:
            w=1/max((self.mesh.data.vertices[i].co-hit).length,.0001)**2;total+=w
            for n,s in self.weights[i].items():ws[n]=ws.get(n,0)+w*s
        ws=sorted(((n,w/total) for n,w in ws.items()),key=lambda x:-x[1])[:4];total=sum(w for n,w in ws)
        return hit-direction*.0025,{n:w/total for n,w in ws}

class Fittings:
    def __init__(self,kind):self.v=[];self.f=[];self.uv=[];self.w=[];self.roles=[];self.kind=kind;self.pieces=0
    def add(self,verts,faces,uv,weights,role):
        offset=len(self.v);self.v.extend(verts);self.f.extend([tuple(offset+i for i in f) for f in faces]);self.uv.extend(uv);self.w.extend(weights);self.roles.extend([role]*len(verts));self.pieces+=1
    def tube(self,samples,radius,role=0,sides=5):
        verts=[];uv=[];weights=[]
        for i,(p,w) in enumerate(samples):
            tangent=(samples[min(i+1,len(samples)-1)][0]-samples[max(0,i-1)][0]).normalized()
            x=tangent.cross(Vector((0,0,1)))
            if x.length<.01:x=tangent.cross(Vector((0,1,0)))
            x.normalize();y=tangent.cross(x)
            for j in range(sides):
                angle=j*math.tau/sides;verts.append(p+radius*(x*math.cos(angle)+y*math.sin(angle)));uv.append((i/(len(samples)-1),j/sides));weights.append(w)
        faces=[(i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j) for i in range(len(samples)-1) for j in range(sides)]
        self.add(verts,faces,uv,weights,role)
    def eyelet(self,sample,normal,radius=.0038):
        p,w=sample;n=Vector(normal).normalized();x=n.cross(Vector((0,0,1)))
        if x.length<.01:x=n.cross(Vector((0,1,0)))
        x.normalize();y=n.cross(x);verts=[]
        for i in range(8):
            radial=x*math.cos(i*math.tau/8)+y*math.sin(i*math.tau/8)
            for j in range(3):
                a=j*math.tau/3;verts.append(p+radial*(radius+math.cos(a)*.001)+n*math.sin(a)*.001)
        faces=[(i*3+j,((i+1)%8)*3+j,((i+1)%8)*3+(j+1)%3,i*3+(j+1)%3) for i in range(8) for j in range(3)]
        self.add(verts,faces,[(i%3/3,i//3/8) for i in range(24)],[w]*24,2)
    def object(self,mat):
        data=bpy.data.meshes.new('woven fittings');data.from_pydata(self.v,[],self.f);data.update()
        ob=bpy.data.objects.new('woven fittings',data);bpy.context.scene.collection.objects.link(ob);data.materials.append(mat)
        data.uv_layers.new(name='HeroBake');data.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
        # Creating a second CustomData layer reallocates the first layer's RNA.
        uv=data.uv_layers['HeroBake'];ca=data.color_attributes['Color']
        colors=[(.27,.19,.10,1),(.065,.057,.045,1),(.42,.25,.075,1),(.23,.006,.009,1)]
        if self.kind=='ieyasu':colors[0]=(.20,.035,.018,1)
        for loop in data.loops:
            i=loop.vertex_index;role=self.roles[i];u,v=self.uv[i]
            uv.data[loop.index].uv=((role%2+.04+.92*u)/2,(role//2+.04+.92*v)/2);ca.data[loop.index].color=colors[role]
        for i,weights in enumerate(self.w):
            for n,w in weights.items():
                g=ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n);g.add([i],w,'REPLACE')
        for p in data.polygons:p.use_smooth=True
        return ob

def construction(mesh,kind,mat):
    out=Fittings(kind);chest=Surface(mesh,'body.spine02');skipped=[]
    def mapped(surface,points,direction):return [surface.at(p,direction) for p in points]
    def cross(surface,center,dx,dz,direction,radius=.0022):
        samples=[]
        for sign in (-1,1):
            coords=[Vector(center)+Vector((dx*t,0,sign*dz*t)) for t in (-1,0,1)]
            a=mapped(surface,coords,direction);out.tube(a,radius,0,5);samples.append(a[0]);samples.append(a[-1])
        for sample in samples[:2]:out.eyelet(sample,-Vector(direction))
    for z in (1.02,1.125,1.225,1.31):
        for x in (-.23,-.175,-.12,.12,.175,.23):
            try:cross(chest,point(x,0,z),.008,.014,(0,1,0))
            except ValueError as e:skipped.append(str(e))
    for z in (.976,1.073,1.182,1.285,1.348):
        for direction in ((0,1,0),(0,-1,0)):
            try:out.tube(mapped(chest,[point(x,0,z) for x in np.linspace(-.255,.255,19)],direction),.0013,2,5)
            except ValueError as e:skipped.append(str(e))
    # Narrow crossed cords replace the impression of wide rectangular bars.
    # Original straps remain as a recessed dark backing under the added braid.
    for side,sign in [('L',-1),('R',1)]:
        s=Surface(mesh,'body.upperarm01.'+side);direction=(-sign,0,0)
        for row in range(5):
            for u in (-.74,-.25,.25,.74):
                z=1.405-row*.058-.033-.036*u*u;y=u*(.184-row*.003)
                for turn in (-1,1):
                    coords=[point(sign*.5,y+t*.010,z+turn*t*.014) for t in (-1,0,1)]
                    try:
                        a=mapped(s,coords,direction);out.tube(a,.0025,0,5)
                        if turn==1:
                            out.eyelet(a[0],(sign,0,0));out.eyelet(a[-1],(sign,0,0))
                    except ValueError as e:skipped.append(str(e))
        for row in range(5):
            coords=[point(sign*.5,u*(.184-row*.003),1.405-row*.058-.058-.036*u*u) for u in np.linspace(-.9,.9,13)]
            try:out.tube(mapped(s,coords,direction),.0016,2,5)
            except ValueError as e:skipped.append(str(e))
    # Two tailored fabric bands bridge the large wrist and the forearm armour.
    # Ray-fit every sample against the reshaped sleeve; transfer its skin weights.
    rig=mesh.parent
    for side in ('L','R'):
        skin=Surface(mesh,lambda n:n.endswith('.'+side),(1,2))
        bone=rig.data.bones['forearm.'+side];axis=bone.tail_local-bone.head_local;a=bone.head_local
        x=Vector((1,0,0));x=(x-axis*x.dot(axis)/axis.length_squared).normalized();y=axis.normalized().cross(x)
        for lo,hi in ((.59,.67),(.89,.97)):
            rings=[]
            for t in (lo,hi):
                ring=[]
                for i in range(25):
                    n=x*math.cos(i*math.tau/24)+y*math.sin(i*math.tau/24)
                    p,w=skin.at(a+axis*t,-n);ring.append((p+n*.004,w))
                rings.append(ring)
            verts=[p for ring in rings for p,w in ring];weights=[w for ring in rings for p,w in ring]
            uv=[(i/24,j) for j in (0,1) for i in range(25)]
            faces=[(i,i+1,25+i+1,25+i) for i in range(24)]
            # Ensure outward winding for either mirrored limb.
            p0,p1,p2=[verts[j] for j in faces[0][:3]]
            if (p1-p0).cross(p2-p0).dot(x)<0:faces=[tuple(reversed(f)) for f in faces]
            out.add(verts,faces,uv,weights,0)
            for ring in rings:out.tube(ring,.0011,2,4)
    ob=out.object(mat);return ob,{'pieces':out.pieces,'vertices':len(out.v),'missed_paths':skipped}

def run(kind):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-physique.blend'))
    scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    measure=wrists(mesh,rig);normal,orm=textures();mat=material(normal,orm)
    extra,details=construction(mesh,kind,mat)
    extra.data.uv_layers.active.name=mesh.data.uv_layers.active.name
    # Match attributes so joining does not blacken existing baked vertex colours.
    for attr in mesh.data.color_attributes:
        if not extra.data.color_attributes.get(attr.name):
            c=extra.data.color_attributes.new(name=attr.name,type=attr.data_type,domain=attr.domain)
            for value in c.data:value.color=(1,1,1,1)
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);extra.select_set(True);bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join()
    mesh.data.calc_loop_triangles();assert len(mesh.data.loop_triangles)<85000
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-detail.blend'),compress=True)
    target=OUT/f'{kind}.glb';bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    images=share_images(target)
    report={'triangles':len(mesh.data.loop_triangles),'bones':len(rig.data.bones),'source_bones':163,'materials':len(mesh.data.materials),'bytes':target.stat().st_size,'textures':images,'wrists_vs_v15':measure,'fittings':details}
    (STAGE/f'{kind}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

def soldier(kind):
    # Rebuild from the editable source, never from an already detailed runtime.
    from prepare_commander_base import prepare
    base=STAGE/'base';base.mkdir(exist_ok=True)
    snapshot=base/f'{kind}-base.glb'
    prepare(ROOT/'assets/source/samurai-kit.blend',snapshot,base/f'{kind}.sha256')
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(snapshot))
    rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    # glTF import places the NLA strips at frame 1. Keep original clip duration
    # when exporting from time zero instead of introducing an extra idle frame.
    for track in rig.animation_data.nla_tracks:
        strip=track.strips[0];duration=strip.frame_end-strip.frame_start
        strip.frame_start=0;strip.frame_end=duration
    surface=Surface(mesh,'chest');kit=Fittings(kind)
    for z in (1.08,1.20):
        samples=[surface.at(point(x,0,z),(0,1,0)) for x in np.linspace(-.18,.18,9)]
        kit.tube(samples,.0018,2,4)
        for x in (-.16,-.08,.08,.16):
            a=[surface.at(point(x+t*.008,0,z+.035+t*.013),(0,1,0)) for t in (-1,0,1)]
            kit.tube(a,.0028,0,4);kit.eyelet(a[0],(0,-1,0))
    extra=kit.object(mesh.data.materials[0])
    # Reuse the soldier's existing lace/gold atlas tiles: one material/draw call,
    # no extra texture or skeleton on any crowd instance.
    uv=extra.data.uv_layers.active
    for loop in extra.data.loops:
        i=loop.vertex_index;u,v=kit.uv[i];tile=7 if kit.roles[i]==0 else 4
        uv.data[loop.index].uv=((tile%4+.04+.92*u)/4,(tile//4+.04+.92*v)/4)
    for attr in mesh.data.color_attributes:
        if not extra.data.color_attributes.get(attr.name):
            ca=extra.data.color_attributes.new(name=attr.name,type=attr.data_type,domain=attr.domain)
            for item in ca.data:item.color=(1,1,1,1)
    # The imported texture UV name differs from the commander authoring scene.
    extra.data.uv_layers.active.name=mesh.data.uv_layers.active.name
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);extra.select_set(True);bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join()
    mesh.data.calc_loop_triangles();assert len(mesh.data.loop_triangles)<3800
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-detail.blend'),compress=True)
    target=OUT/f'{kind}.glb';bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    images=share_images(target)
    report={'triangles':len(mesh.data.loop_triangles),'bones':len(rig.data.bones),'materials':len(mesh.data.materials),'bytes':target.stat().st_size,'textures':images,'shared_fittings_lod':'crowd','pieces':kit.pieces}
    (STAGE/f'{kind}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    assert all(k in ('yukimura','ieyasu','ashigaru','tokugawa') for k in args)
    for kind in args or ('yukimura','ieyasu','ashigaru','tokugawa'):
        (run if kind in ('yukimura','ieyasu') else soldier)(kind)
