"""Rebuild the waist cord after the reference: thick braid, big knot with bow loops, two tassels.

TRELLIS made the waist cord a smooth tube with a glossy heart-shaped knot and two smooth
tassels. The old knot and tassels are flattened onto the surface behind them (deleting fused
geometry tears holes); a braided cord is laid around the waist on a ray-cast path that skips
the hanging forearms, and a knot, two bow loops and two fringed tassels are built at the front.
"""
from pathlib import Path
import argparse, json, sys
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import bmesh
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cord_geometry import catmull, braided_cord, knot, fringe, loop

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--output', required=True)
p.add_argument('--clear-only', action='store_true', help='Flatten the generated knot only; tie_cords.py builds the new cord')
a = p.parse_args()

FLATTEN = (-.155, .058, .975, 1.128)   # old heart knot + tassels, gridded unlit front render
CORD_Z = 1.122                          # centre line of the waist band
R = .013                                # braided waist cord radius (reference: heavy braid)
KNOT = (-.066, 1.103)                   # (x, z), left of centre as in the reference
MAX_RADIUS = .245                       # torso only: hits farther out are the forearms

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
objs = list(bpy.context.scene.objects)
body = next(o for o in objs if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
cord_mat = next((m for m in bpy.data.materials if m.name.startswith('Braided silk cord')), None)

def bvh(objects):
    bm = bmesh.new()
    for o in objects: bm.from_mesh(o.data)
    t = BVHTree.FromBMesh(bm); bm.free(); return t

# 1. Flatten the old knot and tassels onto a surface fitted from a ring of rays around the box.
tree0 = bvh(objs)
x0, x1, z0, z1 = FLATTEN
ring = []
for x in np.arange(x0 - .015, x1 + .0151, .003):
    for z in np.arange(z0 - .015, z1 + .0151, .003):
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
co = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
inside = (co[:, 0] > x0) & (co[:, 0] < x1) & (co[:, 2] > z0) & (co[:, 2] < z1)
target = A(co[:, 0], co[:, 2]) @ coef - .0015
move = inside & (co[:, 1] < target)
co[move, 1] = target[move]; body.data.vertices.foreach_set('co', co.ravel()); body.data.update()
# The flattened knot keeps its glossy cord-red texture; in the reference this is the dark belt.
band = bpy.data.materials.new('Waist band / dark cloth under the cord'); band.use_nodes = True
bb = band.node_tree.nodes['Principled BSDF']; bb.inputs['Base Color'].default_value = (.025, .02, .02, 1); bb.inputs['Roughness'].default_value = .8
body.data.materials.append(band); band_index = len(body.data.materials) - 1
moved = np.zeros(len(co), bool); moved[move] = True
fv = np.empty(sum(len(f.vertices) for f in body.data.polygons), np.int32); body.data.polygons.foreach_get('vertices', fv)
starts = np.empty(len(body.data.polygons), np.int32); body.data.polygons.foreach_get('loop_start', starts)
counts = np.empty(len(body.data.polygons), np.int32); body.data.polygons.foreach_get('loop_total', counts)
all_moved = np.logical_and.reduceat(moved[fv], starts)
mi = np.empty(len(body.data.polygons), np.int32); body.data.polygons.foreach_get('material_index', mi)
mi[all_moved] = band_index; body.data.polygons.foreach_set('material_index', mi); body.data.update()

if a.clear_only:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
    rep = {'flattened_vertices': int(move.sum()), 'dark_band_faces': int(all_moved.sum()), 'ring_points': int(len(ring))}
    Path(a.output).with_name('waist-clear-report.json').write_text(json.dumps(rep, indent=2) + '\n'); print(json.dumps(rep)); raise SystemExit
# 2. Waist path: rays from outside toward the axis; step past forearm hits.
tree = bvh(objs)
path = []
for t in np.linspace(0, 2 * np.pi, 73)[:-1]:
    d = Vector((-np.sin(t), np.cos(t), 0))                             # t = 0: from the front (-Y)
    origin = Vector((0, 0, CORD_Z)) - d * .7
    hit = None
    for _ in range(6):
        h = tree.ray_cast(origin, d, 2)
        if h[0] is None: break
        if np.hypot(h[0].x, h[0].y) <= MAX_RADIUS: hit = h; break
        origin = h[0] + d * .002
    if hit is None: continue
    n = Vector((hit[0].x, hit[0].y, 0)).normalized()
    path.append(np.array(hit[0] + n * (R * 1.05)))
path = np.array(path)
# Smooth radially (keeps the cord off lame edges) and close the loop.
rad = np.hypot(path[:, 0], path[:, 1]); ang = np.arctan2(path[:, 1], path[:, 0])
k = np.array([1, 2, 3, 2, 1], float); k /= k.sum()
rad_s = np.convolve(np.r_[rad[-2:], rad, rad[:2]], k, 'valid')
rad_s = np.maximum(rad_s, rad)                                        # never sink into the armour
path = np.stack([rad_s * np.cos(ang), rad_s * np.sin(ang), np.full_like(rad_s, CORD_Z)], 1)
path = np.vstack([path, path[:1]])
loop_path = catmull(list(path), 4)

cbm = bmesh.new()
braided_cord(cbm, loop_path, R, pitch=6 * R)
def front(x, z, lift):
    h = tree.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
    n = np.array(h[1]); n = -n if n[1] > 0 else n
    return np.array(h[0]) + n * lift
kc = front(KNOT[0], KNOT[1], R * 2.4)
knot(cbm, kc, R * 2.1)
loop(cbm, kc + np.array([-R * 1.5, -.002, .004]), R * .75, .05, .03, .25, -1)
loop(cbm, kc + np.array([R * 1.5, -.002, .004]), R * .75, .045, .028, -.2, 1)
rng = np.random.default_rng(1615)
tassels = []
for dx in (-.028, .024):
    head = front(KNOT[0] + dx, KNOT[1] - .055, R * 1.9)
    braided_cord(cbm, catmull([kc + np.array([dx * .35, 0, -R]), head + np.array([0, 0, .008])], 8), R * .75)
    knot(cbm, head, R * 1.5)
    fringe(cbm, head + np.array([0, 0, -R * 1.2]), .09, R * 1.8, rng, strands=90)
    tassels.append(head.round(4).tolist())
mesh = bpy.data.meshes.new('Waist cord'); cbm.normal_update(); cbm.to_mesh(mesh); cbm.free()
for poly in mesh.polygons: poly.use_smooth = True
if cord_mat is None:
    cord_mat = bpy.data.materials.new('Braided silk cord / lacquer red'); cord_mat.use_nodes = True
cb = cord_mat.node_tree.nodes['Principled BSDF']                      # same deep crimson as the neck cords
cb.inputs['Base Color'].default_value = (.16, .008, .008, 1); cb.inputs['Roughness'].default_value = .72
cb.inputs['Specular IOR Level'].default_value = .25; cb.inputs['Sheen Weight'].default_value = .05
mesh.materials.append(cord_mat)
obj = bpy.data.objects.new('Waist cord / braided silk', mesh); bpy.context.collection.objects.link(obj)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
report = {'flattened_vertices': int(move.sum()), 'dark_band_faces': int(all_moved.sum()), 'ring_points': int(len(ring)), 'path_samples': int(len(path) - 1),
          'cord_radius': R, 'cord_z': CORD_Z, 'knot': kc.round(4).tolist(), 'tassels': tassels,
          'triangles': sum(len(f.vertices) - 2 for f in mesh.polygons)}
Path(a.output).with_name('waist-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
