"""CC0 MPFB hand + articulated grip and reusable crimson kote study.

Uses pinned source assets and weights directly; no MPFB addon code is required.
Run with the existing bpy runtime, CLI arguments after --.
"""
import argparse, collections, hashlib, json, math, sys, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'assets/vendor/mpfb'
OUT=ROOT/'renders/open-hand';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--width',type=int,default=1280)
parser.add_argument('--samples',type=int,default=24)
parser.add_argument('--views',default='open,grip')
parser.add_argument('--save',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
for f in json.loads((SRC/'provenance.json').read_text())['files']:
    assert hashlib.sha256((SRC/f['file']).read_bytes()).hexdigest()==f['sha256'],f['file']
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
vertices=[];uvs=[];faces=[];groups=collections.defaultdict(set);group=''
for line in (SRC/'base.obj').read_text().splitlines():
    p=line.split()
    if not p:continue
    if p[0]=='v':vertices.append(Vector((float(p[1])*.1,-float(p[3])*.1,float(p[2])*.1)))
    elif p[0]=='vt':uvs.append(tuple(map(float,p[1:3])))
    elif p[0]=='g':group=p[1]
    elif p[0]=='f':
        ids=[int(t.split('/')[0])-1 for t in p[1:]]
        groups[group].update(ids)
        if group=='body':faces.append((ids,[int(t.split('/')[1])-1 for t in p[1:]]))
rigdef=json.loads((SRC/'rig.default.json').read_text())
weights=json.loads((SRC/'weights.default.json').read_text())['weights']
def joint(d):
    if d['strategy']=='CUBE':ids=groups[d['cube_name']]
    elif d['strategy']=='VERTEX':ids=[d['vertex_index']]
    elif d['strategy']=='MEAN':ids=d['vertex_indices']
    else:raise ValueError(d)
    return sum((vertices[i] for i in ids),Vector())/len(ids)

origin=joint(rigdef['wrist.R']['head'])
y=(joint(rigdef['finger3-1.R']['head'])-origin).normalized()
x=joint(rigdef['finger2-1.R']['head'])-joint(rigdef['finger5-1.R']['head'])
x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized()
canonical=Matrix((x,y,z))
def transform(p):return canonical@(p-origin)
verts=[transform(v) for v in vertices]
names=[n for n in rigdef if n.endswith('.R') and n.startswith(('wrist','finger','metacarpal','lowerarm'))]
influence=collections.defaultdict(float)
for name in names:
    for i,w in weights[name]:influence[i]+=w
chosen=[(ids,uv) for ids,uv in faces if all(influence[i]>.65 and verts[i].y>-.22 for i in ids)]
ids=sorted({i for f,uv in chosen for i in f});remap={i:k for k,i in enumerate(ids)}
mesh=bpy.data.meshes.new('MPFB continuous hand and forearm')
mesh.from_pydata([verts[i] for i in ids],[],[[remap[i] for i in f] for f,uv in chosen]);mesh.update()
hand=bpy.data.objects.new('MPFB right hand — CC0 anatomy base',mesh);scene.collection.objects.link(hand)
uvlayer=mesh.uv_layers.new(name='MPFB original UV')
for poly,(_,uv) in zip(mesh.polygons,chosen):
    poly.use_smooth=True
    for li,ui in zip(poly.loop_indices,uv):uvlayer.data[li].uv=uvs[ui]
rigdata=bpy.data.armatures.new('MPFB hand deformation bones')
rig=bpy.data.objects.new('Open hand rig',rigdata);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name in names:
    d=rigdef[name];b=rigdata.edit_bones.new(name)
    b.head=transform(joint(d['head']));b.tail=transform(joint(d['tail']))
    b.align_roll(Vector((0,0,1)))
for name in names:
    parent=rigdef[name]['parent']
    if parent in names:rigdata.edit_bones[name].parent=rigdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for name in names:
    vg=hand.vertex_groups.new(name=name)
    for i,w in weights[name]:
        if i in remap:vg.add([remap[i]],w/influence[i],'REPLACE')
bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,-.185,0),plane_no=(0,1,0),clear_inner=True)
bm.to_mesh(mesh);bm.free();mesh.update()
hand.parent=rig
mod=hand.modifiers.new('MPFB supplied skin weights','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
sub=hand.modifiers.new('anatomical surface smoothing','SUBSURF');sub.levels=2;sub.render_levels=2
hand['source']='MPFB CC0 base mesh and default skin weights'
hand['source_commit']=json.loads((SRC/'provenance.json').read_text())['commit']

def material(name,color,rough=.7,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
clay=material('neutral anatomical clay',(.40,.43,.44),.78)
hand.data.materials.append(clay)
wood=material('dark spear wood',(.04,.02,.008),.58)
ground=material('studio charcoal',(.024,.031,.039),.87)
def cylinder(name,a,b,r,mat):
    delta=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=delta.length,location=(Vector(a)+Vector(b))/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

# Fit a shared shaft in the palm, then solve each three-bone chain around it.
# MPFB's canonical +Z is the palmar side; flexion must bend towards +Z.
mcp={i:rig.data.bones[f'finger{i}-1.R'].head_local.copy() for i in range(1,6)}
shaft_y=float(np.mean([mcp[i].y for i in range(2,6)]))+.016
shaft_z=.023
shaft_r=.014
shaft_slope=.25
shaft=cylinder('Yari grip — 28 mm diameter',(-.23,shaft_y-.23*shaft_slope,shaft_z),(.23,shaft_y+.23*shaft_slope,shaft_z),shaft_r,wood)
shaft.hide_render=True
def shaft_distance(p):return math.sqrt((p.y-shaft_y-shaft_slope*p.x)**2/(1+shaft_slope**2)+(p.z-shaft_z)**2)
def orient(pb,head,direction):
    bone=pb.bone;old=(bone.tail_local-bone.head_local).normalized()
    rotation=old.rotation_difference(direction.normalized()).to_matrix().to_4x4()
    pb.matrix=Matrix.Translation(head)@rotation@bone.matrix_local.to_3x3().to_4x4()
    bpy.context.view_layer.update()

def finger_points(i,angles):
    points=[mcp[i].copy()];theta=0
    for j,a in enumerate(angles,1):
        theta+=a
        length=rig.data.bones[f'finger{i}-{j}.R'].length
        points.append(points[-1]+Vector((0,math.cos(theta)*length,math.sin(theta)*length)))
    return points

def cost(i,angles):
    pts=finger_points(i,angles);result=0
    target=shaft_r+(.008 if i<5 else .0065)
    for j in range(3):
        for t in (.25,.5,.75,1):
            p=pts[j].lerp(pts[j+1],t)
            d=shaft_distance(p)
            result+=(max(0,target-d)*12)**2
            if j>0:result+=(d-target)**2
    # MCP flexion, PIP and DIP stay in plausible positive bending ranges.
    result+=(pts[-1].z-(shaft_z+.014))**2*.7
    result+=(pts[-1].y-(shaft_y+shaft_slope*pts[-1].x-.012))**2*1.7
    result+=(angles[2]-.66*angles[1])**2*.00003
    return result

solutions={}
for i in range(2,6):
    best=None
    for initial in [(10,60,45),(25,80,55),(5,95,65)]:
        a=[math.radians(v) for v in initial]
        for stepdeg in (12,6,3,1,.3):
            step=math.radians(stepdeg)
            for iteration in range(25):
                improved=False
                for j in range(3):
                    for sign in (-1,1):
                        candidate=a.copy();candidate[j]=max(math.radians([-5,20,15][j]),min(math.radians([75,110,80][j]),candidate[j]+sign*step))
                        if cost(i,candidate)<cost(i,a):a=candidate;improved=True
                if not improved:break
        if best is None or cost(i,a)<best[0]:best=(cost(i,a),a)
    solutions[i]=best[1]

def pose(close):
    for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    if not close:return
    for i in range(2,6):
        pts=finger_points(i,solutions[i])
        for j in range(3):orient(rig.pose.bones[f'finger{i}-{j+1}.R'],pts[j],pts[j+1]-pts[j])
    # Opposed thumb is aimed across the palm; preserve each segment length.
    head=mcp[1].copy()
    targets=[Vector((.050,.049,.025)),Vector((.049,.082,.048)),Vector((.025,shaft_y+.001,shaft_z+.022))]
    for j,target in enumerate(targets,1):
        pb=rig.pose.bones[f'finger1-{j}.R'];orient(pb,head,target-head);head=pb.tail.copy()

pose(False)
for pb in rig.pose.bones:
    pb.rotation_mode='QUATERNION'
    for path in ('location','rotation_quaternion','scale'):pb.keyframe_insert(data_path=path,frame=1)
pose(True)
for pb in rig.pose.bones:
    for path in ('location','rotation_quaternion','scale'):pb.keyframe_insert(data_path=path,frame=24)
scene.frame_start=1;scene.frame_end=24;scene.render.fps=24
scene.frame_set(24);bpy.context.view_layer.update()
evaluated=hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
before_contact=min(shaft_distance(v.co)-shaft_r for v in evaluated.data.vertices)
contact=hand.modifiers.new('grip surface contact correction','SHRINKWRAP')
contact.target=shaft;contact.wrap_method='NEAREST_SURFACEPOINT';contact.wrap_mode='OUTSIDE';contact.offset=.00065
contact.show_render=False;contact.show_viewport=False
contact.keyframe_insert(data_path='show_render',frame=1);contact.keyframe_insert(data_path='show_viewport',frame=1)
contact.show_render=True;contact.show_viewport=True
contact.keyframe_insert(data_path='show_render',frame=24);contact.keyframe_insert(data_path='show_viewport',frame=24)
scene.frame_set(24);bpy.context.view_layer.update()
evaluated=hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
after_contact=min(shaft_distance(v.co)-shaft_r for v in evaluated.data.vertices)
from open_hand_armor import build_armor
armor,leather=build_armor(hand,rig,scene)

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.33,.34,-.38));camera=bpy.context.object;camera.name='anatomy review camera';aim(camera,(0,.025,0));camera.data.type='ORTHO';camera.data.ortho_scale=.46;scene.camera=camera
for name,pos,power,size,color in [('large softbox',(.25,.05,-.5),5,.35,(1,.89,.74)),('cool fill',(-.3,.15,-.23),2,.28,(.67,.80,1)),('edge light',(-.1,-.25,-.3),4,.22,(1,.6,.35)),('palm fill',(.1,.3,.3),3.5,.25,(.8,.88,1))]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;aim(o,(0,0,0))
scene.world=bpy.data.worlds.new('neutral study world');scene.world.color=(.10,.10,.10)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*.8);scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='16' if args.width>=1920 else '8'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.8
report={'source':'MPFB CC0','source_vertices_used':len(ids),'source_faces_used':len(chosen),'bones':len(names),'finger_angles_deg':{i:[round(math.degrees(v),2) for v in a] for i,a in solutions.items()},'shaft_radius_m':shaft_r,'shaft_yz':[shaft_y,shaft_z],'frames':[]}
report['grip_vertex_clearance_m']={'before_contact':before_contact,'after_contact':after_contact}
report['shaft_slope_y_over_x']=shaft_slope
(OUT/'anatomy.json').write_text(json.dumps(report,indent=2)+'\n')
print('HAND_READY '+json.dumps(report),flush=True)
if args.save:
    bpy.context.preferences.filepaths.save_version=0
    scene.frame_set(24);shaft.hide_render=False
    hand.data.materials[0]=leather
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/cinema/open-hand-study.blend'),compress=True)
for view in args.views.split(','):
    close=view!='open';scene.frame_set(24 if close else 1);shaft.hide_render=not close
    beauty=view.startswith('beauty')
    for o in armor:o.hide_render=not beauty
    hand.data.materials[0]=leather if beauty else clay
    camera.location=(.25,.25,.35) if 'palm' in view else (.33,.34,-.38)
    aim(camera,(0,.025,0))
    scene.render.filepath=str(OUT/f'{view}-{args.width}.png');before=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    report['frames'].append({'view':view,'file':Path(scene.render.filepath).name,'seconds':round(time.perf_counter()-before,2)})
    (OUT/f'render-{args.width}.json').write_text(json.dumps(report,indent=2)+'\n')
