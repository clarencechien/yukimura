"""Open-source rigging line of the Tripo/open comparison: rig a generated character in Blender only.

1. Scale the mesh to 2 m and measure its joints from its filled front silhouette (legs are separate
   below the crotch, arms beside the torso), taking each joint's depth from the nearby vertices.
2. Build the game's 18 control bones (same names and hierarchy as public/models/yukimura.glb)
   at those joints and bind with Blender's automatic (bone heat) weights on a voxel-remeshed proxy,
   copied to the real mesh; vertices still unweighted fall back to inverse-distance weights.
3. Retarget the game's own clips onto it with game_retarget.py.

  blender-python tools/rig_open.py --mesh .tmp/tripo-game-ny.glb --output .tmp/rig-open/rig-open.glb \
      --clips idle,run,slash,hurt
"""
from pathlib import Path
import argparse, json, math, sys
import bpy
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, str(Path(__file__).parent)); import game_retarget

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--mesh', required=True); p.add_argument('--output', required=True)
p.add_argument('--source', default=str(ROOT / 'public/models/yukimura.glb')); p.add_argument('--clips', default='idle,run,slash,hurt')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- source rig and clips
src = game_retarget.load_source(a.source)
CTRL = [b.name for b in src.data.bones if not b.name.startswith('body.')]
PARENT = {n: (src.data.bones[n].parent.name if src.data.bones[n].parent else None) for n in CTRL}

# ---------------------------------------------------------------- mesh and its joints
before = set(scene.objects)
bpy.ops.import_scene.gltf(filepath=a.mesh)
mesh = next(o for o in scene.objects if o not in before and o.type == 'MESH')
for o in [o for o in scene.objects if o not in before and o is not mesh]: bpy.data.objects.remove(o, do_unlink=True)
w = mesh.matrix_world.copy(); mesh.parent = None; mesh.data.transform(w); mesh.matrix_world = Matrix.Identity(4)
V = np.array([v.co for v in mesh.data.vertices])
s = 2.0 / (V[:, 2].max() - V[:, 2].min())
mesh.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(Vector((-(V[:, 0].max() + V[:, 0].min()) / 2, -(V[:, 1].max() + V[:, 1].min()) / 2, -V[:, 2].min()))))
V = np.array([v.co for v in mesh.data.vertices]); H = V[:, 2].max()
yc = float(np.median(V[:, 1]))

# Front silhouette: rasterise the triangles onto a 5 mm XZ grid, close small gaps, fill the inside.
from scipy import ndimage
r = .005; X0 = V[:, 0].min() - .1; GW = int((V[:, 0].max() + .1 - X0) / r); GH = int((H + .02) / r)
mesh.data.calc_loop_triangles(); Tri = V[np.array([t.vertices[:] for t in mesh.data.loop_triangles])]
G = np.zeros((GH, GW), bool)
for u in np.linspace(0, 1, 7):
    for v in np.linspace(0, 1 - u, 7):
        q = Tri[:, 0] * (1 - u - v) + Tri[:, 1] * u + Tri[:, 2] * v
        G[np.clip((q[:, 2] / r).astype(int), 0, GH - 1), np.clip(((q[:, 0] - X0) / r).astype(int), 0, GW - 1)] = True
G = ndimage.binary_closing(G, iterations=2)
holes, nh = ndimage.label(ndimage.binary_fill_holes(G) & ~G)      # fill only pin-holes, not the gaps between arm and torso
G |= np.isin(holes, 1 + np.where(ndimage.sum(holes > 0, holes, range(1, nh + 1)) < 200)[0])
def runs(z):
    """filled x-intervals of the silhouette row at height z"""
    d = np.diff(np.r_[0, G[min(int(z / r), GH - 1)].astype(int), 0])
    return [(X0 + s0 * r, X0 + e0 * r) for s0, e0 in zip(np.where(d == 1)[0], np.where(d == -1)[0])]
def mid(i): return (i[0] + i[1]) / 2
def depth_at(x, z, w=.04):
    """middle of the body's depth around (x, z)"""
    S = V[(np.abs(V[:, 0] - x) < w) & (np.abs(V[:, 2] - z) < w)]
    return float((S[:, 1].min() + S[:, 1].max()) / 2) if len(S) else yc
def pt(x, z): return Vector((x, depth_at(x, z), z))

# Legs: two runs from the floor to the crotch.
zs = np.arange(.05, H * .6, r)
crotch = next(z for z in zs if len(runs(z)) == 1)
cx = (mid(runs(crotch - .1)[0]) + mid(runs(crotch - .1)[-1])) / 2      # body centre line
def leg_x(z, sign): return mid(max(runs(z), key=lambda i: sign * mid(i)))
# Arms: the outermost runs that are separate from the torso, between the hand tip and the armpit.
arm_rows = {1: [], -1: []}
for z in np.arange(crotch * .8, H * .8, r):
    rr = runs(z)
    for sign in (1, -1):
        o = max(rr, key=lambda i: sign * mid(i))
        if len(rr) >= 2 and sign * (mid(o) - cx) > .25: arm_rows[sign].append((z, mid(o)))
legs, arms = {}, {}
for side, sign in (('R', 1), ('L', -1)):         # the game's '.R' bones sit at +X
    hip_x = cx + (leg_x(crotch - .05, sign) - cx) * .85
    legs[side] = dict(hip=(hip_x, crotch + .1), knee=(leg_x(crotch * .55, sign), crotch * .55),
                      ankle=(leg_x(crotch * .13, sign), crotch * .13))
    rows = sorted(arm_rows[sign])
    # the arm run can merge with the torso on one side; keep the longest stretch (5 cm gaps allowed)
    segs = [[rows[0]]]
    for z, x in rows[1:]:
        if z - segs[-1][-1][0] > .05: segs.append([])
        segs[-1].append((z, x))
    seg = max(segs, key=lambda q: q[-1][0] - q[0][0])
    arms[side] = dict(tip=seg[0], pit=seg[-1], rows=seg)
# Use the side with the longer free arm for both (the figure is symmetric), mirrored about the centre.
best = max(arms.values(), key=lambda A: A['pit'][0] - A['tip'][0])
pit_z, tip_z = best['pit'][0], best['tip'][0]
def arm_x(z):
    return abs(min(best['rows'], key=lambda q: abs(q[0] - z))[1] - cx)
shoulder_z = pit_z + .1
leg_off = {k: (abs(legs['R'][k][0] - cx) + abs(legs['L'][k][0] - cx)) / 2 for k in ('hip', 'knee', 'ankle')}
for side, sign in (('R', 1), ('L', -1)):
    elbow_z = shoulder_z + (tip_z - shoulder_z) * .45; wrist_z = shoulder_z + (tip_z - shoulder_z) * .8
    arms[side] = dict(shoulder=pt(cx + sign * arm_x(pit_z) * .8, shoulder_z), elbow=pt(cx + sign * arm_x(elbow_z), elbow_z),
                      wrist=pt(cx + sign * arm_x(wrist_z), wrist_z), tip=pt(cx + sign * arm_x(tip_z), tip_z))
    legs[side] = {k: pt(cx + sign * leg_off[k], legs[side][k][1]) for k in ('hip', 'knee', 'ankle')}
for k in ('shoulder', 'elbow', 'wrist', 'tip'): arms['R'][k].y = arms['L'][k].y = (arms['R'][k].y + arms['L'][k].y) / 2
for k in ('hip', 'knee', 'ankle'): legs['R'][k].y = legs['L'][k].y = (legs['R'][k].y + legs['L'][k].y) / 2
for side, sign in (('R', 1), ('L', -1)):
    foot = V[(V[:, 2] < .08) & (sign * (V[:, 0] - cx) > 0)]
    legs[side]['toe'] = Vector((legs[side]['ankle'].x, foot[:, 1].min() + .04, .03))
# Neck: first row above the shoulders that is narrower than the shoulder line; head top: last row on the centre line.
neck_z = next(z for z in np.arange(shoulder_z, H, r) if np.ptp(runs(z)[0] + runs(z)[-1]) < .45)
head_top = max(z for z in np.arange(neck_z, H, r) if any(i[0] <= cx <= i[1] for i in runs(z)))
yc = depth_at(cx, crotch + .2, .08)
pelvis_z = crotch + .1
J = {'pelvis': (Vector((cx, yc, pelvis_z)), Vector((cx, yc, pelvis_z + .09))),
     'chest': (Vector((cx, yc, pelvis_z + .18)), Vector((cx, yc, neck_z - .04))),
     'head': (Vector((cx, yc, neck_z)), Vector((cx, yc, head_top))),
     'cape': (Vector((cx, yc + .12, neck_z - .05)), Vector((cx, yc + .25, pelvis_z))),
     'cape_tip': (Vector((cx, yc + .25, pelvis_z)), Vector((cx, yc + .4, crotch * .5))),
     'weapon': (arms['R']['wrist'] + Vector((0, -.02, -.04)), arms['R']['wrist'] + Vector((0, -.12, .36)))}
for side in ('R', 'L'):
    A, Lg = arms[side], legs[side]
    J.update({f'arm.{side}': (A['shoulder'], A['elbow']), f'forearm.{side}': (A['elbow'], A['wrist']), f'hand.{side}': (A['wrist'], A['tip']),
              f'thigh.{side}': (Lg['hip'], Lg['knee']), f'shin.{side}': (Lg['knee'], Lg['ankle']), f'foot.{side}': (Lg['ankle'], Lg['toe'])})

# ---------------------------------------------------------------- new rig, weights
data = bpy.data.armatures.new('open rig'); rig = bpy.data.objects.new('open rig', data); scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for n in CTRL:
    b = data.edit_bones.new(n); b.head, b.tail = J[n]
for n in CTRL:
    if PARENT[n]: data.edit_bones[n].parent = data.edit_bones[PARENT[n]]
    data.edit_bones[n].use_deform = n not in ('cape', 'cape_tip', 'weapon')   # the generated mesh has no cape; the spear is separate
bpy.ops.object.mode_set(mode='OBJECT')
# Bone heat needs one watertight surface; the generated mesh is many open shells. Bind a voxel-remeshed
# proxy of it, then copy the weights to the real mesh from the nearest proxy face.
# The proxy is the solid the shells enclose: a 1 cm occupancy grid, closed and hole-filled in 3D, whose outer
# voxel faces are then voxel-remeshed into one smooth watertight surface.
vs = .01; lo = V.min(0) - .03; dims = ((V.max(0) + .03 - lo) / vs).astype(int) + 1
occ = np.zeros(dims, bool)
for u in np.linspace(0, 1, 6):
    for v in np.linspace(0, 1 - u, 6):
        q = ((Tri[:, 0] * (1 - u - v) + Tri[:, 1] * u + Tri[:, 2] * v - lo) / vs).astype(int); occ[q[:, 0], q[:, 1], q[:, 2]] = True
occ = ndimage.binary_fill_holes(ndimage.binary_closing(occ, iterations=1))
verts, faces = [], []
for ax in range(3):
    for d in (1, -1):
        nb = np.roll(occ, -d, ax); idx = np.argwhere(occ & ~nb)
        base = idx + (np.eye(3, dtype=int)[ax] * (d > 0))
        o1, o2 = np.eye(3, dtype=int)[(ax + 1) % 3], np.eye(3, dtype=int)[(ax + 2) % 3]
        quad = np.stack([base, base + o1, base + o1 + o2, base + o2], 1)
        if d < 0: quad = quad[:, ::-1]
        faces.append(np.arange(len(quad) * 4).reshape(-1, 4) + sum(len(x) for x in verts)); verts.append(quad.reshape(-1, 3) * vs + lo)
pm = bpy.data.meshes.new('weight proxy'); pm.from_pydata(np.concatenate(verts).tolist(), [], np.concatenate(faces).tolist())
proxy = bpy.data.objects.new('weight proxy', pm); scene.collection.objects.link(proxy)
rm = proxy.modifiers.new('remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = .012
bpy.context.view_layer.objects.active = proxy; bpy.ops.object.modifier_apply(modifier='remesh')
bpy.ops.object.select_all(action='DESELECT'); proxy.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
deform = [n for n in CTRL if rig.data.bones[n].use_deform]
for n in deform: mesh.vertex_groups.get(n) or mesh.vertex_groups.new(name=n)
dt = mesh.modifiers.new('weights', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = mesh; bpy.ops.object.modifier_apply(modifier='weights')
proxy_unweighted = sum(1 for v in proxy.data.vertices if sum(g.weight for g in v.groups) < 1e-4)
proxy_verts = len(proxy.data.vertices); bpy.data.objects.remove(proxy, do_unlink=True)
mesh.parent = rig; arm_mod = mesh.modifiers.new('rig', 'ARMATURE'); arm_mod.object = rig
unweighted = [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups) < 1e-4]
if unweighted:
    # Fallback for the islands bone heat cannot reach: inverse-distance to the bone segments.
    segs = {n: (np.array(J[n][0]), np.array(J[n][1])) for n in deform}
    def seg_d(pnt, a0, a1):
        d = a1 - a0; t = np.clip(((pnt - a0) @ d) / (d @ d), 0, 1); return np.linalg.norm(pnt - (a0 + t[:, None] * d), axis=1)
    P = np.array([mesh.data.vertices[i].co for i in unweighted])
    D = np.stack([seg_d(P, *segs[n]) for n in deform], 1); Wt = 1 / np.maximum(D, 1e-3) ** 4
    top = np.argsort(-Wt, 1)[:, :2]
    for row, i in enumerate(unweighted):
        ws = Wt[row, top[row]]; ws /= ws.sum()
        for k, wv in zip(top[row], ws): (mesh.vertex_groups.get(deform[k]) or mesh.vertex_groups.new(name=deform[k])).add([i], float(wv), 'REPLACE')

# ---------------------------------------------------------------- retarget
report = {'clips': game_retarget.retarget(src, rig, {n: n for n in ['pelvis'] + [n for n in CTRL if n != 'pelvis']}, a.clips.split(','),
                                          (('thigh.R', 'shin.R', 'foot.R'),) * 2)}
bpy.data.objects.remove(src, do_unlink=True)
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix('.blend').resolve()))
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out.resolve()), export_format='GLB', use_selection=True, export_animations=True, export_animation_mode='NLA_TRACKS')
report.update(joints={n: [list(map(lambda x: round(x, 3), J[n][0])), list(map(lambda x: round(x, 3), J[n][1]))] for n in CTRL},
              crotch=round(crotch, 3), neck=round(float(neck_z), 3), heat_unweighted_vertices=len(unweighted), proxy_vertices=proxy_verts, proxy_unweighted=proxy_unweighted, vertices=len(mesh.data.vertices))
out.with_name('rig-open-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('clips', 'crotch', 'neck', 'heat_unweighted_vertices', 'proxy_vertices', 'proxy_unweighted', 'vertices')}))
