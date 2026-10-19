"""Rebuild the neck cords after the reference illustration.

The reference ties a braided red chin cord from both sides of the mask down to a knot at
the throat, with two fringed tassels hanging side by side, and hangs a braided cord with a
long fringed tassel from each gold shoulder fitting. TRELLIS gave one off-centre cone and two
flat 'paddles' with knobs. This removes those (faces standing clear in front of the local
chest surface inside hand-measured boxes) and builds three-strand twisted cords, knots and
strand fringes along paths placed on the surface by rays from the front.
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cord_geometry import catmull, frames, tube, braided_cord, knot, fringe

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--output', required=True)
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--flow-cache', default='.tmp/v3/flow.npz')
p.add_argument('--clear-only', action='store_true', help='Remove / flatten the generated cords only; tie_cords.py builds the new ones')
a = p.parse_args()

# Boxes (x0, x1, z0, z1) measured on a gridded unlit front render (front = -Y).
REMOVE = {'centre cone tassel': (-.08, -.02, 1.44, 1.535)}
# Paddles are fused into the chest: deleting them tears holes. Flatten them onto the chest.
FLATTEN = {'right paddle tassel': (-.20, -.14, 1.355, 1.51), 'left paddle tassel': (.07, .132, 1.385, 1.505)}
COIL = (-.105, .095, 1.47, 1.565)    # TRELLIS's lumpy chin coil (removed by its cord-red texture)
CORD_R = .0075                       # braided chin cord radius (reference: thick kumihimo)
SIDE_R = .006                        # shoulder cords

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
objs = list(bpy.context.scene.objects)
body = next(o for o in objs if o.data.materials and o.data.materials[0].name.startswith('Body v2'))

# 1. Remove the old tassels: faces inside each box that stand clear in front of the chest.
bm = bmesh.new(); bm.from_mesh(body.data); bm.faces.ensure_lookup_table()
cen = np.array([f.calc_center_median() for f in bm.faces])
removed = {}
for name, (x0, x1, z0, z1) in REMOVE.items():
    inside = (cen[:, 0] > x0) & (cen[:, 0] < x1) & (cen[:, 2] > z0) & (cen[:, 2] < z1)
    ring = (cen[:, 0] > x0 - .03) & (cen[:, 0] < x1 + .03) & (cen[:, 2] > z0) & (cen[:, 2] < z1) & ~inside & (cen[:, 1] < .05)
    # Chest plane behind the tassel: a typical depth of the faces just around the box.
    chest = np.percentile(cen[ring, 1], 35)
    kill = inside & (cen[:, 1] < chest - .006)
    removed[name] = {'faces': int(kill.sum()), 'chest_y': float(chest)}
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.where(kill)[0]], context='FACES')
    bm.faces.ensure_lookup_table(); cen = np.array([f.calc_center_median() for f in bm.faces])
# Old chin coil: cord-red faces in front of the neck. Behind it is the dark neck lining,
# which matches the reference (dark cloth behind the cords).
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from trellis_body_materials import rgb_to_hsv
img = body.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node.image
W, H = img.size; tex = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(tex); tex = tex.reshape(H, W, 4)
uvl = bm.loops.layers.uv.active
x0, x1, z0, z1 = COIL
box = [f for f, c in zip(bm.faces, cen) if x0 < c[0] < x1 and z0 < c[2] < z1 and c[1] < -.02]
if box:
    fuv = np.array([np.mean([l[uvl].uv for l in f.loops], 0) for f in box])
    col = tex[np.clip((fuv[:, 1] * H).astype(int), 0, H - 1), np.clip((fuv[:, 0] * W).astype(int), 0, W - 1), :3]
    h, s_, v_ = rgb_to_hsv(col)
    red = (np.abs(((h + 180) % 360) - 180) < 16) & (s_ > .55) & (v_ > .3)
    bmesh.ops.delete(bm, geom=[f for f, r in zip(box, red) if r], context='FACES')
    removed['chin coil (cord-red faces)'] = {'faces': int(red.sum())}
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(body.data); bm.free()

# 2. Flatten the paddles: fit the chest from a ring of rays just outside each box (clean
# chest), then push every vertex in front of that surface back onto it, 1.5 mm proud.
bm_all = bmesh.new()
for o in objs: bm_all.from_mesh(o.data)
tree0 = BVHTree.FromBMesh(bm_all); bm_all.free()
flattened = {}
co = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
for name, (x0, x1, z0, z1) in FLATTEN.items():
    ring = []
    for x in np.arange(x0 - .012, x1 + .0121, .003):
        for z in np.arange(z0 - .012, z1 + .0121, .003):
            if x0 - .002 < x < x1 + .002 and z0 - .002 < z < z1 + .002: continue
            hit = tree0.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
            if hit[0] is not None: ring.append(hit[0][:])
    ring = np.array(ring)
    A = lambda X, Z: np.stack([np.ones_like(X), X, Z, X * X, X * Z, Z * Z], -1)
    keep = np.ones(len(ring), bool)
    for _ in range(6):
        coef, *_ = np.linalg.lstsq(A(ring[keep, 0], ring[keep, 2]), ring[keep, 1], rcond=None)
        res = ring[:, 1] - A(ring[:, 0], ring[:, 2]) @ coef
        keep = np.abs(res - np.median(res[keep])) < 2.5 * np.std(res[keep]) + 1e-4
    inside = (co[:, 0] > x0) & (co[:, 0] < x1) & (co[:, 2] > z0) & (co[:, 2] < z1)
    target = A(co[:, 0], co[:, 2]) @ coef - .0015
    move = inside & (co[:, 1] < target)
    co[move, 1] = target[move]
    flattened[name] = {'vertices_moved': int(move.sum()), 'ring_points': int(len(ring)), 'ring_kept': int(keep.sum())}
body.data.vertices.foreach_set('co', co.ravel()); body.data.update()
if a.clear_only:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
    Path(a.output).with_name('neck-clear-report.json').write_text(json.dumps({'removed': removed, 'flattened': flattened}, indent=2) + '\n')
    print(json.dumps({'removed': removed, 'flattened': flattened})); raise SystemExit
bm_all = bmesh.new()
for o in objs: bm_all.from_mesh(o.data)
tree = BVHTree.FromBMesh(bm_all); bm_all.free()
def surface(x, z, lift):
    """Front-most surface point at (x, z), lifted toward the viewer."""
    hit = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 2.0)
    n = np.array(hit[1]); n = -n if n[1] > 0 else n
    return np.array(hit[0]) + n * lift

rng = np.random.default_rng(1615)
cord_bm = bmesh.new()
built = {}
# Chin cords: from each side of the mask's lower edge down under the chin to the throat knot.
knot_c = surface(-.006, 1.468, CORD_R * 2.2)
for side in (-1, 1):
    pts = [surface(side * .072, 1.555, CORD_R * 1.3), surface(side * .066, 1.525, CORD_R * 1.3),
           surface(side * .045, 1.495, CORD_R * 1.4), surface(side * .02, 1.477, CORD_R * 1.8), knot_c]
    braided_cord(cord_bm, catmull(pts, 10), CORD_R)
knot(cord_bm, knot_c, CORD_R * 2.0)
# Two tassels side by side under the knot.
for dx in (-.017, .014):
    head = surface(knot_c[0] + dx, knot_c[2] - .026, CORD_R * 2.2)
    braided_cord(cord_bm, catmull([knot_c + np.array([dx * .3, -.001, -.004]), head + np.array([0, 0, .006])], 6), CORD_R * .8)
    knot(cord_bm, head, CORD_R * 1.45)
    fringe(cord_bm, head + np.array([0, 0, -CORD_R * 1.1]), .086, CORD_R * 2.3, rng, strands=72)
built['chin'] = {'knot': knot_c.round(4).tolist(), 'tassels': 2}
# Shoulder cords: from the old knob positions, a short cord, knot and long fringe.
for name, x, z in (('right shoulder cord', -.172, 1.492), ('left shoulder cord', .103, 1.486)):
    top = surface(x, z, SIDE_R * 1.6); mid = surface(x + .002, z - .045, SIDE_R * 2.2)
    braided_cord(cord_bm, catmull([top, surface(x + .001, z - .02, SIDE_R * 1.9), mid], 8), SIDE_R)
    knot(cord_bm, mid, SIDE_R * 1.7)
    fringe(cord_bm, mid + np.array([0, 0, -SIDE_R * 1.3]), .105, SIDE_R * 2.9, rng, strands=80)
    built[name] = {'top': top.round(4).tolist(), 'knot': mid.round(4).tolist()}

mesh = bpy.data.meshes.new('Neck cords'); cord_bm.normal_update(); cord_bm.to_mesh(mesh); cord_bm.free()
for poly in mesh.polygons: poly.use_smooth = True
mat = bpy.data.materials.new('Braided silk cord / lacquer red'); mat.use_nodes = True
bs = mat.node_tree.nodes['Principled BSDF']
bs.inputs['Base Color'].default_value = (.16, .008, .008, 1); bs.inputs['Roughness'].default_value = .72
bs.inputs['Specular IOR Level'].default_value = .25; bs.inputs['Sheen Weight'].default_value = .05; bs.inputs['Sheen Tint'].default_value = (1, .45, .4, 1)
mesh.materials.append(mat)
cords = bpy.data.objects.new('Neck cords / braided silk', mesh); bpy.context.collection.objects.link(cords)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
report = {'removed': removed, 'flattened': flattened, 'built': built, 'cord_triangles': sum(len(f.vertices) - 2 for f in mesh.polygons), 'cord_radius': CORD_R, 'shoulder_cord_radius': SIDE_R}
Path(a.output).with_name('cords-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
