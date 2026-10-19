"""Neck cleanup for body v2: drop orphaned fragments and line the neck opening.

Removing the generated head cut the neck cords, leaving tassel tips hanging in the air in
front of the chest, and left the neck stump open: a dark void shows between the helmet's
neck guard (shikoro) and the back collar. This removes body pieces that float clear of
everything (gap > --gap) plus debris inside the helmet zone, and adds a dark quilted neck
lining (an elliptical tube) under the helmet.
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np
from scipy.spatial import cKDTree
from mathutils import Matrix, Vector

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--output', required=True)
p.add_argument('--gap', type=float, default=.006, help='Pieces farther than this from any other part are orphans')
p.add_argument('--max-piece', type=int, default=2000, help='Never remove pieces with more vertices than this')
p.add_argument('--lining-z', type=float, nargs=2, default=(1.37, 1.57))
p.add_argument('--lining-radius', type=float, nargs=3, default=(.088, .072, .098), help='fallback ellipse (x, front y, back y) where no surface is hit')
a = p.parse_args()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
objs = [o for o in bpy.context.scene.objects]
body = next(o for o in objs if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
head = [o for o in objs if o != body and not o.name.startswith(('Energy seam', 'Back plate shell'))]
head_pts = np.concatenate([np.array([v.co for v in o.data.vertices]) for o in objs if o != body])
head_lo = np.min([np.min(np.array([v.co for v in o.data.vertices]), 0) for o in head], 0)

bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6); bm.verts.ensure_lookup_table(); bm.verts.index_update()
co = np.array([v.co for v in bm.verts]); comp = -np.ones(len(co), int); n = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    stack = [v]; comp[v.index] = n
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = n; stack.append(o)
    n += 1
sizes = np.bincount(comp)
tree = cKDTree(co); tree_other = cKDTree(head_pts)
removed = []; drop_ids = []
for k in np.where(sizes <= a.max_piece)[0]:
    idx = np.where(comp == k)[0]; pts = co[idx]
    d, j = tree.query(pts, k=40, distance_upper_bound=.08)
    valid = (j < len(co)); valid[valid] &= comp[j[valid]] != k
    gap_body = d[valid].min() if valid.any() else np.inf
    gap = min(gap_body, tree_other.query(pts)[0].min())
    centre = pts.mean(0)
    inside_helmet = centre[2] > head_lo[2] + .06 and abs(centre[0]) < .06            # hidden debris
    if gap > a.gap or inside_helmet:
        drop_ids.append(k)
        removed.append({'vertices': int(len(idx)), 'gap': float(round(gap, 4)), 'centre': centre.round(3).tolist(), 'reason': 'inside helmet' if inside_helmet and gap <= a.gap else 'floating'})
drop = np.where(np.isin(comp, drop_ids))[0]
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in drop], context='VERTS')
bm.to_mesh(body.data); bm.free()

# Neck lining: a tube that sits just inside the surrounding shikoro / collar / mask. Rays cast
# outward from the neck centre find the inner surfaces; a fixed ellipse sat too deep at the
# back, where the stump opening is widest.
from mathutils.bvhtree import BVHTree
cx = float((head_lo[0] + np.max([np.max(np.array([v.co for v in o.data.vertices]), 0) for o in head], 0)[0]) / 2)
cy = .026
rx, ryf, ryb = a.lining_radius; z0, z1 = a.lining_z
bm_all = bmesh.new()
for o in objs: bm_all.from_mesh(o.data)
tree_all = BVHTree.FromBMesh(bm_all); bm_all.free()
seg, rings = 48, 12
radius = np.zeros((rings + 1, seg))
for r in range(rings + 1):
    z = z0 + (z1 - z0) * r / rings
    for s_ in range(seg):
        t = 2 * np.pi * s_ / seg; d = Vector((np.sin(t), np.cos(t), 0))
        hit = tree_all.ray_cast(Vector((cx, cy, z)), d, .25)
        base = np.hypot(rx * np.sin(t), (ryb if np.cos(t) > 0 else ryf) * np.cos(t))
        radius[r, s_] = (hit[3] - .004) if hit[0] is not None else base
radius = np.clip(radius, .05, .2)
from scipy import ndimage as _nd
radius = _nd.median_filter(radius, size=(3, 5), mode='wrap'); radius = _nd.gaussian_filter(radius, (.8, 1.2), mode='wrap')
mesh = bpy.data.meshes.new('Neck lining'); bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
grid = []
for r in range(rings + 1):
    z = z0 + (z1 - z0) * r / rings
    grid.append([bm.verts.new((cx + radius[r, s_] * np.sin(2 * np.pi * s_ / seg), cy + radius[r, s_] * np.cos(2 * np.pi * s_ / seg), z)) for s_ in range(seg)])
for r in range(rings):
    for s_ in range(seg):
        f = bm.faces.new((grid[r][s_], grid[r][(s_ + 1) % seg], grid[r + 1][(s_ + 1) % seg], grid[r + 1][s_]))
        for loop, (du, dv) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = ((s_ + du) / seg * 6, (r + dv) / rings * 2)
bm.normal_update()
if np.mean([(Vector(f.calc_center_median()) - Vector((cx, cy, f.calc_center_median().z))).dot(f.normal) for f in bm.faces]) < 0:
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bm.to_mesh(mesh); bm.free()
for poly in mesh.polygons: poly.use_smooth = True
mat = bpy.data.materials.new('Neck lining / dark quilted cloth'); mat.use_nodes = True
nodes = mat.node_tree.nodes; b = nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (.03, .025, .025, 1); b.inputs['Roughness'].default_value = .85
mesh.materials.append(mat)
lining = bpy.data.objects.new('Neck lining / dark quilted cloth', mesh); bpy.context.collection.objects.link(lining)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
report = {'gap_threshold': a.gap, 'removed_pieces': removed, 'removed_vertices': len(drop),
          'lining': {'z': [z0, z1], 'centre': [cx, cy], 'fitted_radius_min': float(radius.min()), 'fitted_radius_max': float(radius.max()), 'inset_from_hit': .004}}
Path(a.output).with_name('neck-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'removed_pieces'}), len(removed))
