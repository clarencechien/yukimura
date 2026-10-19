"""Stage 4c: place the generated parts on the fitted body and bind each rigidly to one game bone.

Layout (parts-layout.json) per part:
  file      GLB (TRELLIS closed export or procedural)
  bone      game bone the part follows (side suffix filled in per copy: {S})
  anchor    [bone, t]: point along bone segment head->child head (t = 0..1), or [bone] for the head
  align     optional [bone_a, bone_b]: rotate the part's long (Z) axis onto that segment
  size      metres of the part's largest dimension
  offset    metres, added in world space (x is mirrored for the other side)
  rotate    euler degrees applied to the part before alignment (part frame: front -Y, up +Z)
  sides     ["R"] / ["R", "L"]: physical +X is the game's '.R' side; the drawn left parts go there
  clip      optional {"keep": "front"|"back", "y": metres}: cut the part at a world plane y
  decimate  target triangles per copy

Every part's vertices get weight 1 on its bone (rigid plates, as in the shipped commanders).
"""
from pathlib import Path
import argparse, json, math, sys
import bpy, bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(); p.add_argument('--body', required=True); p.add_argument('--layout', required=True); p.add_argument('--output', required=True)
p.add_argument('--only', help='comma list of parts to include')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
layout = json.loads(Path(a.layout).read_text())
bpy.ops.wm.open_mainfile(filepath=str(Path(a.body).resolve()))
scene = bpy.context.scene
rig = next(o for o in scene.objects if o.type == 'ARMATURE'); W = rig.matrix_world
head = {b.name: W @ b.head_local for b in rig.data.bones}

def point_on(spec, side):
    name = spec[0].replace('{S}', side)
    if len(spec) == 1: return head[name].copy()
    if len(spec) == 3: return head[name].lerp(head[spec[2].replace('{S}', side)], spec[1])   # [bone_a, t, bone_b]
    # segment towards the nearest child head (the game bones' own tails point up; see build_body.py)
    kids = [c.name for c in rig.data.bones[name].children]
    child = min(kids, key=lambda c: (head[c] - head[name]).length) if kids else None
    end = head[child] if child else head[name]
    return head[name].lerp(end, spec[1])

def body_material():
    m = bpy.data.materials.new('Undersuit black mech fabric'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (.022, .02, .022, 1); b.inputs['Roughness'].default_value = .55
    b.inputs['Metallic'].default_value = .25
    return m
body = next(o for o in scene.objects if o.type == 'MESH')
body.data.materials.clear(); body.data.materials.append(body_material())
# Body regions the armour replaces outright (feet inside boots, hands inside gauntlets) are cut
# away so they cannot poke through.
hide = tuple(layout.get('hide_body', []))
if hide:
    idx = {g.index for g in body.vertex_groups if g.name.startswith(hide)}
    bm = bmesh.new(); bm.from_mesh(body.data); dl = bm.verts.layers.deform.active
    doomed = [v for v in bm.verts if sum(w for gi, w in v[dl].items() if gi in idx) > .5]
    bmesh.ops.delete(bm, geom=doomed, context='VERTS'); bm.to_mesh(body.data); bm.free()

report = {}
for name, spec in layout['parts'].items():
    if a.only and name not in a.only.split(','): continue
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str((ROOT / spec['file']).resolve()))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        w = o.matrix_world.copy(); o.parent = None; o.data.transform(w); o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    src = bpy.context.view_layer.objects.active; src.name = f'Part / {name}'
    if spec.get('decimate'):
        tris = sum(len(f.vertices) - 2 for f in src.data.polygons)
        if tris > spec['decimate']:
            d = src.modifiers.new('budget', 'DECIMATE'); d.ratio = spec['decimate'] / tris; bpy.ops.object.modifier_apply(modifier=d.name)
    # Normalise: bbox centre at the origin, largest dimension = 1.
    vs = [v.co for v in src.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    src.data.transform(Matrix.Scale(1 / max(hi - lo), 4) @ Matrix.Translation(-(lo + hi) / 2))
    if spec.get('pca'):
        # Long principal axis onto +Z, keeping it pointing the way the part's +Z already leaned.
        import numpy as np
        P = np.array([v.co for v in src.data.vertices]); P = P[::max(1, len(P) // 20000)]
        axis = Vector(np.linalg.svd(P - P.mean(0), full_matrices=False)[2][0])
        if axis.z < 0: axis = -axis
        src.data.transform(axis.rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4())
        vs = [v.co for v in src.data.vertices]
        lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
        src.data.transform(Matrix.Scale(1 / max(hi - lo), 4) @ Matrix.Translation(-(lo + hi) / 2))
    rot = Matrix.Rotation(0, 4, 'Z')
    for axis, deg in zip('XYZ', spec.get('rotate', [0, 0, 0])): rot = Matrix.Rotation(math.radians(deg), 4, axis) @ rot
    src.data.transform(Matrix.Scale(spec['size'], 4) @ rot)
    copies = []; base = src.data.copy()
    for k, side in enumerate(spec.get('sides', ['R'])):
        ob = src if k == 0 else src.copy()
        if k:
            ob.data = base.copy(); scene.collection.objects.link(ob)
            ob.modifiers.clear()                      # the copy carries the first side's armature modifier: deforming twice
        ob.name = f'Part / {name}' + (f' {side}' if len(spec.get('sides', [])) > 1 else '')
        M = Matrix.Identity(4)
        if spec.get('align'):
            pa, pb = point_on([spec['align'][0]], side), point_on([spec['align'][1]], side)
            d = (pa - pb).normalized()                        # part +Z (up) points from the distal joint to the proximal one
            M = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
        off = Vector(spec.get('offset', [0, 0, 0]))
        if side == 'L':
            ob.data.transform(Matrix.Diagonal(Vector((-1, 1, 1, 1))))     # mirror to the other side
            ob.data.flip_normals(); off.x = -off.x
        ob.data.transform(Matrix.Translation(point_on(spec['anchor'], side) + off) @ M)
        if spec.get('clip'):
            bm = bmesh.new(); bm.from_mesh(ob.data)
            keep_front = spec['clip']['keep'] == 'front'
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, spec['clip']['y'], 0), plane_no=(0, 1, 0), clear_outer=keep_front, clear_inner=not keep_front)
            bm.to_mesh(ob.data); bm.free()
        bone = spec['bone'].replace('{S}', side)
        assert bone in rig.data.bones, bone
        ob.vertex_groups.clear(); g = ob.vertex_groups.new(name=bone)
        if spec.get('blend'):
            # Hanging plates: rigid on `bone` at the top, handing over to the thigh towards the bottom.
            b2 = spec['blend']['bone'].replace('{S}', side); assert b2 in rig.data.bones, b2
            g2 = ob.vertex_groups.new(name=b2); zs = [v.co.z for v in ob.data.vertices]; top, bot = max(zs), min(zs)
            for v in ob.data.vertices:
                w2 = spec['blend']['max'] * ((top - v.co.z) / (top - bot)) ** 1.5
                g.add([v.index], 1 - w2, 'REPLACE'); g2.add([v.index], w2, 'REPLACE')
        else:
            g.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
        ob.parent = rig; mod = ob.modifiers.new('rigid on ' + bone, 'ARMATURE'); mod.object = rig
        for poly in ob.data.polygons: poly.use_smooth = True
        copies.append({'object': ob.name, 'bone': bone, 'triangles': sum(len(f.vertices) - 2 for f in ob.data.polygons)})
    report[name] = copies
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
print(json.dumps({'parts': report, 'total_triangles': sum(c['triangles'] for v in report.values() for c in v)}))
