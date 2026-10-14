"""v18/v19 fitted menpo and v20 embossed menpo over the shared v17 head."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detail_commanders import Fittings
from gltf_assets import share_images
from refine_commander_faces import fit, components, SOURCE, SOURCE_SHA
import hashlib

ROOT = Path(__file__).resolve().parents[1]
TRIAL = '--trial' in sys.argv
SCULPT = '--sculpt' in sys.argv or TRIAL
VISOR = '--visor' in sys.argv or SCULPT
STAGE = ROOT / ('.tmp/menpo-v21' if TRIAL else '.tmp/menpo-v20' if SCULPT else '.tmp/menpo-v19' if VISOR else '.tmp/menpo-v18')
OUT = STAGE / 'models'
OUT.mkdir(parents=True, exist_ok=True)


def battle_expressions():
    """Bake the source artist's anatomical brow/lid targets, not an eye-bar mesh."""
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    source=next(o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.materials)==3)
    material=next(i for i,m in enumerate(source.data.materials) if m.name=='m024_head')
    ids=sorted({i for p in source.data.polygons if p.material_index==material for i in p.vertices})
    keys=source.data.shape_keys.key_blocks
    result={}
    for kind in ['yukimura','ieyasu']:
        values={'AK_01_BrowDownLeft':.98 if kind=='yukimura' else 1.0,
                'AK_02_BrowDownRight':.90 if kind=='yukimura' else 1.0,
                'AK_09_EyeBlinkLeft':.22 if kind=='yukimura' else .26,
                'AK_10_EyeBlinkRight':.20 if kind=='yukimura' else .26}
        if VISOR:
            values['AK_01_BrowDownLeft']=1.12
            values['AK_02_BrowDownRight']=1.06 if kind=='yukimura' else 1.12
        fitted=[]
        for active in [False,True]:
            positions=[]
            for i in ids:
                p=source.data.vertices[i].co.copy()
                for name,value in values.items():
                    strength=value if active else .22 if 'BrowDown' in name else 0
                    p+=(keys[name].data[i].co-source.data.vertices[i].co)*strength
                positions.append(source.matrix_world@p)
            data=bpy.data.meshes.new('expression fitting');data.from_pydata(positions,[],[])
            ob=bpy.data.objects.new('expression fitting',data)
            fit(ob,None,kind)
            if active:
                for vertex in data.vertices:
                    x,y,z=vertex.co
                    front=max(0,min(1,(-y-.17)/.07))
                    inner=math.exp(-((abs(x)-.025)/.019)**2-((z-1.927)/.012)**2)*front
                    outer=math.exp(-((abs(x)-.067)/.020)**2-((z-1.933)/.011)**2)*front
                    furrow=math.exp(-((abs(x)-.012)/.003)**2-((z-1.953)/.024)**2)*front
                    compression=(.009 if kind=='yukimura' else .010) if VISOR else (.006 if kind=='yukimura' else .007)
                    vertex.co.z-=inner*compression-outer*.0015
                    vertex.co.y-=inner*.0035-furrow*.002
            fitted.append([v.co.copy() for v in data.vertices])
            bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(data)
        result[kind]={'before':fitted[0],'after':fitted[1],'targets':values}
    return result


def menpo(mesh, kind):
    skin = next(i for i, m in enumerate(mesh.data.materials) if m.name.startswith('human skin /'))
    polygons = [list(p.vertices) for p in mesh.data.polygons if p.material_index == skin]
    surface = BVHTree.FromPolygons([v.co for v in mesh.data.vertices], polygons)
    out = Fittings(kind)
    # Reuse atlas quadrant 3 (lacquer) or 1 (hammered iron), with gold rims in 2.
    role = 3 if kind == 'yukimura' else 1
    weight = {'body.head': 1.0}
    cols = 20
    levels = [1.869, 1.852, 1.834, 1.819, 1.808, 1.798, 1.781, 1.760, 1.744]
    widths = [.107, .113, .115, .111, .106, .099, .086, .064, .039]
    if VISOR:
        # User-provided armour photographs: projecting nose, cheek creases,
        # open mouth frame and rounded jaw, paired with a low kabuto brim.
        levels=[1.887,1.871,1.855,1.837,1.819,1.811,1.773,1.757,1.743,1.739]
        widths=[.119,.120,.117,.115,.108,.102,.093,.080,.065,.050]
    verts = []
    for row, (z0, width) in enumerate(zip(levels, widths)):
        for col in range(cols + 1):
            u = col / cols * 2 - 1
            x = width * u * (1.045 if kind == 'ieyasu' else 1)
            slope=(.010 if row==2 else .014 if row==3 else .004 if row<2 else .012) if VISOR else (.022 if row<4 else .012)
            z = z0 + slope * abs(u) ** 1.5
            if VISOR:
                z=z0+.012*u*u
                if row==0:z=1.887+.044*math.exp(-(u/.19)**2)+.015*u*u
                elif row==1:z=1.871+.035*math.exp(-(u/.30)**2)+.013*u*u
                elif row==2:z=1.855+.008*math.exp(-(u/.4)**2)+.012*u*u
                elif row==5:z=1.817-.010*math.exp(-(u/.30)**2)
                elif row==6:z=1.786-.010*math.exp(-(u/.65)**2)
                elif row>=7:z=z0+.009*u*u
            # Fit to actual skin including the nose, rather than an ideal sphere.
            hit, _, _, _ = surface.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
            if hit is None:
                for shrink in [.98, .94, .90, .86, .82]:
                    hit, _, _, _ = surface.ray_cast(Vector((x * shrink, -1, z)), Vector((0, 1, 0)), 2)
                    if hit is not None:
                        x *= shrink
                        break
            assert hit is not None, (kind, row, col)
            # Raised cheek creases and nose/chin modelling in the metal shell.
            cheek = math.exp(-((abs(u) - .63) / .21) ** 2) * math.exp(-((row - 2.3) / 1.7) ** 2)
            chin = math.exp(-(u / .65) ** 2) * math.exp(-((row - 6.5) / 1.2) ** 2)
            gap = .007 + cheek * .006 + chin * .006
            if VISOR:
                nasal=math.exp(-(x/.030)**4-((z-1.883)/.045)**2)
                tip=math.exp(-(x/.016)**2-((z-1.856)/.014)**2)
                wings=math.exp(-((abs(x)-.028)/.012)**2-((z-1.864)/.013)**2)
                cheek=math.exp(-((abs(x)-.074)/.017)**2-((z-1.846)/.028)**2)
                jaw=math.exp(-(x/.060)**4-((z-1.751)/.017)**2)
                gap=.010+.050*nasal+.034*tip+.025*wings+.028*cheek+.022*jaw
            verts.append(Vector((x, hit.y - gap, z)))
    if VISOR:
        # Taper each nostril into a nasal wing; no rectangular punched vents.
        for col in [7,12]:
            ids=[2*21+col,3*21+col,3*21+col+1,2*21+col+1]
            center=sum((verts[i] for i in ids),Vector())/4
            for n,i in enumerate(ids):
                verts[i].x=center.x+(verts[i].x-center.x)*(.60 if n in (0,3) else .95)
                verts[i].z=center.z+(verts[i].z-center.z)*.55
                verts[i].y-=.014
    count = len(verts)
    exterior = []; openings=[]
    for row in range(len(levels) - 1):
        for col in range(cols):
            a = row * (cols + 1) + col
            if (VISOR and ((row==5 and 5<=col<15) or (row==2 and col in (7,12)))) or (not VISOR and row==4 and 6<=col<14):
                openings.append((a,a+cols+1,a+cols+2,a+1));continue
            exterior.append((a, a + cols + 1, a + cols + 2, a + 1))
    if VISOR:
        # Make the fitting BVH and exported mesh use the exact same diagonals.
        # Non-planar quads otherwise triangulate differently during glTF export.
        exterior=[tri for a,b,c,d in exterior for tri in [(a,b,c),(a,c,d)]]
    # A sparse shell may clear its own vertices yet slice through the nose
    # between them. Fit the complete skin vertex set into the shell envelope.
    skin_ids={i for p in polygons for i in p}
    probes=[mesh.data.vertices[i].co for i in skin_ids]
    if VISOR:
        mesh.data.calc_loop_triangles()
        for tri in mesh.data.loop_triangles:
            if tri.material_index!=skin:continue
            a,b,c=[mesh.data.vertices[i].co for i in tri.vertices]
            probes.extend([(a+b)/2,(b+c)/2,(c+a)/2,(a+b+c)/3])
    for iteration in range(12):
        hull=BVHTree.FromPolygons(verts,exterior)
        corrections={}
        for p in probes:
            hit,_,face,_=hull.ray_cast(Vector((p.x,-1,p.z)),Vector((0,1,0)),2)
            if hit is not None:
                missing=(.009 if VISOR else .006)-(p.y-hit.y)
                if missing>.00001:
                    for vertex in exterior[face]:corrections[vertex]=max(corrections.get(vertex,0),missing)
        if not corrections:break
        for i,amount in corrections.items():verts[i].y-=amount
    coverage={}
    if VISOR:
        hull=BVHTree.FromPolygons(verts,exterior)
        for name,x,z,covered in [('forehead',0,1.94,False),('nose',0,1.845,True),
                ('mouth',0,1.795,False),('chin',0,1.75,True),('bridge',0,1.900,True),
                ('left_eye',-.040,1.900,False),('right_eye',.040,1.900,False)]:
            hit,_,_,_=hull.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
            coverage[name]=hit is not None
            assert coverage[name]==covered, f'{kind}: visor coverage at {name}'
    # 2 mm shell, explicit interior and perimeter walls, including the mouth slit.
    verts += [v + Vector((0, .002, 0)) for v in verts]
    faces = exterior + [tuple(i + count for i in reversed(f)) for f in exterior]
    edges = {}
    for f in exterior:
        for a, b in zip(f, f[1:] + f[:1]):
            key = tuple(sorted((a, b)))
            if key in edges: del edges[key]
            else: edges[key] = (a, b)
    faces += [(b, a, a + count, b + count) for a, b in edges.values()]
    uv = [(i % (cols + 1) / cols, i // (cols + 1) / (len(levels) - 1)) for i in range(count)] * 2
    out.add(verts, faces, uv, [weight] * len(verts), role)
    shell_count = len(verts)
    dark_ids=set();hair_ids=set()
    # Rolled top/bottom lips and gold cheek seam. Tubes share the existing atlas.
    for indices in [list(range(cols + 1)), list(range((len(levels)-1) * (cols + 1), len(levels) * (cols + 1)))]:
        out.tube([(verts[i] + Vector((0, -.0006, 0)), weight) for i in indices], .0013, role if VISOR and kind=='yukimura' else 2, 3 if VISOR else 4)
    for col in [0, cols]:
        out.tube([(verts[row * (cols + 1) + col], weight) for row in range(len(levels))], .0013, role if VISOR and kind=='yukimura' else 2, 3 if VISOR else 4)
    # The opening is a genuine gap, framed by a narrow lip; the original mouth
    # remains visible behind it. Avoid opaque, painted "teeth" or bar moustaches.
    for row in ([] if VISOR else [4, 5]):
        out.tube([(verts[row * (cols + 1) + col] + Vector((0, -.0008, 0)), weight)
                  for col in range(6, 15)], .0010, role, 4)
    if VISOR:
        # Dark recessed interiors hide the actor's lips; sculpted mouth and
        # nostrils read as metal cavities instead of holes in a fabric mask.
        for f in openings:
            start=len(out.v)
            out.add([verts[i]+Vector((0,.003,0)) for i in f],[(0,1,2),(0,2,3)],[(0,0),(0,1),(1,1),(1,0)],[weight]*4,0)
            dark_ids.update(range(start,len(out.v)))
        for row in [5,6]:
            out.tube([(verts[row*21+col]+Vector((0,-.001,0)),weight) for col in range(5,16)],.0024,role if kind=='yukimura' else 2,3)
        for col in [7,12]:
            ids=[2*21+col,3*21+col,3*21+col+1,2*21+col+1,2*21+col]
            out.tube([(verts[i],weight) for i in ids],.0015,role,3)
        for col in [5,15]:
            out.tube([(verts[row*21+col]+Vector((0,-.001,0)),weight) for row in [5,6]],.0024,role if kind=='yukimura' else 2,3)
        # Firm cheek folds, following the punched/raised lines in the references.
        for col in [4,16]:
            out.tube([(verts[row*21+col]+Vector((0,-.0014,0)),weight) for row in [2,3,4,5,6]],.0022,role,3)
        if kind=='ieyasu':
            # Fine grey moustache strands and a restrained gilded tooth edge.
            for side in [-1,1]:
                for strand in range(5):
                    path=[]
                    for t in [0,.33,.66,1]:
                        x=side*(.011+t*.043);z=1.818+.009*math.sin(t*math.pi)+(strand-2)*.0015
                        hit,_,_,_=hull.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
                        y=hit.y-.003 if hit is not None else -.290
                        p=Vector((x,y,z));path.append((p,weight))
                    start=len(out.v);out.tube(path,.00085,0,3);hair_ids.update(range(start,len(out.v)))
            for col in range(6,15):
                p=verts[5*21+col]+Vector((0,-.0005,-.001))
                out.add([p+Vector((-.002,0,0)),p+Vector((.002,0,0)),p+Vector((.001,0,-.004)),p+Vector((-.001,0,-.004))],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)],[weight]*4,2)
    mat = next(m for m in mesh.data.materials if m.name == 'samurai woven cords and fittings')
    ob = out.object(mat)
    ob.name = 'surface-fitted menpo'
    # Normals from the ordered shell should face outwards (-Y on the exterior).
    assert ob.data.polygons[0].normal.y < 0
    # Slightly warmer/redder lacquer and near-black iron; retain the atlas ORM.
    ca = ob.data.color_attributes['Color']
    for loop in ob.data.loops:
        if out.roles[loop.vertex_index] == role:
            ca.data[loop.index].color = (.19, .008, .012, 1) if kind == 'yukimura' else (.025, .027, .028, 1)
        if loop.vertex_index in dark_ids:ca.data[loop.index].color=(.002,.0015,.001,1)
        if loop.vertex_index in hair_ids:ca.data[loop.index].color=(.42,.39,.32,1)
        if VISOR and out.roles[loop.vertex_index]==role:
            # Smooth lacquer/iron on the broad plate. The construction atlas's
            # coarse repeated relief belongs on fittings, not across the face.
            uv=ob.data.uv_layers.active.data[loop.index].uv
            center=Vector((.75,.75 if role==3 else .25))
            uv[:]=center+(uv-center)*.008
    report = {'shell_vertices': shell_count, 'vertices': len(out.v), 'shell_thickness_m': .002,
              'minimum_authored_front_clearance_m': .005, 'mouth_opening': True,
              'eye_openings':0,'reference_form':'photograph-guided menpo with low kabuto' if VISOR else 'v18',
              'shared_material': mat.name, 'bone': 'body.head', 'new_textures': 0}
    if VISOR:report['coverage_rays']=coverage
    return ob, report


def seat_helmet(mesh):
    skin=next(i for i,m in enumerate(mesh.data.materials) if m.name.startswith('human skin /'))
    skin_ids={i for p in mesh.data.polygons if p.material_index==skin for i in p.vertices}
    head=mesh.vertex_groups['body.head'].index
    count=0;brim=[]
    for comp in components(mesh):
        if any(v.index in skin_ids for v in comp):continue
        if min(v.co.z for v in comp)<1.735:continue
        if any(sum(g.weight for g in v.groups if g.group==head)<.99 for v in comp):continue
        is_brim=len(comp) in (264,266) and max(v.co.y for v in comp)<-.2
        before=min(v.co.z for v in comp)
        for v in comp:
            t=max(0,min(1,(v.co.z-1.77)/.20))
            v.co.x*=1-.04*t
            v.co.y=-.085+(v.co.y+.085)*(1-.04*t)
            v.co.z-=.045*t
            count+=1
        if is_brim:brim.append({'before_z':before,'after_z':min(v.co.z for v in comp)})
    assert count>4000 and len(brim)==1, 'Helmet selection changed'
    mesh.data.update()
    return {'vertices':count,'crown_lowered_m':.045,'lateral_scale':.96,'brim':brim}


def run(kind, expression):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'assets/optimized/commanders' / f'{kind}-face.blend'))
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    mesh = next(o for o in scene.objects if o.type == 'MESH' and o.parent == rig)
    # Keep the jaw rigid with the cranium. The v17 height-only neck blend reached
    # the chin, causing skin to move through a rigid menpo during a strong turn.
    skin=next(i for i,m in enumerate(mesh.data.materials) if m.name.startswith('human skin /'))
    ids={i for p in mesh.data.polygons if p.material_index==skin for i in p.vertices}
    assert len(ids)==len(expression['before'])
    for i,before,after in zip(sorted(ids),expression['before'],expression['after']):
        assert (mesh.data.vertices[i].co-before).length<.00001, 'Source head vertex mapping changed'
        mesh.data.vertices[i].co=after
    head=mesh.vertex_groups['body.head'];chest=mesh.vertex_groups['body.spine02']
    for i in ids:
        t=max(0,min(1,(mesh.data.vertices[i].co.z-1.64)/.10));t=t*t*(3-2*t)
        head.add([i],t,'REPLACE');chest.add([i],1-t,'REPLACE')
    original_vertices = len(mesh.data.vertices)
    helmet=seat_helmet(mesh) if VISOR else None
    if SCULPT:
        from sculpt_menpo import sculpted_menpo
        extra, report = sculpted_menpo(mesh, kind, slim=TRIAL)
    else:
        extra, report = menpo(mesh, kind)
    if VISOR:report['helmet_fit']=helmet
    report['battle_expression']={'source_targets':expression['targets'],'baked_static':True,
                                 'runtime_morph_targets':0,'sculpt':'inner brow compression, raised brow ridge and glabella furrows'}
    extra.data.uv_layers.active.name = mesh.data.uv_layers.active.name
    for attr in mesh.data.color_attributes:
        if extra.data.color_attributes.get(attr.name) is None:
            layer = extra.data.color_attributes.new(name=attr.name, type=attr.data_type, domain=attr.domain)
            for value in layer.data: value.color = (1, 1, 1, 1)
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True); extra.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    mesh.data.calc_loop_triangles()
    assert len(mesh.data.loop_triangles) <= (90000 if SCULPT else 80000)
    if TRIAL:
        from technique_trial import apply_technique
        report['technique_trial']=apply_technique(rig,mesh,kind)
    report['first_vertex'] = original_vertices
    mesh['menpo'] = json.dumps(report)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/optimized/commanders' / f'{kind}-{"trial" if TRIAL else "sculpt" if SCULPT else "visor" if VISOR else "menpo"}.blend'), compress=True)
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True); rig.select_set(True)
    target = OUT / f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True, export_yup=True,
        export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
        export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_extras=True)
    images = share_images(target)
    info = {'triangles': len(mesh.data.loop_triangles), 'bytes': target.stat().st_size,
            'bones': len(rig.data.bones), 'materials': len(mesh.data.materials), 'textures': images, 'menpo': report}
    assert info['bytes'] < (7000000 if SCULPT else 6100000)
    (STAGE / f'{kind}.json').write_text(json.dumps(info, indent=2) + '\n')
    print(kind, info['triangles'], info['bytes'], flush=True)


if __name__ == '__main__':
    expressions=battle_expressions()
    for kind in ['yukimura', 'ieyasu']: run(kind,expressions[kind])
