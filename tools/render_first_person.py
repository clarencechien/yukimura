"""Actual Cycles POV look development. Run with Blender 4.3 and -- args.

Reuses editable sculpt masters and authored weapon/arm poses. No image generation,
no changes to game assets. Three blocking poses, not a finished animation.
"""
import bpy, math, random, time, json, argparse, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from samurai_rig import bone_for_part
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--width',type=int,default=1280)
parser.add_argument('--samples',type=int,default=24)
parser.add_argument('--frames',default='1,120,240')
parser.add_argument('--output',default=str(ROOT/'renders/first-person'))
parser.add_argument('--save-scene',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=Path(args.output);OUT.mkdir(parents=True,exist_ok=True)
started=time.perf_counter();random.seed(1614)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/source/samurai-kit.blend'))
print('CINEMA_BUILD source loaded',flush=True)
scene=bpy.context.scene
for layer in bpy.context.view_layer.layer_collection.children:layer.exclude=False
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
for o in scene.objects:o.hide_render=True;o.hide_set(False)

def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def material(name,color,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
def mesh(name,vertices,faces,mat):
    d=bpy.data.meshes.new(name);d.from_pydata(vertices,[],faces);d.update()
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.data.materials.append(mat);return o
def box(name,pos,scale,mat,bevel=0):
    v=[(x*scale[0]/2,y*scale[1]/2,z*scale[2]/2) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    o=mesh(name,v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    o.location=pos
    if bevel:
        mod=o.modifiers.new('soft weathered edge','BEVEL');mod.width=bevel;mod.segments=2
    return o
def rod(name,a,b,r,mat,tip=None,sides=8):
    delta=Vector(b)-Vector(a);q=delta.to_track_quat('Z','Y');v=[]
    for center,radius in [(a,r),(b,r if tip is None else tip)]:
        for i in range(sides):
            angle=i*math.tau/sides;v.append(Vector(center)+q@Vector((radius*math.cos(angle),radius*math.sin(angle),0)))
    f=[tuple(range(sides-1,-1,-1)),tuple(range(sides,sides*2))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    return mesh(name,v,f,mat)
def surface(name,c1,c2,scale=4,rough=.8,metal=0):
    m=material(name,c1,rough,metal);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=4;tex.inputs['Roughness'].default_value=.72
    coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],tex.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*c1,1);ramp.color_ramp.elements[1].color=(*c2,1)
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.36;bump.inputs['Distance'].default_value=.028 if name=='old stone' else .007
    l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m

# Evaluate the original rig at authored poses and rigidly attach sculpted plates.
# Hands, forearms, weapon and armour keep the actual high-poly geometry/shaders.
def sculpt_actor(kind):
    rig=bpy.data.objects[kind+'_Rig'];rig.location=(0,0,0)
    tracks={t.name:t for t in rig.animation_data.nla_tracks}
    coll=next(c for c in bpy.data.collections if c.name.startswith('20_'+kind.upper()+'_HIGH'))
    objects=[]
    for o in coll.objects:
        name=o['part_name']
        if kind=='yukimura' and bone_for_part(name) not in ('hand.L','hand.R','weapon'):continue
        o.hide_render=False;o.hide_set(False);objects.append(o)
        if kind=='yukimura' and name.startswith(('glove.hero.','finger.hero.','forearm.hero.underlay.')) and 'plate' not in name:
            mod=o.modifiers.new('cinematic rounded glove seams','SUBSURF');mod.levels=1;mod.render_levels=1
        # Lacquer is physically distinct from textile; no metallic red cloth.
        for m in o.data.materials:
            p=m.node_tree.nodes.get('Principled BSDF')
            if o['palette_role']=='armor':
                p.inputs['Coat Weight'].default_value=.55;p.inputs['Coat Roughness'].default_value=.22
    return rig,tracks,objects
hero=sculpt_actor('yukimura');boss=sculpt_actor('ieyasu')
for layer in bpy.context.view_layer.layer_collection.children:
    if layer.name.startswith('20_'):layer.exclude=True
print('CINEMA_BUILD sculpt masters ready',flush=True)
def pose_actor(actor,clip,frame,position=(0,0,0),yaw=0,scale=1):
    rig,tracks,objects=actor
    rig.animation_data.action=None
    for name,track in tracks.items():track.mute=name!=clip;track.is_solo=False
    scene.frame_set(frame);bpy.context.view_layer.update()
    world=Matrix.Translation(position)@Matrix.Rotation(yaw,4,'Z')@Matrix.Scale(scale,4)
    transforms=[]
    for o in objects:
        bone=rig.pose.bones[bone_for_part(o['part_name'])]
        transforms.append((o,world@bone.matrix@bone.bone.matrix_local.inverted()))
    return transforms

# Linked skinned low-detail troops form the mid/far field, never near-camera heroes.
troop=bpy.data.objects['tokugawa_runtime'];troop_rig=troop.parent
troop_rig.location=(0,0,0);troop_rig.animation_data.action=None
for track in troop_rig.animation_data.nla_tracks:track.mute=track.name!='thrust'
scene.frame_set(8);bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get();troop_data=bpy.data.meshes.new_from_object(troop.evaluated_get(deps))
troops=[]
for row in range(5):
    for col in range(13):
        x=(col-6)*2.1+random.uniform(-.4,.4);y=-26-row*3.2+random.uniform(-.5,.5)
        if abs(x)<2.6:continue
        o=bpy.data.objects.new('Tokugawa formation',troop_data);scene.collection.objects.link(o)
        o.location=(x,y,.04);o.rotation_euler.z=math.pi+random.uniform(-.12,.12);troops.append(o)
print('CINEMA_BUILD linked army ready',flush=True)

snow=surface('wind packed snow',(.26,.32,.38),(.70,.77,.82),20,.78)
stone=surface('old stone',(.025,.036,.045),(.16,.19,.21),5,.88)
wood=surface('charred wet timber',(.012,.008,.006),(.080,.039,.016),8,.53)
gold=material('old banner gold',(.52,.29,.055),.54,.5)
red=surface('oxblood battle banners',(.085,.003,.007),(.27,.012,.018),38,.9)
black=surface('Tokugawa banner black',(.005,.009,.013),(.025,.032,.034),38,.88)
plaster=surface('weathered castle plaster',(.13,.15,.15),(.38,.39,.33),3,.92)
roofmat=surface('winter roof tiles',(.018,.027,.038),(.09,.12,.15),12,.59)
mud=surface('wet churned earth',(.009,.007,.005),(.055,.035,.022),11,.58)
packed=surface('compressed boot impressions',(.020,.019,.016),(.060,.065,.066),18,.73)

# POV-only sleeves connect the inherited sculpted hands to off-screen shoulders.
# Their two segments are posed per shot; game geometry and its rig stay unchanged.
leather=surface('POV indigo woven sleeve',(.008,.012,.018),(.038,.046,.058),180,.86)
lacquer=surface('POV crimson kote',(.14,.004,.007),(.28,.010,.015),180,.37,.10)
for m,distance in [(leather,.0005),(lacquer,.0008)]:
    for node in m.node_tree.nodes:
        if node.type=='BUMP':node.inputs['Distance'].default_value=distance;node.inputs['Strength'].default_value=.24
lacquer.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.65
lacquer.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.19
def sleeve(name,r0,r1):
    v=[];f=[]
    for j in range(21):
        z=j/20
        for i in range(32):
            a=i*math.tau/32;r=(r0*(1-z)+r1*z)*(1+.055*math.sin(z*38+a*3))
            v.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(20):
        for i in range(32):a=j*32+i;b=j*32+(i+1)%32;f.append((a,b,b+32,a+32))
    o=mesh(name,v,f,leather)
    for p in o.data.polygons:p.use_smooth=True
    return o
pov_arms={}
for side in ('L','R'):
    upper=sleeve('POV upper sleeve '+side,.095,.080);fore=sleeve('POV forearm sleeve '+side,.080,.056)
    for strip in range(5):
        v=[];f=[]
        for j in range(13):
            z=.12+j/12*.80;r=.085*(1-z)+.065*z
            for i in range(7):
                a=strip*math.tau/5+(i/6-.5)*.85;v.append((r*math.cos(a),r*math.sin(a),z))
        for j in range(12):
            for i in range(6):a=j*7+i;f.append((a,a+1,a+8,a+7))
        plate=mesh('curved red kote splint',v,f,lacquer);plate.parent=fore
        for p in plate.data.polygons:p.use_smooth=True
        mod=plate.modifiers.new('forged splint thickness','SOLIDIFY');mod.thickness=.003
        mod=plate.modifiers.new('worn splint edge','BEVEL');mod.width=.002;mod.segments=2
    for z in (.16,.82):
        for i in range(24):
            a=i*math.tau/24;b=(i+1)*math.tau/24;r=.09*(1-z)+.066*z
            tie=rod('gold kote binding',(r*math.cos(a),r*math.sin(a),z),(r*math.cos(b),r*math.sin(b),z),.002,gold,sides=5);tie.parent=fore
    pov_arms[side]=(upper,fore)
def connect(segment,start,end,frame):
    segment.location=start;delta=Vector(end)-Vector(start);segment.rotation_euler=delta.to_track_quat('Z','Y').to_euler();segment.scale=(1,1,delta.length)
    for path in ('location','rotation_euler','scale'):segment.keyframe_insert(data_path=path,frame=frame)

def height(x,y):
    road=math.exp(-((x-.4*math.sin(y*.24))/3.0)**4)
    return .12*(1-road)+.018*math.sin(x*3.2+y)*math.cos(y*4.7)+.025*math.sin(x*.8+y*.45)

# Continuous shader mask instead of polygon material boundaries.
terrain=material('continuous thawed snow',(.2,.23,.26),.8)
n=terrain.node_tree.nodes;l=terrain.node_tree.links;p=n.get('Principled BSDF')
position=n.new('ShaderNodeNewGeometry');xyz=n.new('ShaderNodeSeparateXYZ');l.new(position.outputs['Position'],xyz.inputs[0])
edge_noise=n.new('ShaderNodeTexNoise');edge_noise.inputs['Scale'].default_value=1.65;edge_noise.inputs['Detail'].default_value=4;l.new(position.outputs['Position'],edge_noise.inputs['Vector'])
def math_node(operation,a,b):
    node=n.new('ShaderNodeMath');node.operation=operation
    for i,v in enumerate((a,b)):
        if isinstance(v,(int,float)):node.inputs[i].default_value=v
        else:l.new(v,node.inputs[i])
    return node.outputs[0]
warp=math_node('MULTIPLY_ADD',edge_noise.outputs['Fac'],2.0)
# MULTIPLY_ADD defaults its third input to .5; explicitly centre this noise.
n[-1].inputs[2].default_value=-1
edge=math_node('ABSOLUTE',math_node('ADD',xyz.outputs['X'],warp),0)
mask=n.new('ShaderNodeMapRange');mask.interpolation_type='SMOOTHSTEP';mask.inputs['From Min'].default_value=1.95;mask.inputs['From Max'].default_value=3.30;l.new(edge,mask.inputs[0])
pigment=n.new('ShaderNodeMixRGB');pigment.inputs[1].default_value=(.013,.011,.009,1);pigment.inputs[2].default_value=(.52,.61,.67,1);l.new(mask.outputs[0],pigment.inputs[0]);l.new(pigment.outputs[0],p.inputs['Base Color'])
rough=math_node('MULTIPLY_ADD',mask.outputs[0],.30);n[-1].inputs[2].default_value=.55;l.new(rough,p.inputs['Roughness'])
fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=45;fine.inputs['Detail'].default_value=3;l.new(position.outputs['Position'],fine.inputs['Vector'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=.015;l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])

# True uneven ground, road depressions and snow accumulation; centimetre relief.
verts=[];faces=[];nx=220;ny=340
for j in range(ny+1):
    y=10-j*.36
    for i in range(nx+1):
        x=(i-nx/2)*.36
        verts.append((x,y,height(x,y)))
for j in range(ny):
    for i in range(nx):
        a=j*(nx+1)+i;faces.append((a,a+nx+1,a+nx+2,a+1))
ground=mesh('snow broken by a muddy approach',verts,faces,terrain)
for p in ground.data.polygons:
    p.use_smooth=True
# Foot impressions, broken clods and icy puddles are actual geometry.
for i in range(200):
    y=random.uniform(-48,2);x=random.choice([-1,1])*random.uniform(.35,1.9)
    angle=random.uniform(-.4,.4);v=[]
    for k in range(18):
        a=k*math.tau/18;dx=.08*math.cos(a);dy=.17*math.sin(a)
        xx=x+dx*math.cos(angle)-dy*math.sin(angle);yy=y+dx*math.sin(angle)+dy*math.cos(angle)
        v.append((xx,yy,height(xx,yy)+.0015))
    mesh('boot pressed into slush',v,[tuple(range(18))],packed)
for i in range(130):
    x=random.uniform(-10,10);y=random.uniform(-55,0)
    if abs(x)<1.2:continue
    r=random.uniform(.04,.15)
    mesh('frozen clod',[(x+r,y,.04),(x-r,y,.04),(x,y+r,.04),(x,y-r,.04),(x,y,.04+r*.4),(x,y,.01)],[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)],stone)

def banner(x,y,color,crest=False):
    rod('sashimono mast',(x,y,0),(x,y,4.7),.045,wood)
    rod('cross pole',(x,y,4.58),(x+1.1,y,4.58),.025,wood)
    v=[];f=[]
    for j in range(13):
        for i in range(9):
            u=i/8;t=j/12
            v.append((x+u,y+.16*math.sin(u*5+t*5)+t*.22,4.55-t*2.6))
    for j in range(12):
        for i in range(8):a=j*9+i;f.append((a,a+1,a+10,a+9))
    o=mesh('wind swept banner',v,f,color)
    for p in o.data.polygons:p.use_smooth=True
    if crest:
        for ix in range(3):
            for iz in range(2):
                vv=[];ff=[]
                for a in range(16):
                    for b in range(5):
                        u=a*math.tau/16;v=b*math.tau/5;r=.09+.016*math.cos(v)
                        vv.append((x+.23+ix*.25+r*math.cos(u),y-.23-.016*math.sin(v),3.68+iz*.27+r*math.sin(u)))
                for a in range(16):
                    for b in range(5):ff.append((a*5+b,((a+1)%16)*5+b,((a+1)%16)*5+(b+1)%5,a*5+(b+1)%5))
                mesh('six coins crest',vv,ff,gold)
print('CINEMA_BUILD terrain ready',flush=True)
for y in [-6,-15,-24,-35,-46]:
    for side in [-1,1]:banner(side*(5.8 if y>-24 else 10),y,red if y>-20 else black,y>-20)
for side in [-1,1]:
    for y in range(-10,-42,-3):
        x=side*8
        for k in range(3):rod('splintered defensive stake',(x+k*.5,y,0),(x+k*.5,y+.8,1.6+random.random()*.4),.10,wood,tip=.015)
        rod('lashed cross brace',(x-.4,y+.3,.85),(x+1.5,y+.3,.85),.065,wood)

# Distant Osaka-inspired layered keep: a cinematic setting, not surveyed geometry.
for tier in range(5):
    z=5+tier*3.1;w=17-tier*2.6;d=13-tier*1.7
    box('keep plaster storey',(0,-61,z+1.1),(w,d,2.6),plaster,.08)
    for side in [-1,1]:
        vv=[];ff=[]
        for j in range(7):
            t=j/6
            for i in range(19):
                u=i/18*2-1;vv.append((u*w*(.43+.19*t),-61+side*d*.66*t,z+4.0-2*t+.65*t**4+.32*abs(u)**5*t))
        for j in range(6):
            for i in range(18):a=j*19+i;ff.append((a,a+1,a+20,a+19))
        roof=mesh('snow heavy curved eave',vv,ff,roofmat)
        so=roof.modifiers.new('solid roof','SOLIDIFY');so.thickness=.15
        for k in range(21):
            x=(k/20-.5)*w*1.2
            rod('snowy eave edge',(x,-61+side*d*.66,z+2.70),(x+w*.03,-61+side*d*.66,z+2.70),.035,snow)
    for x in [-w*.46,0,w*.46]:box('keep dark pillar',(x,-61-d/2-.015,z+1),( .15,.13,2.4),wood)
    for i in range(max(3,int(w/1.8))):
        x=(i-(max(3,int(w/1.8))-1)/2)*1.7
        box('keep arrow window',(x,-61+d/2+.03,z+1.2),(.55,.06,1.1),wood,.025)
for row in range(4):
    for col in range(18):
        box('rough castle foundation',((col-8.5)*1.7+(row%2)*.5,-52,1+row*.85),(1.58,2,.8),stone,.08)

# Fire has warm physical light, ember geometry and restrained emission.
flame=material('embers',(.25,.022,.003),.5);p=flame.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.10,.005,1);p.inputs['Emission Strength'].default_value=2
for x,y in [(-4,-8),(4,-19),(-7,-32),(7,-39)]:
    for k in range(4):rod('burning fallen beam',(x-.6,y+k*.12,.1),(x+.6,y+.2+k*.12,.25),.08,wood)
    for k in range(12):
        px=x+random.uniform(-.4,.4);py=y+random.uniform(-.3,.3)
        rod('glowing wood fissure',(px,py,.22),(px+.12,py,.24),random.uniform(.01,.025),flame,tip=.005,sides=7)
    bpy.ops.object.light_add(type='POINT',location=(x,y,1));o=bpy.context.object;o.name='firelight';o.data.energy=330;o.data.color=(1,.23,.045);o.data.shadow_soft_size=1.2

# Localised distant haze leaves the close red armour crisp.
fog=bpy.data.materials.new('cold battlefield haze');fog.use_nodes=True;n=fog.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');volume=n.new('ShaderNodeVolumePrincipled');volume.inputs['Density'].default_value=.018;volume.inputs['Color'].default_value=(.50,.59,.66,1);volume.inputs['Anisotropy'].default_value=.25;fog.node_tree.links.new(volume.outputs['Volume'],out.inputs['Volume'])
box('distant battlefield mist',(0,-56,10),(130,70,25),fog)
flake=material('snow crystals',(.70,.79,.86),.5)
# Small clustered flakes, larger and sparse in the foreground; deterministic.
v=[];f=[]
for i in range(1700):
    x=random.uniform(-18,18);y=random.uniform(-55,1);z=random.uniform(.2,8);r=random.uniform(.003,.010)
    a=len(v);v.extend([(x-r,y,z),(x+r,y,z),(x,y-.004,z+r),(x,y+.004,z-r)]);f.extend([(a,a+1,a+2),(a,a+3,a+1)])
mesh('falling snow',v,f,flake)

scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.16,.22,.30,1);bg.inputs[1].default_value=.32
for name,pos,target,power,color,size in [
    ('cold sky opening',(-8,-18,14),(0,-12,0),2400,(.62,.76,1),12),
    ('low winter sun',(8,-32,13),(0,-17,1),1500,(1,.74,.43),8),
    ('near armour softbox',(-3,-3,4),(0,-1,1.4),250,(1,.68,.42),4),
    ('boss rim',(2,-28,7),(0,-24,2),800,(1,.71,.36),4)]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,target)
bpy.ops.object.light_add(type='SUN',location=(0,0,15));sun=bpy.context.object;sun.rotation_euler=(.55,-.4,-.4);sun.data.energy=1.2;sun.data.angle=.20;sun.data.color=(.70,.80,1)

bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='Yukimura eyes — POV';scene.camera=camera
camera.data.lens=25;camera.data.sensor_width=36;camera.data.clip_start=.035
camera.data.dof.use_dof=True;camera.data.dof.aperture_fstop=7.1
print('CINEMA_BUILD environment ready',flush=True)
shots={1:('ready',0,'idle',0,(0,.08,2.05),(-.25,-2.5,1.60),.9),
       120:('advance',-7,'thrust',6,(0,-6.92,2.05),(0,-22,2.0),12),
       240:('ieyasu',-13,'thrust',11,(0,-12.92,2.05),(0,-24,2.45),11)}
for frame,(name,offset,clip,pose,eye,target,focus) in shots.items():
    # Dedicated POV arms carry the weapon higher and forward than the game rig.
    hero_pose=pose_actor(hero,clip,pose,(0,offset-.50,.55))
    wrists={side:hero[0].pose.bones['hand.'+side].head.copy()+Vector((0,offset-.50,.55)) for side in ('L','R')}
    boss_pose=pose_actor(boss,'idle',0,(0,-24,0),math.pi,1.65)
    # Source rig frames and output timeline frames are separate. Objects store
    # sampled high-poly transforms at the three planned cinematic key poses.
    for o,transform in hero_pose+boss_pose:
        o.matrix_world=transform
        o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='rotation_euler',frame=frame);o.keyframe_insert(data_path='scale',frame=frame)
    for side,sign in [('L',-1),('R',1)]:
        upper,fore=pov_arms[side];elbow=(sign*.42,offset-.20,1.44)
        connect(upper,(sign*.28,offset+.30,1.38),elbow,frame);connect(fore,elbow,wrists[side],frame)
    camera.location=eye;aim(camera,target);camera.data.dof.focus_distance=focus
    camera.data.lens=22 if frame==1 else 25;camera.data.keyframe_insert(data_path='lens',frame=frame)
    camera.keyframe_insert(data_path='location',frame=frame);camera.keyframe_insert(data_path='rotation_euler',frame=frame);camera.data.dof.keyframe_insert(data_path='focus_distance',frame=frame)
    light=bpy.data.objects['near armour softbox'];light.location=(-3,offset-1,4);aim(light,(0,offset-.5,1.6));light.keyframe_insert(data_path='location',frame=frame);light.keyframe_insert(data_path='rotation_euler',frame=frame)
    scene.timeline_markers.new(name,frame=frame)
# Remove hidden source-only objects and empty rig collections from this derivative.
bpy.data.batch_remove([o for o in scene.objects if o.hide_render])
for layer in bpy.context.view_layer.layer_collection.children:layer.exclude=False
print('CINEMA_BUILD poses ready',flush=True)
scene.frame_start=1;scene.frame_end=240;scene.render.fps=24
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples
scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.035
scene.cycles.max_bounces=7;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3;scene.cycles.volume_bounces=1
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*9/16);scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='16' if args.width>=3840 else '8'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.35
scene.render.film_transparent=False
scene['README']='First-person look development. Three sampled blocking poses, not a finished 240-frame performance. Real sculpt masters, Cycles CPU, AgX, procedural cinematic terrain. Game assets unchanged.'
if args.save_scene:
    bpy.context.preferences.filepaths.save_version=0
    bpy.data.orphans_purge(do_recursive=True)
    scene.frame_set(1)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/cinema/first-person-lookdev.blend'),compress=True)
preparation=time.perf_counter()-started
report={'renderer':'Blender '+bpy.app.version_string+' / Cycles CPU','threads':4,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'samples':args.samples,'png_bits_per_channel':int(scene.render.image_settings.color_depth),'denoising':True,'hero_sculpt_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in hero[2]),'boss_sculpt_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in boss[2]),'preparation_seconds':round(preparation,2),'frames':[],'note':'Three blocking poses; POV-only sleeves and inherited sculpted hands/weapon. No final animation, motion blur, Modal GPU timing or GPU cost measurement.'}
for frame in map(int,args.frames.split(',')):
    scene.frame_set(frame);scene.render.filepath=str(OUT/f'pov-{frame:03d}-{args.width}.png')
    before=time.perf_counter();bpy.ops.render.render(write_still=True)
    item={'frame':frame,'shot':shots[frame][0],'seconds':round(time.perf_counter()-before,2),'file':Path(scene.render.filepath).name};report['frames'].append(item)
    (OUT/f'render-{args.width}.json').write_text(json.dumps(report,indent=2)+'\n');print('FRAME_COMPLETE',json.dumps(item),flush=True)
print('CINEMA_COMPLETE',json.dumps(report),flush=True)
