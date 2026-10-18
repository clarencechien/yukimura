"""Offline orthographic sprite proof; never writes live game assets.

Blender 4.3: blender -b -t 4 --python-exit-code 1 --python tools/render_jigoku_study.py -- --draft
Final: omit --draft. CPU Cycles; shared camera/pivot across all poses.
"""
import argparse, hashlib, json, math, random, sys, time
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--draft',action='store_true')
parser.add_argument('--poses',default='ready,windup,strike')
parser.add_argument('--samples',type=int,default=128)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=ROOT/('.tmp/jigoku-2d/draft' if args.draft else 'docs/routes/jigoku-2d/renders')
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'assets/optimized/commanders/yukimura-grip-study.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
rig=next(o for o in scene.objects if o.type=='ARMATURE')
hero=next(o for o in scene.objects if o.type=='MESH')
hero.hide_render=False;hero.hide_set(False)
tracks={t.name:t for t in rig.animation_data.nla_tracks}
POSES={'ready':('idle',0),'windup':('thrust',20),'strike':('thrust',40)}
rng=random.Random(1615)

def pose(name):
    clip,frame=POSES[name]
    rig.animation_data.action=None
    for t in tracks.values():t.mute=t.name!=clip;t.is_solo=False
    scene.frame_set(frame);bpy.context.view_layer.update()

def mat(name,c1,c2,rough=.7,metal=0,scale=8,bump_distance=.003):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
    coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*c1,1);ramp.color_ramp.elements[1].color=(*c2,1)
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=bump_distance
    l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m

def box(name,loc,size,material,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    if bevel:
        b=o.modifiers.new('worn edge','BEVEL');b.width=bevel;b.segments=3
        b=o.modifiers.new('weighted plate normals','WEIGHTED_NORMAL')
    return o

def rod(name,start,end,r,material,vertices=12):
    delta=Vector(end)-Vector(start)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=delta.length,location=(Vector(start)+Vector(end))/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
    b=o.modifiers.new('rounded end','BEVEL');b.width=.003;b.segments=2
    return o

# Refine offline shaders only. Keep source UVs, baked normals and the exact rig.
for m in hero.data.materials:
    if not m or not m.use_nodes:continue
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    if 'runtime/' in m.name:
        base=p.inputs['Base Color'].links[0].from_socket
        split=n.new('ShaderNodeSeparateColor');l.new(base,split.inputs[0])
        diff=n.new('ShaderNodeMath');diff.operation='SUBTRACT';l.new(split.outputs[0],diff.inputs[0]);l.new(split.outputs[1],diff.inputs[1])
        mask=n.new('ShaderNodeMapRange');mask.clamp=True;mask.inputs['From Min'].default_value=.04;mask.inputs['From Max'].default_value=.19;mask.inputs['To Max'].default_value=.62;l.new(diff.outputs[0],mask.inputs[0]);l.new(mask.outputs[0],p.inputs['Coat Weight'])
        p.inputs['Coat Roughness'].default_value=.24
        # Small-scale lacquer microrelief, not extra topology or a sculpt claim.
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=210;noise.inputs['Detail'].default_value=2
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.1;bump.inputs['Distance'].default_value=.00035
        if p.inputs['Normal'].is_linked:l.new(p.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
        l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    elif 'deerskin' in m.name:
        p.inputs['Base Color'].default_value=(.018,.024,.03,1);p.inputs['Roughness'].default_value=.83
        wave=n.new('ShaderNodeTexNoise');wave.inputs['Scale'].default_value=340;wave.inputs['Detail'].default_value=2
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.0006;l.new(wave.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    elif 'fitted crimson' in m.name:
        p.inputs['Base Color'].default_value=(.18,.008,.014,1);p.inputs['Roughness'].default_value=.35;p.inputs['Metallic'].default_value=.2;p.inputs['Coat Weight'].default_value=.45

# Reusable 4 m stage. No generated concept image is used as geometry or texture.
objects_before=set(scene.objects)
stone=[mat('basalt wet '+str(i),(.018+i*.003,.024+i*.003,.027+i*.003),(.085,.098,.105),.34+i*.035,scale=12,bump_distance=.012) for i in range(4)]
mud=mat('ash between stones',(.012,.011,.01),(.065,.06,.052),.88,scale=40,bump_distance=.009)
ash=mat('soft pale ash',(.14,.14,.13),(.32,.32,.29),.95,scale=50,bump_distance=.003)
wood=mat('charred timber',(.007,.005,.004),(.055,.031,.018),.57,scale=7,bump_distance=.008)
iron=mat('forged black iron',(.008,.012,.014),(.042,.05,.055),.4,.75,scale=30,bump_distance=.001)
roof=mat('smoke darkened roof tiles',(.018,.026,.033),(.065,.08,.09),.56,scale=22,bump_distance=.004)
red=mat('weathered oxblood banner',(.065,.003,.006),(.2,.009,.013),.9,scale=36,bump_distance=.001)
gold=mat('aged brass',(.19,.105,.025),(.46,.29,.075),.44,.65,scale=18,bump_distance=.001)
box('4 m ground foundation',(0,0,-.105),(4,4,.18),mud)
for row in range(8):
    for col in range(8):
        x=-1.75+col*.5+rng.uniform(-.012,.012);y=-1.75+row*.5+rng.uniform(-.014,.014)
        o=box('wet basalt sett', (x,y,-.025+rng.uniform(-.006,.006)),(.473+rng.uniform(-.015,.01),.468,.07),rng.choice(stone),.027)
        o.rotation_euler.z=rng.uniform(-.028,.028)
# Ash along sheltered stage edges and small chips: geometry, with a clear lane.
for i in range(95):
    x=rng.uniform(-1.95,1.95);y=rng.uniform(-1.95,1.95)
    if abs(x)<1.35 and abs(y)<1.25:continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,.014))
    o=bpy.context.object;o.name='ash and broken stone';o.scale=(rng.uniform(.02,.07),rng.uniform(.02,.08),rng.uniform(.005,.022));o.data.materials.append(ash if i%3 else stone[0])
# Gate corner at the back, leaving the foreground and spear travel unobstructed.
for x in (-1.65,1.65):
    box('gate footing',(x,1.75,.18),(.47,.44,.38),stone[2],.035)
    box('burned gate post',(x,1.75,1.15),(.23,.25,2.05),wood,.02)
    for z in (.4,1.7):box('iron post band',(x,1.75,z),(.248,.268,.07),iron,.006)
box('gate lintel',(0,1.75,2.11),(3.8,.32,.24),wood,.025)
# Curved tiled roof: complete overlapping surfaces, not separated cylinders.
for side in (-1,1):
    for tile in range(18):
        verts=[];faces=[]
        for j in range(9):
            t=j/8;y=1.75+side*t*.64;z=2.62-.50*t+.16*t*t
            for k in range(5):
                u=k/4;x=-1.98+tile*.22+u*.225
                verts.append((x,y,z+.022*math.cos((u-.5)*math.tau)))
        for j in range(8):
            for k in range(4):
                v=j*5+k;faces.append((v,v+1,v+6,v+5))
        me=bpy.data.meshes.new('curved roof tile');me.from_pydata(verts,[],faces);me.update()
        ob=bpy.data.objects.new('overlapping kawara',me);scene.collection.objects.link(ob);me.materials.append(roof)
        sol=ob.modifiers.new('fired clay thickness','SOLIDIFY');sol.thickness=.018
        be=ob.modifiers.new('soft tile edge','BEVEL');be.width=.004;be.segments=2
    box('eave timber',(0,1.75+side*.61,2.23),(4.02,.09,.10),wood,.012)
box('roof ridge',(0,1.75,2.65),(4.04,.13,.12),roof,.022)
# Hanging battle cloth, small enough to remain a supporting scene element.
verts=[];faces=[]
for j in range(13):
    for i in range(6):
        x=-1.4+i*.09;z=2-j*.088
        verts.append((x,1.56+.022*math.sin(i*1.7+j*.5),z-(.03*math.sin(i*3) if j==12 else 0)))
for j in range(12):
    for i in range(5):
        k=j*6+i;faces.append((k,k+1,k+7,k+6))
mesh=bpy.data.meshes.new('cloth grid');mesh.from_pydata(verts,[],faces);mesh.update();flag=bpy.data.objects.new('six coin battle cloth',mesh);scene.collection.objects.link(flag);mesh.materials.append(red)
for row in range(2):
    for col in range(3):
        x=-1.32+col*.14;z=1.8-row*.14
        bpy.ops.mesh.primitive_torus_add(major_radius=.042,minor_radius=.01,major_segments=16,minor_segments=6,location=(x,1.52,z),rotation=(math.pi/2,0,0));bpy.context.object.name='coin banner applique';bpy.context.object.data.materials.append(gold)
stage=[o for o in scene.objects if o not in objects_before]

# One camera and one world light rig for every shot; no per-frame composition fixes.
world=bpy.data.worlds.new('jigoku neutral cold ambient');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.17,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.34

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,energy,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1))
light('warm diffuse key',(-3,-4,6),650,(1,.76,.55),4)
light('cool soft fill',(4,-2,3),230,(.52,.69,1),4)
light('spirit rim',(1,3,4),500,(.3,.68,.78),3)
bpy.ops.object.camera_add(location=(6,-6,7))
cam=bpy.context.object;cam.name='fixed isometric camera';aim(cam,(0,0,1));cam.data.type='ORTHO';cam.data.ortho_scale=5.5;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12 if args.draft else args.samples
scene.cycles.use_denoising=False;scene.cycles.adaptive_threshold=.06 if args.draft else .025
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.film_transparent=True;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.resolution_x=scene.render.resolution_y=512 if args.draft else 1024
# Pose-union camera fit includes the entire spear, horn, feet and trailing cloth.
all_points=[]
for name in POSES:
    pose(name);deps=bpy.context.evaluated_depsgraph_get();ev=hero.evaluated_get(deps)
    all_points.extend(ev.matrix_world@v.co for v in ev.data.vertices)
# Fit the union once, then reuse this exact framing for all three sprites.
cam.data.ortho_scale=5.5
projected=[world_to_camera_view(scene,cam,p) for p in all_points]
xmin=min(p.x for p in projected);xmax=max(p.x for p in projected);ymin=min(p.y for p in projected);ymax=max(p.y for p in projected)
right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0))
cam.location+=right*((xmin+xmax)/2-.5)*5.5+up*((ymin+ymax)/2-.5)*5.5
cam.data.ortho_scale=max(xmax-xmin,ymax-ymin)*5.5/.86
sprite_scale=cam.data.ortho_scale;sprite_location=cam.location.copy()
stage_location=Vector((6,-6,7));stage_scale=6.8
report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'engine':'Cycles','device':'CPU','threads':4,'samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,'draft':args.draft,'camera':{'type':'ORTHO','location':list(cam.location),'rotation':list(cam.rotation_euler),'scale':sprite_scale,'stage_location':list(stage_location),'stage_scale':stage_scale,'elevation_degrees':35.264389682754654},'mesh_vertices':len(hero.data.vertices),'triangles':sum(len(p.vertices)-2 for p in hero.data.polygons),'bones':len(rig.data.bones),'poses':[],'files':[],'limitations':['Existing v22 geometry/pose reused; no new high-poly character sculpt.','Three sampled key poses are not a completed animation.','The isolated sprite hides stage geometry; stage shadows are not exported as a separate layer in this proof.']}
scene.render.resolution_x=scene.render.resolution_y=512 if args.draft else 1024
pivot=world_to_camera_view(scene,cam,Vector((0,0,0)));report['pivot_normalized_top_left']=[pivot.x,1-pivot.y]
for name in args.poses.split(','):
    cam.location=sprite_location;cam.data.ortho_scale=sprite_scale
    pose(name);clip,frame=POSES[name]
    ev=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());points=[world_to_camera_view(scene,cam,ev.matrix_world@v.co) for v in ev.data.vertices]
    bounds=[min(v.x for v in points),1-max(v.y for v in points),max(v.x for v in points),1-min(v.y for v in points)]
    report['poses'].append({'name':name,'clip':clip,'source_frame':frame,'normalized_bounds':bounds})
    for mode in (['stage'] if args.draft else ['sprite','stage']):
        cam.location=sprite_location if mode=='sprite' else stage_location
        cam.data.ortho_scale=sprite_scale if mode=='sprite' else stage_scale
        for o in stage:o.hide_render=mode=='sprite'
        for resolution in ([512] if args.draft else ([1024,512] if mode=='sprite' else [1024])):
            scene.render.resolution_x=scene.render.resolution_y=resolution
            target=OUT/f'{name}-{mode}-{resolution}.png';scene.render.filepath=str(target)
            started=time.perf_counter();print('JIGOKU_RENDER',name,mode,resolution,flush=True);bpy.ops.render.render(write_still=True)
            report['files'].append({'path':target.name,'width':resolution,'height':resolution,'pose':name,'mode':mode,'camera_scale':cam.data.ortho_scale,'camera_location':list(cam.location),'seconds':round(time.perf_counter()-started,3),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
            (OUT/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
if not args.draft:
    for o in stage:o.hide_render=False
    cam.location=stage_location;cam.data.ortho_scale=stage_scale
    pose('ready');scene.render.resolution_x=scene.render.resolution_y=1024
    bpy.context.preferences.filepaths.save_version=0
    target=ROOT/'assets/optimized/jigoku-2d';target.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(OUT/'ready-stage-1024.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(target/'yukimura-sprite-study.blend'),compress=True)
    report['editable_scene']=str((target/'yukimura-sprite-study.blend').relative_to(ROOT))
    report['editable_scene_sha256']=hashlib.sha256((target/'yukimura-sprite-study.blend').read_bytes()).hexdigest()
    (OUT/'render-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('JIGOKU_DONE',OUT,flush=True)
