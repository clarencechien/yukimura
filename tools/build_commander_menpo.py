"""v18: surface-fitted menpo over the v17 human head. No new textures or rig."""
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
from refine_commander_faces import fit, SOURCE, SOURCE_SHA
import hashlib

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / '.tmp/menpo-v18'
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
                    vertex.co.z-=inner*(.006 if kind=='yukimura' else .007)-outer*.0015
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
    verts = []
    for row, (z0, width) in enumerate(zip(levels, widths)):
        for col in range(cols + 1):
            u = col / cols * 2 - 1
            x = width * u * (1.045 if kind == 'ieyasu' else 1)
            z = z0 + (.022 if row < 4 else .012) * abs(u) ** 1.5
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
            verts.append(Vector((x, hit.y - gap, z)))
    count = len(verts)
    exterior = []
    for row in range(len(levels) - 1):
        for col in range(cols):
            if row == 4 and 6 <= col < 14:
                continue
            a = row * (cols + 1) + col
            exterior.append((a, a + cols + 1, a + cols + 2, a + 1))
    # A sparse shell may clear its own vertices yet slice through the nose
    # between them. Fit the complete skin vertex set into the shell envelope.
    skin_ids={i for p in polygons for i in p}
    for iteration in range(12):
        hull=BVHTree.FromPolygons(verts,exterior)
        corrections={}
        for i in skin_ids:
            p=mesh.data.vertices[i].co
            hit,_,face,_=hull.ray_cast(Vector((p.x,-1,p.z)),Vector((0,1,0)),2)
            if hit is not None:
                missing=.006-(p.y-hit.y)
                if missing>.00001:
                    for vertex in exterior[face]:corrections[vertex]=max(corrections.get(vertex,0),missing)
        if not corrections:break
        for i,amount in corrections.items():verts[i].y-=amount
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
    # Rolled top/bottom lips and gold cheek seam. Tubes share the existing atlas.
    for indices in [list(range(cols + 1)), list(range(8 * (cols + 1), 9 * (cols + 1)))]:
        out.tube([(verts[i] + Vector((0, -.0006, 0)), weight) for i in indices], .0013, 2, 4)
    for col in [0, cols]:
        out.tube([(verts[row * (cols + 1) + col], weight) for row in range(9)], .0013, 2, 4)
    # The opening is a genuine gap, framed by a narrow lip; the original mouth
    # remains visible behind it. Avoid opaque, painted "teeth" or bar moustaches.
    for row in [4, 5]:
        out.tube([(verts[row * (cols + 1) + col] + Vector((0, -.0008, 0)), weight)
                  for col in range(6, 15)], .0010, role, 4)
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
    report = {'shell_vertices': shell_count, 'vertices': len(out.v), 'shell_thickness_m': .002,
              'minimum_authored_front_clearance_m': .005, 'mouth_opening': True,
              'shared_material': mat.name, 'bone': 'body.head', 'new_textures': 0}
    return ob, report


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
    extra, report = menpo(mesh, kind)
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
    assert len(mesh.data.loop_triangles) <= 80000
    report['first_vertex'] = original_vertices
    mesh['menpo'] = json.dumps(report)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/optimized/commanders' / f'{kind}-menpo.blend'), compress=True)
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True); rig.select_set(True)
    target = OUT / f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True, export_yup=True,
        export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
        export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_extras=True)
    images = share_images(target)
    info = {'triangles': len(mesh.data.loop_triangles), 'bytes': target.stat().st_size,
            'bones': len(rig.data.bones), 'materials': len(mesh.data.materials), 'textures': images, 'menpo': report}
    assert info['bytes'] < 6100000
    (STAGE / f'{kind}.json').write_text(json.dumps(info, indent=2) + '\n')
    print(kind, info['triangles'], info['bytes'], flush=True)


if __name__ == '__main__':
    expressions=battle_expressions()
    for kind in ['yukimura', 'ieyasu']: run(kind,expressions[kind])
