"""Reusable samurai kit, Blender 4.x. Local CPU only, no downloads or paid services.
Source: linked modular meshes. Runtime: one shared-atlas material per GLB; skinned hero plus instanced troops.
Meters, feet at Z=0, front=-Y; glTF exports Y-up. MODEL_OUTPUT overrides output.
"""
import bpy
import math
import os
import json
import sys
import re
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from painted_surfaces import make_atlas, map_uv, painted_material
from samurai_rig import bind_hero, bone_for_part, weapon_point
from gltf_assets import share_images
from refine_hero import refine_hero, hero_parts, HERO_COLORS
from hero_highpoly import bake_hero
from refine_ieyasu import commander_parts, refine_ieyasu, IEYASU_COLORS, commander_silhouette

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get('MODEL_OUTPUT', ROOT / 'public/models'))
SOURCE = Path(os.environ.get('MODEL_SOURCE', ROOT / 'assets/source/samurai-kit.blend'))
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
lib = bpy.data.collections.new('00_SHARED_PARTS — linked mesh library')
bpy.context.scene.collection.children.link(lib)

COLORS = {
    'armor': (.49,.025,.045,1), 'cloth': (.025,.034,.048,1),
    'gold': (.37,.25,.12,1), 'skin': (.61,.35,.20,1),
    'steel': (.55,.66,.73,1), 'wood': (.16,.065,.025,1),
    'horn': (.065,.042,.024,1), 'cape': (.26,.018,.029,1),
    'lace': (.42,.32,.18,1), 'eye': (.006,.008,.012,1),
}
VARIANTS = {
    'yukimura': {'armor': (.32,.017,.025,1), 'helmet':'kabuto', 'weapon':'cross_yari', 'antlers':True, 'cape':True},
    'ashigaru': {'armor': (.24,.013,.02,1), 'helmet':'jingasa', 'weapon':'yari', 'banner':True},
    'tokugawa': {'armor': (.038,.088,.115,1), 'helmet':'jingasa', 'weapon':'yari', 'banner':True},
    'ieyasu': {'armor': (.065,.055,.028,1), 'helmet':'kabuto', 'weapon':'katana', 'crest':True, 'cape':True},
}
materials = {}
for role, color in COLORS.items():
    m=bpy.data.materials.new('source/'+role);m.diffuse_color=color;m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color
    bs.inputs['Metallic'].default_value={'gold':.48,'steel':.72,'armor':.12}.get(role,0)
    bs.inputs['Roughness'].default_value={'gold':.56,'steel':.36,'armor':.72,'eye':.5}.get(role,.82)
    materials[role]=m
parts={}

def register(name, obj, role):
    obj.name=name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    lib.objects.link(obj)
    obj.data.materials.clear();obj.data.materials.append(materials[role])
    obj['palette_role']=role;obj['part_name']=name;parts[name]=obj
    return obj

def cube(name, loc, scale, role, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('edge catchlight','BEVEL');mod.width=bevel;mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return register(name,o,role)

def sphere(name, loc, scale, role, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc)
    o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for poly in o.data.polygons:poly.use_smooth=True
    return register(name,o,role)

def rod(name, a, b, radius, role, tip=None, sides=6):
    d=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=sides,radius1=radius,radius2=radius if tip is None else tip,depth=d.length,location=(Vector(a)+Vector(b))/2)
    o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return register(name,o,role)

def mesh(name, verts, faces, role):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
    return register(name,o,role)

def shell(name,z0,z1,rx0,rx1,ry0,ry1,role):
    # Closed elliptical band: shared lamellar cuirass profile.
    n=24;verts=[]
    for z,rx,ry in [(z0,rx0,ry0),(z1,rx1,ry1)]:
        verts += [(math.cos(i*2*math.pi/n)*rx,math.sin(i*2*math.pi/n)*ry,z) for i in range(n)]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,role)

def coin(name,x,y,z,r=.037):
    bpy.ops.mesh.primitive_torus_add(major_segments=8,minor_segments=3,location=(x,y,z),major_radius=r,minor_radius=r*.30,rotation=(math.pi/2,0,0))
    return register(name,bpy.context.object,'gold')

# One reusable body: cloth joints, segmented limbs, geta-like boots, gloved hands.
base=[]
def add(obj):base.append(obj.name)
for side in [-1,1]:
    x=side*.145
    add(rod(f'thigh.{side}',(x,0,.85),(x,.015,.45),.168,'cloth',tip=.12,sides=10))
    add(rod(f'shin.{side}',(x,.015,.45),(x,-.015,.13),.085,'cloth',tip=.07,sides=8))
    add(cube(f'boot.{side}',(x,-.075,.0675),(.155,.29,.115),'cloth',.032))
    verts=[]
    for r in range(4):
        z=.16+r*.09
        for c in range(9):
            a=(c/8-.5)*1.9;radius=.079+.013*math.sin(r/3*math.pi)
            verts.append((x+math.sin(a)*radius,-math.cos(a)*radius-.012,z))
    add(mesh(f'shin_plate.{side}',verts,[(r*9+c,r*9+c+1,(r+1)*9+c+1,(r+1)*9+c) for r in range(3) for c in range(8)],'armor'))
    for z in [.23,.37]:add(cube(f'shin_tie.{side}.{z}',(x,-.115,z),(.16,.015,.024),'lace'))
    add(rod(f'upper_arm.{side}',(side*.31,0,1.32),(side*.43,-.025,1.10),.115,'cloth',tip=.085,sides=12))
    add(rod(f'forearm.{side}',(side*.43,-.025,1.10),(side*.47,-.16,.94),.078,'armor',tip=.065,sides=8))
    add(sphere(f'glove.{side}',(side*.47,-.16,.91),(.076,.078,.09),'cloth',8,4))
add(sphere('neck',(0,0,1.40),(.105,.10,.12),'cloth',8,4))
add(sphere('face',(0,-.015,1.56),(.162,.142,.200),'skin',16,8))
for side in [-1,1]:
    o=cube(f'eye.{side}',(side*.078,-.163,1.595),(.086,.028,.017),'eye');o.rotation_euler.y=side*.14;add(o)
# Sculpted angular cheek/nose mask under the eye opening, no rectangular muzzle.
add(mesh('menpo', [(-.145,-.10,1.55),(-.092,-.177,1.535),(0,-.198,1.56),(.092,-.177,1.535),(.145,-.10,1.55),(-.13,-.125,1.47),(-.060,-.180,1.43),(0,-.187,1.418),(.060,-.180,1.43),(.13,-.125,1.47),(0,-.214,1.50)], [(0,1,6,5),(1,2,10,6),(2,3,8,10),(3,4,9,8),(6,10,7),(10,8,7)],'armor'))
add(rod('mask.mouth',(-.060,-.194,1.464),(.060,-.194,1.464),.006,'eye',sides=6))
for i in range(10):
    z=.94+i*.0395
    add(shell(f'cuirass.band.{i}',z,z+.033,.266+i*.007,.270+i*.007,.173+i*.002,.176+i*.002,'armor'))
for side in [-1,1]:
    for i in range(5):
        verts=[]
        for col in range(3):
            for row in range(5):
                y=(row-2)*.088
                x=side*(.285+col*.083+i*.004)
                z=1.37-i*.043-col*.036+(1-(y/.23)**2)*.020
                verts.append((x,y,z))
        faces=[(c*5+r,c*5+r+1,(c+1)*5+r+1,(c+1)*5+r) for c in range(2) for r in range(4)]
        add(mesh(f'sode.{side}.{i}',verts,faces,'armor'))
        add(cube(f'sode_lace.{side}.{i}',(side*.37,-.179,1.34-i*.043),(.11,.012,.009),'lace'))
# Flared long kusazuri follow the new 2D guide rather than block-like belt tiles.
for i in range(9):
    angle=i*2*math.pi/9
    verts=[]
    for row in range(6):
        r=.26+row*.018
        for col in range(4):
            a=angle+(col/3-.5)*.56
            verts.append((math.sin(a)*r,math.cos(a)*r*.80,.91-row*.069+(row%2)*.008))
    faces=[(row*4+c,row*4+c+1,(row+1)*4+c+1,(row+1)*4+c) for row in range(5) for c in range(3)]
    add(mesh(f'kusazuri.{i}',verts,faces,'armor'))
add(shell('waist_sash',.90,.95,.282,.282,.192,.192,'cloth'))
for side in [-1,1]:
    add(cube(f'cuirass_lace.{side}',(side*.205,-.185,1.11),(.018,.035,.32),'lace'))
# Exposed helmet module choices.
helmets={}
kabuto=[]
kabuto.append(sphere('kabuto.dome',(0,.01,1.718),(.238,.218,.188),'armor',24,10).name)
kabuto.append(cube('kabuto.brow',(0,-.202,1.68),(.45,.13,.037),'cloth',.015).name)
# Curved shikoro sweeps from each temple around the nape in overlapping lames.
for row in range(5):
    verts=[]
    for edge in range(2):
        for j in range(19):
            a=-.34+j*(math.pi+.68)/18
            rx=.218+row*.010+edge*.010;ry=.205+row*.007+edge*.008
            verts.append((math.cos(a)*rx,math.sin(a)*ry+.008,1.685-row*.046-edge*.044))
    kabuto.append(mesh(f'kabuto.shikoro.{row}',verts,[(j,j+1,j+20,j+19) for j in range(18)],'armor').name)
for side in [-1,1]:
    kabuto.append(mesh(f'kabuto.fukigaeshi.{side}',[(side*.20,-.10,1.68),(side*.275,-.10,1.70),(side*.276,-.045,1.56),(side*.217,-.055,1.55)],[(0,1,2,3)],'armor').name)
helmets['kabuto']=kabuto
helmets['jingasa']=[rod('jingasa.hat',(0,.015,1.69),(0,.015,1.87),.32,'armor',tip=.055,sides=12).name,rod('jingasa.rim',(0,.015,1.675),(0,.015,1.70),.332,'cloth',sides=12).name]
antlers=[]
for side in [-1,1]:
    paths=[[(.125,-.012,1.83),(.235,-.022,1.97),(.31,-.018,2.13),(.32,-.008,2.29),(.40,.002,2.48)],
           [(.235,-.022,1.97),(.39,-.014,2.075),(.46,.0,2.23)],
           [(.31,-.018,2.13),(.21,-.03,2.25),(.195,-.026,2.40)],
           [(.32,-.008,2.29),(.29,-.013,2.39),(.32,-.007,2.49)]]
    for k,path in enumerate(paths):
        for j in range(len(path)-1):
            a=path[j];b=path[j+1]
            r=(.034 if k==0 else .023)*(1-j/len(path))
            antlers.append(rod(f'antler.{side}.{k}.{j}',(a[0]*side,a[1],a[2]),(b[0]*side,b[1],b[2]),r,'horn',tip=.002 if j==len(path)-2 else r*.75,sides=8).name)
    antlers.append(rod(f'antler.collar.{side}',(side*.125,-.012,1.83),(side*.157,-.017,1.875),.045,'gold',sides=10).name)
crest=[]
for i in range(7):
    a=(i-3)*.20
    crest.append(rod(f'gold_fan.{i}',(0,-.22,1.75),(math.sin(a)*.42,-.22,1.76+math.cos(a)*.49),.025,'gold',tip=.045).name)
coins=[coin(f'rokumon.{i}.{j}',(i-1)*.093,-.208,1.16+j*.091,.032).name for i in range(3) for j in range(2)]
coins += [coin(f'helmet.coin.{i}.{j}',(i-1)*.065,-.198,1.745+j*.064,.025).name for i in range(3) for j in range(2)]
# Wind-pulled, torn cloth instead of a rectangular plastic cape.
cape_verts=[]
for r in range(19):
    t=r/18
    for col in range(13):
        u=col/12
        # Tattered scalloped hem and wind-driven large cloth folds.
        z=1.395-t*1.04
        if r==18:z+=.05+(.07 if col%3==0 else -.025)
        cape_verts.append(((u-.5)*(.47+t*.45)-t*t*.20,.165+t*t*.40+math.sin(u*math.pi*7+t*2)*(.018+t*.065),z))
cape=mesh('cape',cape_verts,[(r*13+c,r*13+c+1,(r+1)*13+c+1,(r+1)*13+c) for r in range(18) for c in range(12) if not (r>15 and (r+c)%13==0)],'cape').name
# Pleated haidate cover the thighs; pointed lamellar edges break the silhouette.
for side in [-1,1]:
    verts=[]
    for row,z in enumerate([.85,.69,.53]):
        for col in range(5):verts.append((side*.14+(col-2)*(.045+row*.01),-.13-row*.025-(col%2)*.025,z+(.018 if row==2 and col%2 else 0)))
    faces=[(r*5+c,r*5+c+1,(r+1)*5+c+1,(r+1)*5+c) for r in range(2) for c in range(4)]
    add(mesh(f'haidate.{side}',verts,faces,'cloth'))
# Shared weapon grips use the right glove's anchor.
yari=[rod('yari.shaft',(.47,-.16,.20),(.47,-.16,2.62),.022,'wood').name,rod('yari.socket',(.47,-.16,2.50),(.47,-.16,2.65),.035,'gold').name]
blade=mesh('yari.blade',[(.47,-.16,2.96),(.535,-.16,2.69),(.47,-.183,2.65),(.405,-.16,2.69),(.47,-.137,2.65)],[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,4,3,2)],'steel').name
yari.append(blade)
cross=[]
for side in [-1,1]:
    cross.append(mesh(f'yari.cross.{side}',[(.47,-.16,2.76),(.47+side*.11,-.16,2.77),(.47+side*.28,-.16,2.81),(.47+side*.23,-.16,2.705),(.47,-.16,2.705),(.47+side*.105,-.19,2.735)],[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5),(0,4,3,2,1)],'steel').name)

katana=[rod('katana.hilt',(.47,-.16,.79),(.47,-.16,1.05),.027,'cloth').name,cube('katana.tsuba',(.47,-.16,1.06),(.13,.105,.027),'gold').name,rod('katana.blade',(.47,-.16,1.08),(.55,-.16,1.89),.028,'steel',tip=.002).name]
weapons={'yari':yari,'cross_yari':yari+cross,'katana':katana}
banner=[rod('sashimono.pole',(0,.22,.83),(0,.22,2.33),.017,'wood').name,rod('sashimono.cross',(0,.22,2.33),(.39,.22,2.33),.015,'wood').name,mesh('sashimono.cloth',[(.02,.23,2.31),(.38,.23,2.31),(.02,.24,2.03),(.38,.27,2.03),(.02,.24,1.76),(.38,.30,1.79)],[(0,1,3,2),(2,3,5,4)],'armor').name]
banner_coins=[coin(f'banner.coin.{i}.{j}',.10+i*.087,.21,2.08+j*.10,.022).name for i in range(3) for j in range(2)]
enemy_marks=[sphere(f'banner.gold.{i}',(.20+(i-1)*.065,.21,2.17-abs(i-1)*.09),(.052,.015,.058),'gold',8,4).name for i in range(3)]

# Close-range hero details: riveted borders, helmet ribs, laced lamellae and scabbard.
details=[]
for side in [-1,1]:
    for row in range(5):
        z=.968+row*.079
        for col in range(3):
            x=side*(.07+col*.069)
            details.append(sphere(f'cuirass.rivet.{side}.{row}.{col}',(x,-.204,z),(.011,.010,.011),'gold',6,3).name)
    for row in range(3):
        for col in range(3):
            x=side*(.305+col*.058);z=1.35-row*.063
            details.append(rod(f'sode.cord.{side}.{row}.{col}',(x,-.199,z-.017),(x+.015,-.202,z+.024),.007,'lace',sides=5).name)
    # Raised elbow plate and articulated knee cap.
    details.append(sphere(f'elbow.guard.{side}',(side*.44,-.026,1.10),(.08,.08,.065),'armor',8,4).name)
    details.append(sphere(f'knee.guard.{side}',(side*.145,-.085,.46),(.093,.044,.083),'armor',8,4).name)
    for row in range(3):
        details.append(cube(f'bracer.inlay.{side}.{row}',(side*(.442+row*.009),-.101-row*.025,1.055-row*.029),(.071,.015,.012),'steel',.002).name)
# Thin lacquer-colored ribs over the kabuto, with gold rivets at the brim.
for i in range(9):
    a=i*math.pi/4.5
    last=None
    for j in range(5):
        phi=.22+j*.27
        point=(math.cos(a)*.241*math.sin(phi),.01+math.sin(a)*.22*math.sin(phi),1.718+.192*math.cos(phi))
        if last:details.append(rod(f'kabuto.rib.{i}.{j}',last,point,.006,'gold',sides=5).name)
        last=point
# Belt-mounted wakizashi silhouette.
details.extend([
    rod('wakizashi.sheath',(-.28,.06,.90),(-.55,.13,.40),.031,'cloth',sides=8).name,
    rod('wakizashi.grip',(-.28,.06,.90),(-.17,.03,1.09),.032,'cloth',sides=8).name,
    cube('wakizashi.guard',(-.28,.06,.90),(.12,.10,.025),'gold',.008).name,
])
# Hero's folded neck scarf and a fuller, asymmetrical cape.
details.append(shell('neck.scarf',1.355,1.425,.145,.14,.15,.145,'armor').name)
# Braided waist rope, knots, forearm splints, gauntlets and sandal straps.
for strand in range(2):
    for j in range(48):
        a=j*2*math.pi/48;b=(j+1)*2*math.pi/48
        def point(t):return (math.cos(t)*.288,math.sin(t)*.197,.937+.012*math.sin(t*14+strand*math.pi))
        details.append(rod(f'obi.braid.{strand}.{j}',point(a),point(b),.009,'lace',sides=5).name)
for side in [-1,1]:
    for j in range(5):
        x=side*(.422+j*.009)
        details.append(rod(f'kote.splint.{side}.{j}',(x,-.090-j*.008,1.092),(x+side*.032,-.191-j*.005,.968),.009,'steel',sides=6).name)
    for j in range(4):
        details.append(rod(f'finger.{side}.{j}',(side*.47+(j-1.5)*.023,-.208,.938),(side*.47+(j-1.5)*.023,-.224,.884),.012,'cloth',tip=.009,sides=6).name)
    for j in range(3):
        details.append(rod(f'sandal.{side}.{j}',(side*.145-.068,-.17+j*.045,.126),(side*.145+.068,-.17+j*.045,.126),.009,'lace',sides=5).name)
    details.append(rod(f'obi.tail.{side}',(side*.05,-.20,.945),(side*.13,-.21,.76),.015,'lace',tip=.020,sides=8).name)
# Pale six-coin appliqué across the red cape, following its folds.
for i in range(3):
    for j in range(2):
        coins.append(coin(f'cape.coin.{i}.{j}',(i-1)*.095-.035,.256,1.04+j*.105,.033).name)
# Fabric silhouette: gathered hakama and sleeve folds, not cylindrical limbs.
for name,obj in parts.items():
    if name.startswith(('thigh.','upper_arm.')):
        for v in obj.data.vertices:
            p=v.co
            a=math.atan2(p.y,p.x);r=1+.10*math.cos(a*7)+.05*math.sin(a*11+p.z*23)
            p.x*=r;p.y*=r
    if name.startswith(('antler.','obi.braid','kote.splint')):
        for poly in obj.data.polygons:poly.use_smooth=True
# Worn metal piping gives thin armour panels a readable thickness.
for side in [-1,1]:
    for row in range(5):
        for c in range(2):
            def edge(j):return (side*(.285+j*.083+row*.004),-.176,1.37-row*.043-j*.036+(1-(.176/.23)**2)*.02)
            details.append(rod(f'sode.edge.{side}.{row}.{c}',edge(c),edge(c+1),.004,'gold',sides=5).name)
    for c in range(3):
        x=side*.145+(c-1)*.045
        details.append(rod(f'shin.inlay.{side}.{c}',(x,-.100,.18),(x,-.100,.42),.004,'gold',sides=5).name)

# Hero-specific authored plates reuse the same material atlas and rest-space rig.
hero_details=refine_hero(parts,mesh,rod,sphere,cube)
ieyasu_details=refine_ieyasu(mesh,rod,sphere)
images=make_atlas()
for role,color in COLORS.items():
    materials[role]=painted_material('painted/'+role,images,color)
for name,obj in parts.items():
    obj.data.materials.clear();obj.data.materials.append(materials[obj['palette_role']])
    map_uv(obj,name,obj['palette_role'])

# Anatomical re-proportioning shared by every variant: longer legs/torso,
# narrower shoulders, smaller head, an asymmetric braced stance and forward lean.
# Bake transforms once into library geometry; attachments remain aligned.
for name,obj in parts.items():
    mat=obj.matrix_world.copy()
    is_leg=name.startswith(('thigh.','shin.','boot.','shin_plate.','shin_tie.','knee.guard.','haidate.','sandal.'))
    side=-1 if '.-1' in name else 1
    for v in obj.data.vertices:
        p=mat@v.co
        if name.startswith(('yari.','katana.')):
            v.co=weapon_point(p);continue
        p.x*=.82;p.y*=.90
        if is_leg:
            p.x+=side*.055;p.y+=side*.075
        if p.z>1.40:
            p.x*=.86;p.y*=.92
            p.z=1.75+(p.z-1.40)*.88
        else:p.z*=1.25
        p.y-=max(0,p.z-1.05)*.10
        v.co=p
    obj.location=(0,0,0);obj.rotation_euler=(0,0,0);obj.scale=(1,1,1)
    # Facet-scale pigment and edge darkening; deterministic, no texture bake.
    wear=obj.data.color_attributes.new(name='Wear',type='BYTE_COLOR',domain='CORNER')
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            p=obj.data.vertices[obj.data.loops[li].vertex_index].co
            noise=math.sin(p.x*53+p.y*37+p.z*91)*math.sin(p.z*41-p.y*79)
            value=.94+.018*noise
            if p.z<.55:value*=.74
            wear.data[li].color=(value,value,value,1)
# Linked source assemblies retain editable part names, proportions and materials.
source_roots=[];stats={};shared_images={}
for index,(kind,variant) in enumerate(VARIANTS.items()):
    c=bpy.data.collections.new('10_'+kind);bpy.context.scene.collection.children.link(c)
    root=bpy.data.objects.new(kind,None);c.objects.link(root);root.location.x=(index-1.5)*2.3
    names=base+helmets[variant['helmet']]+weapons[variant['weapon']]
    if variant.get('antlers'):names+=antlers+coins
    if variant.get('crest'):names+=crest
    if variant.get('cape'):names+=[cape]+details
    if variant.get('banner'):names+=banner+(banner_coins if kind=='ashigaru' else enemy_marks)
    if kind=='yukimura':names=hero_parts(names)+hero_details
    if kind=='ieyasu':names=[n for n in hero_parts(names) if not n.startswith(('gold_fan','katana.blade'))]+commander_parts(hero_details)+ieyasu_details
    detailed=kind in ('yukimura','ieyasu')
    palette=HERO_COLORS if kind=='yukimura' else IEYASU_COLORS
    armor=painted_material(kind+'/painted armor',images,palette['armor'] if detailed else variant['armor'])
    hero_materials={role:painted_material('hero/'+role,images,color) for role,color in palette.items()} if detailed else {}
    actor_parts=[]
    for name in names:
        src=parts[name];o=src.copy();o.data=src.data;c.objects.link(o);o.parent=root
        if kind=='ieyasu':commander_silhouette(o)
        if o['palette_role']=='armor':o.material_slots[0].link='OBJECT';o.material_slots[0].material=armor
        if o['palette_role'] in hero_materials:o.material_slots[0].link='OBJECT';o.material_slots[0].material=hero_materials[o['palette_role']]
        actor_parts.append(o)
    source_roots.append(root)
    # Bake only the export copy. Source parts retain shared geometry and materials.
    bpy.ops.object.select_all(action='DESELECT')
    copies=[]
    for part_index,source in enumerate(actor_parts):
        o=source.copy();o.data=source.data.copy();bpy.context.collection.objects.link(o)
        o.parent=None # local coordinates: actor exported at origin
        if detailed:
            ids=o.data.attributes.new('BakePart','INT','POINT')
            for item in ids.data:item.value=part_index
        role=source['palette_role'];color=variant['armor'] if role=='armor' else COLORS[role]
        if detailed:color=palette.get(role,color)
        colors=o.data.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
        for i,color_data in enumerate(colors.data):
            wear=o.data.color_attributes['Wear'].data[i].color[0]
            color_data.color=(*(c*wear for c in color[:3]),1)
        o.data.color_attributes.remove(o.data.color_attributes['Wear'])
        # Blender renumbers trailing numeric suffixes on copies (glove.1 ->
        # glove.001). Use the authored identifier, never a guessed object name.
        bone=bone_for_part(source['part_name'])
        group=o.vertex_groups.new(name=bone);group.add(list(range(len(o.data.vertices))),1,'REPLACE')
        # Strip source materials after baking to guarantee one material/submesh.
        o.data.materials.clear();o.data.materials.append(materials['cloth'])
        o.select_set(True);copies.append(o)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.ops.object.join();joined=bpy.context.object;joined.name=kind+'_runtime'
    joined.data.materials.clear()
    if 'runtime/painted_palette' not in bpy.data.materials:
        painted_material('runtime/painted_palette',images,vertex=True)
    joined.data.materials.append(bpy.data.materials['runtime/painted_palette'])
    for poly in joined.data.polygons:poly.material_index=0
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    # Small-radius occlusion stays readable in flat winter light and costs no runtime pass.
    coords=[v.co.copy() for v in joined.data.vertices]
    tree=BVHTree.FromPolygons(coords,[tuple(p.vertices) for p in joined.data.polygons])
    factors=[]
    for v in joined.data.vertices:
        n=v.normal.normalized();t=n.cross(Vector((0,0,1)))
        if t.length<.01:t=n.cross(Vector((0,1,0)))
        t.normalize();b=n.cross(t)
        hits=0
        for j in range(8):
            angle=j*math.tau/8;direction=(n*.65+t*(math.cos(angle)*.76)+b*(math.sin(angle)*.76)).normalized()
            if tree.ray_cast(v.co+n*.004,direction,.15)[0] is not None:hits+=1
        factors.append(1-hits/8*.38)
    attr=joined.data.color_attributes['Color']
    for i,loop in enumerate(joined.data.loops):
        col=attr.data[i].color;f=factors[loop.vertex_index];attr.data[i].color=(col[0]*f,col[1]*f,col[2]*f,1)
    if detailed:
        occlusion=joined.data.attributes.new('HeroOcclusion','FLOAT','POINT')
        for i,item in enumerate(occlusion.data):item.value=factors[i]
        bake_hero(joined,actor_parts,{**COLORS,**palette},OUT,kind,2048 if kind=='yukimura' else 1024)
    joined.data.color_attributes.active_color_index=0
    joined.data.color_attributes.render_color_index=0
    joined.data.calc_loop_triangles()
    path=OUT/(kind+'.glb')
    rig=bind_hero(joined,kind)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_animations=bool(rig),export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)

    shared_images.update(share_images(path))
    stats[kind]={'triangles':len(joined.data.loop_triangles),'bytes':path.stat().st_size,'source_parts':len(names),'materials':1,'textures':3,'rigged':bool(rig)}
    if rig:
        # Keep a playable rig in source; modular static assemblies remain separately editable.
        rig.location=(0,3.5,0);joined.location=(0,0,0)
        rig.hide_render=True;joined.hide_render=True
    else:bpy.data.objects.remove(joined,do_unlink=True)
# Keep the library out of the assembled viewport, accessible through Outliner.
lib.hide_viewport=True;lib.hide_render=True
bpy.ops.object.select_all(action='DESELECT')
for root in source_roots:root.select_set(True)
bpy.context.view_layer.objects.active=source_roots[0]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.color_type='MATERIAL'
            area.spaces.active.region_3d.view_distance=9
            area.spaces.active.region_3d.view_location=(0,0,1.2)
bpy.context.scene['README']='Shared parts in 00_SHARED_PARTS. Four linked assemblies. Edit a shared mesh to update every variant. Runtime exports use a shared painted atlas; Yukimura also has an animated rig. No paid generation dependency.'
# Reference board lives in the .blend only; never exported into runtime GLBs.
reference=ROOT/'docs/art/yukimura-model-guide.png'
if reference.exists():
    reference_collection=bpy.data.collections.new('REFERENCE — adult proportions / lamellar silhouette')
    bpy.context.scene.collection.children.link(reference_collection)
    board=bpy.data.objects.new('2D modeling guide — not a game texture',None)
    reference_collection.objects.link(board)
    board.empty_display_type='IMAGE';board.empty_display_size=10
    board.data=bpy.data.images.load(str(reference));board.data.pack()
    board.rotation_euler=(math.pi/2,0,0);board.location=(0,2.2,1.5)
    board.color[3]=.65;board.hide_render=True;board.hide_viewport=True
for layer in bpy.context.view_layer.layer_collection.children:
    if layer.name.startswith('20_'):layer.exclude=False
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),compress=True)
report={'generator':'Blender local CPU / modular-samurai-v9-commanders-storm','unique_source_parts':len(parts),'variants':stats,'shared_textures':shared_images,'shared_texture_bytes':sum(shared_images.values()),'paid_api_calls':0}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
# Only generated, content-addressed images can be retired. Keep hand-added files.
for path in (OUT/'shared').glob('*.png'):
    if re.fullmatch(r'[a-f0-9]{16}\.png',path.name) and 'shared/'+path.name not in shared_images:
        path.unlink()
print(json.dumps(report,indent=2))
