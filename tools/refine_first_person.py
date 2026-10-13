"""Editable cinematic detail pass, built on the first-person Blender lookdev scene.

All visible additions are meshes and shader nodes, not image overpainting.
Run with the pinned bpy runtime; arguments follow --.
"""
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--width', type=int, default=1280)
parser.add_argument('--samples', type=int, default=20)
parser.add_argument('--frames', default='1,240')
parser.add_argument('--save-scene', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT = ROOT / 'renders/first-person-refined'
OUT.mkdir(parents=True, exist_ok=True)
start = time.perf_counter()
random.seed(1615)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/cinema/first-person-lookdev.blend'))
scene = bpy.context.scene
scene.frame_set(1)


def material(name, dark, light, rough=.6, metal=0, scale=12, bump=.001, weave=False):
    m = bpy.data.materials.new('II / ' + name)
    m.use_nodes = True
    n, links = m.node_tree.nodes, m.node_tree.links
    p = n.get('Principled BSDF')
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    coord = n.new('ShaderNodeTexCoord')
    tex = n.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 5
    tex.inputs['Roughness'].default_value = .78
    links.new(coord.outputs['Object'], tex.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .20
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .82
    ramp.color_ramp.elements[1].color = (*light, 1)
    links.new(tex.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs[0], p.inputs['Base Color'])
    roughmap = n.new('ShaderNodeMapRange')
    roughmap.inputs['To Min'].default_value = rough * .74
    roughmap.inputs['To Max'].default_value = min(1, rough * 1.17)
    links.new(tex.outputs['Fac'], roughmap.inputs[0])
    links.new(roughmap.outputs[0], p.inputs['Roughness'])
    fine = n.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 220 if weave else 95
    fine.inputs['Detail'].default_value = 3
    links.new(coord.outputs['Object'], fine.inputs['Vector'])
    b = n.new('ShaderNodeBump')
    b.inputs['Distance'].default_value = bump
    b.inputs['Strength'].default_value = .32
    links.new(fine.outputs['Fac'], b.inputs['Height'])
    links.new(b.outputs[0], p.inputs['Normal'])
    if weave:
        p.inputs['Sheen Weight'].default_value = .22
        wave = n.new('ShaderNodeTexWave')
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'DIAGONAL'
        wave.inputs['Scale'].default_value = 280
        wave.inputs['Distortion'].default_value = 1.4
        links.new(coord.outputs['Object'], wave.inputs['Vector'])
        links.new(wave.outputs['Color'], b.inputs['Height'])
    return m


red = material('worn vermilion lacquer', (.035,.0015,.003), (.34,.015,.011), .39,.17,18,.0005)
p = red.node_tree.nodes.get('Principled BSDF')
p.inputs['Coat Weight'].default_value = .48
p.inputs['Coat Roughness'].default_value = .24
edge = material('rubbed copper edges', (.07,.025,.009), (.38,.19,.048), .49,.7,48,.0003)
iron = material('blackened iron', (.006,.009,.013), (.055,.065,.064), .55,.65,32,.0006)
cloth = material('indigo woven hemp', (.004,.009,.014), (.038,.052,.063), .94,0,32,.0005,True)
glove = material('smoked deerskin gloves', (.009,.007,.005), (.068,.044,.021), .82,0,55,.0006)
cord = material('weathered silk odoshi', (.075,.022,.013), (.42,.17,.085), .88,0,65,.0004,True)
thread = material('linen stitching', (.12,.085,.04), (.36,.28,.13), .92,0,75,.0003)
wood = material('split cedar grain', (.009,.006,.004), (.16,.078,.032), .83,0,5,.005)
stone = material('irregular wet foundation stone', (.014,.026,.031), (.18,.21,.20), .81,0,3,.035)
tilemat = material('blue charcoal ceramic tiles', (.009,.018,.025), (.085,.12,.14), .52,.08,7,.003)
snow = material('dirty windblown snow', (.18,.22,.22), (.66,.73,.76), .93,0,7,.006)
straw = material('trampled straw', (.038,.025,.01), (.20,.135,.060), .97,0,18,.001)
ash = material('soot and rubble', (.005,.006,.007), (.04,.046,.041), .94,0,13,.004)
plaster = material('aged ochre plaster', (.055,.067,.067), (.31,.30,.24), .97,0,1.8,.014)


class Batch:
    """Group repeated small geometry by material, keeping draw/object counts low."""
    def __init__(self, name, mat, parent=None, smooth=True):
        self.name,self.mat,self.parent,self.smooth = name,mat,parent,smooth
        self.v,self.f = [],[]

    def add(self, vertices, faces):
        base=len(self.v)
        self.v.extend(vertices)
        self.f.extend(tuple(base+i for i in face) for face in faces)

    def tube(self, points, radii, sides=8):
        points=list(map(Vector,points))
        if isinstance(radii,(float,int)):radii=[radii]*len(points)
        vertices=[]
        for j,(point,radius) in enumerate(zip(points,radii)):
            direction=points[min(j+1,len(points)-1)]-points[max(0,j-1)]
            rotation=direction.to_track_quat('Z','Y')
            for k in range(sides):
                a=k*math.tau/sides
                vertices.append(point+rotation@Vector((math.cos(a)*radius,math.sin(a)*radius,0)))
        faces=[tuple(range(sides-1,-1,-1))]
        for j in range(len(points)-1):
            for k in range(sides):
                a=j*sides+k;b=j*sides+(k+1)%sides
                faces.append((a,b,b+sides,a+sides))
        faces.append(tuple((len(points)-1)*sides+k for k in range(sides)))
        self.add(vertices,faces)

    def ellipsoid(self, center, radii, nu=16,nv=10):
        vertices=[]
        for j in range(nv+1):
            t=.0001+(math.pi-.0002)*j/nv
            for k in range(nu):
                a=k*math.tau/nu
                vertices.append((center[0]+radii[0]*math.sin(t)*math.cos(a),center[1]+radii[1]*math.sin(t)*math.sin(a),center[2]+radii[2]*math.cos(t)))
        faces=[]
        for j in range(nv):
            for k in range(nu):
                a=j*nu+k;b=j*nu+(k+1)%nu
                faces.append((a,b,b+nu,a+nu))
        self.add(vertices,faces)

    def box(self, center, size):
        self.add([(center[0]+x*size[0]/2,center[1]+y*size[1]/2,center[2]+z*size[2]/2) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

    def finish(self, bevel=0):
        if not self.v:return None
        data=bpy.data.meshes.new(self.name)
        data.from_pydata(self.v,[],self.f);data.update()
        o=bpy.data.objects.new(self.name,data);scene.collection.objects.link(o)
        data.materials.append(self.mat)
        for p in data.polygons:p.use_smooth=self.smooth
        if self.parent:o.parent=self.parent
        if bevel:
            mod=o.modifiers.new('rounded forged edges','BEVEL');mod.width=bevel;mod.segments=2
        o['detail_pass']='illustration-detail-v2'
        return o


def empty(name):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);return o


def key_matrix(o,matrix,frame):
    o.matrix_world=matrix
    for path in ('location','rotation_euler','scale'):o.keyframe_insert(data_path=path,frame=frame)


def center(o):
    return sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8


def polar(z,a,r):return (math.cos(a)*r,math.sin(a)*r,z)


# Sample existing poses before replacing stretched sleeves and mitten-like gloves.
shaft=bpy.data.objects['HIGH/yari.shaft']
socket=bpy.data.objects['HIGH/yari.socket']
grips={side:empty('II articulated grip '+side) for side in ('L','R')}
forearms={side:empty('II proportioned kote '+side) for side in ('L','R')}
upperarms={side:empty('II folded upper sleeve '+side) for side in ('L','R')}
for frame in (1,120,240):
    scene.frame_set(frame)
    axis=(center(socket)-center(shaft)).normalized()
    for side,sign in [('L',-1),('R',1)]:
        old=bpy.data.objects['HIGH/glove.hero.'+str(sign)]
        oldfore=bpy.data.objects['POV forearm sleeve '+side]
        grip=center(old);grip=center(shaft)+axis*(grip-center(shaft)).dot(axis)
        toward_elbow=(oldfore.matrix_world.translation-grip).normalized()
        z=(toward_elbow-axis*toward_elbow.dot(axis)).normalized()
        x=axis.copy();y=z.cross(x).normalized()
        if y.dot(scene.camera.location-grip)<0:x=-x;y=-y
        orientation=Matrix((x,y,z)).transposed().to_4x4();orientation.translation=grip
        key_matrix(grips[side],orientation,frame)
        wrist=orientation@Vector((0,0,.105))
        elbow=wrist+toward_elbow*.34
        forematrix=(wrist-elbow).to_track_quat('Z','Y').to_matrix().to_4x4();forematrix.translation=elbow
        key_matrix(forearms[side],forematrix,frame)
        shoulder=scene.camera.location+Vector((sign*.32,.26,-.42))
        up=(elbow-shoulder).to_track_quat('Z','Y').to_matrix().to_4x4()
        up.translation=shoulder;up=up@Matrix.Diagonal((1,1,(elbow-shoulder).length,1))
        key_matrix(upperarms[side],up,frame)

remove=[]
for o in scene.objects:
    name=o.name
    if name.startswith(('POV upper sleeve','POV forearm sleeve','curved red kote splint','gold kote binding')):remove.append(o)
    elif o.get('part_name','').startswith(('glove.hero','finger.hero')) and center(o).y>-20:remove.append(o)
bpy.data.batch_remove(remove)

for side in ('L','R'):
    parent=forearms[side]
    fabric=Batch('II sleeve folds '+side,cloth,parent)
    # Actual folds gather at the elbow and wrist; use physical metres, no Z stretch.
    v=[];faces=[];nu=64;nv=58
    for j in range(nv+1):
        z=j/nv*.35
        for k in range(nu):
            a=k*math.tau/nu
            r=.073-.024*j/nv
            r+=.0055*math.sin(z*165+a*3)+.003*math.sin(z*270-a*5)
            v.append(polar(z,a,r))
    for j in range(nv):
        for k in range(nu):
            a=j*nu+k;b=j*nu+(k+1)%nu;faces.append((a,b,b+nu,a+nu))
    fabric.add(v,faces);fabric.finish()
    plates=Batch('II articulated crimson lamellae '+side,red,parent)
    rims=Batch('II abraded plate rims '+side,edge,parent)
    rivets=Batch('II hammered rivets '+side,iron,parent)
    lace=Batch('II braided cross lacing '+side,cord,parent)
    stitches=Batch('II raised cord fibres '+side,thread,parent)
    chips=Batch('II chipped lacquer and grazing cuts '+side,iron,parent,smooth=False)
    for row in range(7):
        z0=.022+row*.042;z1=z0+.056
        for col in range(7):
            a0=col*math.tau/7+.035;a1=(col+1)*math.tau/7-.035
            verts=[];ff=[]
            for j in range(5):
                z=z0+(z1-z0)*j/4
                r=.081-.023*z/.35+.002*math.sin(j*math.pi/4)
                for k in range(11):verts.append(polar(z,a0+(a1-a0)*k/10,r))
            for j in range(4):
                for k in range(10):a=j*11+k;ff.append((a,a+1,a+12,a+11))
            plates.add(verts,ff)
            for chip in range(3):
                a=random.uniform(a0+.02,a1-.02);z=z0+random.uniform(.001,.009)
                r=.081-.023*z/.35+.002*math.sin((z-z0)/.056*math.pi)+.0006
                chips.add([polar(z,a,r),polar(z+random.uniform(.001,.005),a+.019,r),polar(z+.0005,a+.045,r)],[(0,1,2)])
            # Rolled rims and visible stitching holes, all real geometry.
            rims.tube([polar(z0,a0+(a1-a0)*k/16,.081-.023*z0/.35+.0007) for k in range(17)],.00085,6)
            for a in (a0+.10,a1-.10):
                rr=.081-.023*(z0+.012)/.35+.0015
                rivets.ellipsoid(polar(z0+.012,a,rr),(.0017,.0017,.0017),8,5)
            if row<6:
                for direction in (-1,1):
                    points=[]
                    for k in range(13):
                        t=k/12;z=z0+.025+t*.034
                        a=(a0+a1)/2+direction*(t-.5)*.22
                        rr=.087-.023*z/.35+.002*math.sin(t*math.pi)
                        points.append(polar(z,a,rr))
                    lace.tube(points,.0017,7)
                    # Twisted fine strand running around each lace.
                    stitches.tube([Vector(pt)+Vector((math.sin(k*2)*.0014,math.cos(k*2)*.0014,0)) for k,pt in enumerate(points)],.00028,4)
    plateobj=plates.finish()
    mod=plateobj.modifiers.new('individual lamella thickness','SOLIDIFY');mod.thickness=.0018
    rims.finish();rivets.finish();lace.finish();stitches.finish();chips.finish()
    cuffs=Batch('II bound wrist and elbow '+side,glove,parent)
    for z,r in [(.008,.078),(.330,.056)]:
        cuffs.tube([polar(z,k*math.tau/80,r) for k in range(81)],.006,10)
    cuffs.finish()
    # Gathered upper sleeves extend out of camera without stretching the metalwork.
    upper=Batch('II pleated shoulder cloth '+side,cloth,upperarms[side])
    v=[];f=[]
    for j in range(49):
        z=j/48
        for k in range(48):
            a=k*math.tau/48;r=.088-.018*z+.008*math.sin(z*47+a*3)+.004*math.sin(z*81-a*5)
            v.append(polar(z,a,r))
    for j in range(48):
        for k in range(48):a=j*48+k;b=j*48+(k+1)%48;f.append((a,b,b+48,a+48))
    upper.add(v,f);upper.finish()

    # Four independently curled fingers, an opposed thumb, seams and dorsal armour.
    parent=grips[side]
    skin=Batch('II anatomically separated glove '+side,glove,parent)
    skin.ellipsoid((0,.010,.057),(.055,.029,.053),32,24)
    seams=Batch('II hand sewn seams '+side,thread,parent)
    for digit in range(4):
        x=(digit-1.5)*.025
        points=[];radii=[]
        for k in range(33):
            t=k/32;a=math.radians(8+t*256)
            radius=.038+.003*math.sin(t*math.pi)
            points.append((x,radius*math.sin(a),radius*math.cos(a)))
            radii.append((.0125 if digit in (1,2) else .011)*(.94+.09*math.cos(t*math.tau))*(1-.17*t))
        skin.tube(points,radii,14)
        skin.ellipsoid(points[-1],(radii[-1],)*3,12,8)
        # Dark creases in the leather over the finger joints.
        for k in (8,18):
            a=math.radians(8+k/32*256)
            seams.tube([(x+(t/8-.5)*.016,(.050+.0006*math.sin(t))*math.sin(a),(.050+.0006*math.sin(t))*math.cos(a)) for t in range(9)],.00045,5)
    thumbpts=[(-.053,.006,.077),(-.067,.026,.057),(-.064,.047,.033),(-.047,.055,.016),(-.026,.050,.004)]
    skin.tube(thumbpts,[.021,.019,.017,.015,.012],16)
    skin.ellipsoid(thumbpts[-1],(.012,.012,.012),16,10)
    skin.finish()
    for sign in (-1,1):
        for j in range(15):
            z=.025+j*.005
            seams.tube([(sign*.043,.030,z),(sign*.046,.031,z+.0025)],.0005,5)
    seams.finish()
    guard=Batch('II fitted tekko hand guard '+side,red,parent)
    guard.ellipsoid((0,.037,.072),(.043,.008,.038),24,16)
    guard.finish()
    insignia=Batch('II six coin tekko engraving '+side,edge,parent)
    for row in range(2):
        for col in range(3):
            cx=(col-1)*.018;cz=.064+row*.017
            insignia.tube([(cx+.006*math.cos(k*math.tau/24),.046,cz+.006*math.sin(k*math.tau/24)) for k in range(25)],.001,6)
    insignia.finish()

print('REFINE arms and grasp complete',flush=True)

# Add fitted metalwork to the existing boss's curved plates via local-space rays.
# Parenting retains all three original sampled poses without a second rig.
scene.frame_set(1)
for plate in list(scene.objects):
    part=plate.get('part_name','')
    if plate.type!='MESH' or not (-26<center(plate).y<-22):continue
    if not ((part.startswith('cuirass.hero.') and '.False' in part) or part.startswith('sode.hero.') or part.startswith('kusazuri.hero.0.')):continue
    lo=Vector(plate.bound_box[0]);hi=Vector(plate.bound_box[6])
    decor=Batch('II boss fitted gilt edging '+plate.name,edge,plate)
    ties=Batch('II boss plate silk ties '+plate.name,cord,plate)
    def facepoint(x,z,lift=.002):
        hit,loc,normal,index=plate.ray_cast(Vector((x,lo.y-.2,z)),Vector((0,1,0)))
        return loc+normal*lift if hit else None
    for level in (.14,.86):
        pts=[]
        for j in range(41):
            pos=facepoint(lo.x+(hi.x-lo.x)*(.06+.88*j/40),lo.z+(hi.z-lo.z)*level)
            if pos is not None:pts.append(pos)
        if len(pts)>1:decor.tube(pts,.0018,6)
    columns=10 if part.startswith('cuirass') else 4
    for j in range(columns):
        x=lo.x+(hi.x-lo.x)*(.13+.74*j/max(1,columns-1))
        for sign in (-1,1):
            pts=[]
            for k in range(9):
                t=k/8
                pos=facepoint(x+sign*(t-.5)*.016,lo.z+(hi.z-lo.z)*(.32+t*.38),.004)
                if pos is not None:pts.append(pos)
            if len(pts)>1:ties.tube(pts,.0021,6)
        pos=facepoint(x,lo.z+(hi.z-lo.z)*.76,.003)
        if pos is not None:decor.ellipsoid(pos,(.0035,)*3,8,6)
    decor.finish();ties.finish()

# Four different authored troop poses share four evaluated meshes, not 50 rigs.
with bpy.data.libraries.load(str(ROOT/'assets/source/samurai-kit.blend'),link=False) as (available,loaded):
    loaded.objects=['tokugawa_runtime']
source_troop=loaded.objects[0]
scene.collection.objects.link(source_troop)
source_rig=source_troop.parent
scene.collection.objects.link(source_rig)
source_rig.location=(0,0,0);source_rig.animation_data.action=None
pose_meshes=[]
for clip,frame in [('idle',5),('run',8),('thrust',3),('thrust',15)]:
    for track in source_rig.animation_data.nla_tracks:track.mute=track.name!=clip;track.is_solo=False
    scene.frame_set(frame);bpy.context.view_layer.update()
    pose_meshes.append(bpy.data.meshes.new_from_object(source_troop.evaluated_get(bpy.context.evaluated_depsgraph_get())))
for i,troop in enumerate(o for o in scene.objects if o.name.startswith('Tokugawa formation')):
    troop.data=pose_meshes[i%len(pose_meshes)]
    troop.rotation_euler.z+=random.uniform(-.20,.20)
    troop.location.x+=random.uniform(-.35,.35);troop.location.y+=random.uniform(-.8,.8)
    troop.scale=(random.uniform(.94,1.06),random.uniform(.94,1.06),random.uniform(.96,1.04))
bpy.data.batch_remove([source_troop,source_rig])
scene.frame_set(1)

# Grain follows the timber's axis rather than uniform plastic noise.
for m in (wood,):
    n=m.node_tree.nodes;links=m.node_tree.links
    mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(3,3,.16)
    coord=next(x for x in n if x.type=='TEX_COORD')
    links.new(coord.outputs['Object'],mapping.inputs[0])
    for tex in [x for x in n if x.type=='TEX_NOISE']:links.new(mapping.outputs[0],tex.inputs['Vector'])
for o in scene.objects:
    if o.type!='MESH':continue
    if o.name.startswith(('splintered defensive stake','lashed cross brace','sashimono mast','cross pole','burning fallen beam')):
        o.data.materials.clear();o.data.materials.append(wood)
    elif o.name.startswith('keep plaster storey'):
        o.data.materials.clear();o.data.materials.append(plaster)
    elif o.name.startswith('snow heavy curved eave'):
        o.data.materials.clear();o.data.materials.append(tilemat)

# Castle: layered ceramic tiles, end caps, timber framing, lattices and snow ridges.
tiles=Batch('II thousands of ceramic roof tiles',tilemat)
snowcaps=Batch('II wind trapped roof snow',snow)
beams=Batch('II castle timber framing',wood,smooth=False)
ironwork=Batch('II castle iron fittings',iron)
for tier in range(5):
    z=5+tier*3.1;w=17-tier*2.6;d=13-tier*1.7
    front=-61+d/2+.11
    for side in (-1,1):
        for col in range(round(w/.30)+1):
            u=col/round(w/.30)*2-1
            for row in range(11):
                pts=[]
                for j in range(5):
                    t=(row+j/4)/11
                    pts.append((u*w*(.43+.19*t),-61+side*d*.66*t,z+4-2*t+.65*t**4+.32*abs(u)**5*t+.035))
                tiles.tube(pts,.047,8)
                if random.random()<.28:
                    snowcaps.tube([Vector(p)+Vector((0,0,.05)) for p in pts],.026,6)
        for k in range(round(w/.22)):
            x=(k/round(w/.22)*2-1)*w*.62
            tiles.ellipsoid((x,-61+side*d*.66,z+2.67+.32*(abs(x)/(w*.62))**5),(.065,.072,.065),10,6)
        beams.box((0,-61+side*d*.5,z+.02),(w+.22,.25,.17))
        beams.box((0,-61+side*d*.5,z+2.22),(w+.25,.25,.18))
    for k in range(round(w/.9)+1):
        x=(k/round(w/.9)-.5)*w
        beams.box((x,front,z+1.1),(.13,.15,2.3))
        for offset in (-.21,.21):
            beams.box((x+offset,front+.03,z+2.07),(.09,.25,.38))
    for k in range(max(3,int(w/1.8))):
        x=(k-(max(3,int(w/1.8))-1)/2)*1.7
        for dx in (-.32,.32):beams.box((x+dx,front+.055,z+1.2),(.065,.08,1.22))
        for dz in (-.59,.59):beams.box((x,front+.055,z+1.2+dz),(.71,.08,.065))
        for dx in (-.19,-.095,0,.095,.19):beams.box((x+dx,front+.11,z+1.2),(.025,.04,1.1))
        for dz in (-.30,0,.30):beams.box((x,front+.14,z+1.2+dz),(.55,.03,.025))
    # Balcony rail and carved corbels are distinct silhouettes at each storey.
    beams.box((0,front+.45,z+.52),(w+.8,.10,.08))
    for k in range(round(w/.36)+1):
        x=(k/round(w/.36)-.5)*w
        beams.box((x,front+.45,z+.27),(.055,.055,.55))
        if k%3==0:ironwork.tube([(x,front,z-.35),(x,front+.46,z)],.055,6)
tiles.finish();snowcaps.finish();beams.finish(.018);ironwork.finish()

# More varied stone sizes and silhouettes than the first pass's identical blocks.
oldstones=[o for o in scene.objects if o.name.startswith('rough castle foundation')]
bpy.data.batch_remove(oldstones)
masonry=Batch('II battered stone rampart',stone,smooth=False)
stone_snow=Batch('II snow in masonry ledges',snow)
for row in range(6):
    x=-18.0
    while x<18:
        width=random.uniform(.72,1.85);h=random.uniform(.60,.78);z=.35+row*.69
        cy=-51.8-row*.15
        v=[]
        for dz in (-1,1):
            for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                v.append((x+width*.5+dx*width*.49+random.uniform(-.07,.07),cy+dy*.52+random.uniform(-.055,.055),z+dz*h*.47+random.uniform(-.035,.035)))
        masonry.add(v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        if random.random()<.48:stone_snow.ellipsoid((x+width*.5,cy+.50,z+h*.48),(width*.40,.09,.035),12,6)
        x+=width
masonry.finish(.035);stone_snow.finish()

# Replace invisible back-facing heraldry with ink-like crests on both cloth sides.
bpy.data.batch_remove([o for o in scene.objects if o.name.startswith('six coins crest')])
crest=Batch('II visible six coin banner emblems',edge)
hems=Batch('II banner hem and seams',thread)
for banner in [o for o in scene.objects if o.name.startswith('wind swept banner')]:
    x0=min(v.co.x for v in banner.data.vertices)
    y0=banner.data.vertices[0].co.y
    is_red='oxblood' in banner.data.materials[0].name
    def bannerpoint(u,t,offset=0):return (x0+u,y0+.16*math.sin(u*5+t*5)+t*.22+offset,4.55-t*2.6)
    for u in (.025,.975):hems.tube([bannerpoint(u,j/64,.006) for j in range(65)],.004,5)
    if is_red:
        for a in range(3):
            for b in range(2):
                for face in (-1,1):
                    crest.tube([bannerpoint(.24+a*.25+.075*math.cos(k*math.tau/32),.31+b*.10+.075/2.6*math.sin(k*math.tau/32),face*.008) for k in range(33)],.011,6)
    # Slightly torn lower edge, avoiding uniformly rectangular flag silhouettes.
    for v in banner.data.vertices:
        t=(4.55-v.co.z)/2.6
        if t>.83:v.co.z+=random.uniform(0,.085)*(t-.83)/.17
crest.finish();hems.finish()

print('REFINE architecture and heraldry complete',flush=True)

# Snow is interrupted by drifted straw, splinters, gravel and broken equipment.
def height(x,y):
    road=math.exp(-((x-.4*math.sin(y*.24))/3.0)**4)
    return .12*(1-road)+.018*math.sin(x*3.2+y)*math.cos(y*4.7)+.025*math.sin(x*.8+y*.45)

gravel=Batch('II road gravel and rubble',ash,smooth=False)
drifts=Batch('II crusted snow banks',snow)
hay=Batch('II scattered battlefield straw',straw)
splinters=Batch('II split timber debris',wood,smooth=False)
debris_centers=[(random.choice((-1,1))*random.uniform(3,8),random.uniform(-45,1)) for _ in range(38)]
for i in range(850):
    cx,cy=random.choice(debris_centers)
    x=random.gauss(cx,.55);y=random.gauss(cy,.85)
    if abs(x)<1.5 and random.random()<.8:continue
    z=height(x,y);r=random.uniform(.018,.085)
    gravel.ellipsoid((x,y,z+r*.25),(r,r*.7,r*.5),7,4)
for i in range(130):
    y=random.uniform(-48,2);x=random.choice((-1,1))*random.uniform(2.2,7.5)
    z=height(x,y);r=random.uniform(.15,.70)
    drifts.ellipsoid((x,y,z-.040),(r,r*.8,random.uniform(.04,.07)),16,8)
for i in range(2000):
    cx,cy=random.choice(debris_centers);x=random.gauss(cx,.7);y=random.gauss(cy,.9);z=height(x,y)+.015
    a=random.uniform(0,math.tau);length=random.uniform(.06,.32)
    hay.tube([(x,y,z),(x+math.cos(a)*length*.5,y+math.sin(a)*length*.5,z+.018),(x+math.cos(a)*length,y+math.sin(a)*length,z+.005)],.0025,4)
for i in range(110):
    x=random.choice((-1,1))*random.uniform(3.2,9);y=random.uniform(-45,-3);z=height(x,y)+.025
    length=random.uniform(.15,.65);a=random.uniform(-1,1)
    splinters.tube([(x,y,z),(x+length,y+a*length,z+.02)],[random.uniform(.015,.04),.002],5)
gravel.finish();drifts.finish();hay.finish();splinters.finish()

# Rope bindings on the defensive stakes; broken spear shafts and arrow fletching.
ropes=Batch('II timber lashing',cord)
arrows=Batch('II spent arrows',wood)
feathers=Batch('II arrow fletching',cloth,smooth=False)
for side in (-1,1):
    for y in range(-10,-42,-3):
        x=side*8
        for k in range(3):
            cx=x+k*.5
            for j in range(4):
                ropes.tube([(cx+.12*math.cos(a*math.tau/24),y+.42+.10*math.sin(a*math.tau/24),.85+(j-1.5)*.021) for a in range(25)],.009,6)
for i in range(50):
    x=random.choice((-1,1))*random.uniform(3.4,8.5);y=random.uniform(-38,-2);z=height(x,y)
    a=Vector((x,y,z));b=a+Vector((random.uniform(-.18,.18),random.uniform(-.2,.2),random.uniform(.3,.7)))
    arrows.tube([a,b],.005,6)
    for sign in (-1,1):feathers.add([b,b+Vector((sign*.03,0,-.07)),b+Vector((0,0,-.13))],[(0,1,2)])
ropes.finish();arrows.finish();feathers.finish()

# Material layering: soot/snow variation on the existing continuous terrain shader.
terrain=bpy.data.materials['continuous thawed snow']
n=terrain.node_tree.nodes;links=terrain.node_tree.links;p=n.get('Principled BSDF')
oldcolor=p.inputs['Base Color'].links[0].from_socket
geo=next(node for node in n if node.type=='NEW_GEOMETRY')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.7;noise.inputs['Detail'].default_value=6
links.new(geo.outputs['Position'],noise.inputs['Vector'])
colors=n.new('ShaderNodeValToRGB')
colors.color_ramp.elements[0].color=(.14,.115,.083,1)
colors.color_ramp.elements[0].position=.18
colors.color_ramp.elements[1].color=(.94,.96,1,1)
colors.color_ramp.elements[1].position=.75
links.new(noise.outputs['Fac'],colors.inputs[0])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.65
links.new(oldcolor,mix.inputs[1]);links.new(colors.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])

# Cold overcast, warm directional light and restrained fog preserve readable forms.
volume=bpy.data.materials['cold battlefield haze'].node_tree.nodes
next(n for n in volume if n.type=='PRINCIPLED_VOLUME').inputs['Density'].default_value=.010
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.18
for o in scene.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=.65
bpy.data.objects['low winter sun'].data.energy=2700
bpy.data.objects['near armour softbox'].data.energy=170
bpy.data.objects['boss rim'].data.energy=1300
scene.view_settings.exposure=-.15
scene['README']='Detail pass II: proportioned articulated kote, physical lacing/rivets, curled gloves, ceramic roofs, castle framing, visible crests, battlefield debris. Three blocking poses only; no completed animation.'

scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*9/16)
scene.render.resolution_percentage=100
scene.cycles.samples=args.samples;scene.cycles.adaptive_threshold=.035
scene.render.image_settings.color_depth='16' if args.width>=1920 else '8'
scene.frame_set(1)
if args.save_scene:
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/cinema/first-person-refined.blend'),compress=True)
report={'renderer':'Blender '+bpy.app.version_string+' / Cycles CPU','resolution':[args.width,scene.render.resolution_y],'samples':args.samples,'threads':scene.render.threads,'png_bits_per_channel':int(scene.render.image_settings.color_depth),'preparation_seconds':round(time.perf_counter()-start,2),'added_mesh_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH' and o.get('detail_pass')),'frames':[],'note':'Actual editable geometry and shader pass. Three blocking poses; not final animation or game optimisation.'}
print('REFINE ready '+json.dumps(report),flush=True)
for frame in map(int,args.frames.split(',')):
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'pov-{frame:03d}-{args.width}.png')
    before=time.perf_counter();bpy.ops.render.render(write_still=True)
    report['frames'].append({'frame':frame,'file':Path(scene.render.filepath).name,'seconds':round(time.perf_counter()-before,2)})
    (OUT/f'render-{args.width}.json').write_text(json.dumps(report,indent=2)+'\n')
    print('REFINE_FRAME_COMPLETE '+json.dumps(report['frames'][-1]),flush=True)
