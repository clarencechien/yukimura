"""Tie the neck, shoulder and waist cords with physics (reference illustration as the target).

Stage 1: each knot is a real reef knot of the cord itself (two interlaced bights,
reef_knot_design), tightened in isolation by position-based dynamics: pinned ends, shortened
rest lengths and cord-to-cord collision. Stage 2: with the knots fixed where the reference has
them, the cords between the mask, shoulder fittings, waist and knots drape under gravity onto
the armour (collision with friction), the tails swing down to heavy tassel heads, and the bow
loops of the waist knot droop. Stage 3: each tassel's fringe, as clumps of threads pinned
around its binding, falls under gravity onto the armour and spreads by thread repulsion.
Geometry: an 8-strand kumihimo braid along every cord (continuous through its knot), tassel
heads made of threads folded over a core and bound with a brass wrap, fringe threads.
"""
from pathlib import Path
import argparse, json, sys, time
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cord_geometry import catmull, frames, tube, resample, kumihimo, reef_knot_design, coil
from cord_physics import RopeSystem, Collider

p = argparse.ArgumentParser()
p.add_argument('--model', required=True, help='Character with the generated cords cleared')
p.add_argument('--output', required=True)
a = p.parse_args()
t_start = time.monotonic(); log = lambda m: print(m, flush=True)

NECK_R, SHOULDER_R, WAIST_R = .0068, .0055, .0105
NECK_KNOT, WAIST_KNOT = (-.006, 1.468), (-.066, 1.100)          # (x, z) on the front, gridded renders
NECK_ANCHORS = [(-.072, 1.556), (.074, 1.556)]                   # under the mask's side plates
SHOULDER_ANCHORS = [(-.172, 1.492), (.103, 1.486)]               # gold shoulder fittings
WAIST_Z = 1.118

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
objs = list(bpy.context.scene.objects)
solid = [o for o in objs if not o.name.startswith(('Neck lining', 'Collar core', 'Energy seam'))]
bm = bmesh.new()
for o in solid: bm.from_mesh(o.data)
bvh = BVHTree.FromBMesh(bm); bm.free()
verts = np.concatenate([np.array([v.co for v in o.data.vertices]) for o in solid])
collider = Collider(bvh, verts)

class NoBody:
    def resolve(self, p, r, active): return np.zeros(len(p), bool), np.zeros_like(p)

def front(x, z, lift):
    h = bvh.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
    n = np.array(h[1]); n = -n if n[1] > 0 else n
    return np.array(h[0]) + n * lift, n

def frame_at(point, normal):
    w = normal / np.linalg.norm(normal); v = np.array([0, 0, 1.]) - w * w[2]; v /= np.linalg.norm(v)
    return np.cross(v, w), v, w                                       # u (screen right), v (up), w (out)

# ---------------------------------------------------------------- stage 1: knots
def tight_knot(entry_y, exit_y):
    A, B = reef_knot_design(entry_y, exit_y)
    sysk = RopeSystem()
    ia = sysk.add_rope(resample(catmull(list(A), 8), .45), 1, 1., bend=.4, pin_first=True, pin_last=True, slack=.94)
    ib = sysk.add_rope(resample(catmull(list(B), 8), .45), 1, 1., bend=.4, pin_first=True, pin_last=True, slack=.94)
    rep = sysk.simulate(NoBody(), seconds=.5, dt=1 / 400, iterations=30, damping=.9, gravity=False)
    x = np.array(sysk.x)
    return x[ia], x[ib], rep

knots = {}
for name, entry_y in (('neck', 7.), ('waist', 3.)):
    ka, kb, rep = tight_knot(entry_y, -6.5)
    knots[name] = (ka, kb); log(f'knot {name}: {rep}')

def place(local, centre, u, v, w, R):
    return centre + R * (local[:, :1] * u + local[:, 1:2] * v + local[:, 2:3] * w)

# ---------------------------------------------------------------- stage 2: cords
S = RopeSystem(); obstacles = []
def obstacle(points, radius):
    idx = S.add_rope(points, 1, radius)
    for i in idx: S.pin(i)
    obstacles.append(idx); return idx

# Neck knot and its two cords from the mask; tails to the tassel heads.
Kn, nn = front(*NECK_KNOT, 2.3 * NECK_R); un, vn, wn = frame_at(Kn, nn)
neck_A = place(knots['neck'][0], Kn, un, vn, wn, NECK_R); neck_B = place(knots['neck'][1], Kn, un, vn, wn, NECK_R)
obstacle(neck_A, NECK_R); obstacle(neck_B, NECK_R)
ropes = {}
for side, anchor, knot_path in (('A', NECK_ANCHORS[0], neck_A), ('B', NECK_ANCHORS[1], neck_B)):
    top, _ = front(*anchor, 1.3 * NECK_R)
    mid1, _ = front(anchor[0] * .9, anchor[1] - .03, 1.6 * NECK_R); mid2, _ = front(anchor[0] * .6, anchor[1] - .06, 1.8 * NECK_R)
    pts = resample(catmull([top, mid1, mid2, knot_path[0]], 8), 1.4 * NECK_R)
    ropes[f'neck {side}'] = S.add_rope(pts, 1, NECK_R, bend=.5, pin_first=True, pin_last=True, slack=1.03)
    exit_pt = knot_path[-1]; head0 = exit_pt + np.array([0, -.006, -.034])
    tail = resample(np.array([exit_pt, head0]), 1.4 * NECK_R)
    ropes[f'neck tail {side}'] = S.add_rope(tail, 1, NECK_R, bend=.5, pin_first=True)
    S.set_mass(ropes[f'neck tail {side}'][-1], 6, .0068)
# Shoulder cords: short braid from the fitting to a tassel head.
for i, anchor in enumerate(SHOULDER_ANCHORS):
    top, _ = front(*anchor, 1.4 * SHOULDER_R)
    pts = resample(np.array([top, top + np.array([0, -.004, -.045])]), 1.4 * SHOULDER_R)
    ropes[f'shoulder {i}'] = S.add_rope(pts, 1, SHOULDER_R, bend=.5, pin_first=True)
    S.set_mass(ropes[f'shoulder {i}'][-1], 6, .0062)
# Waist: knot, the band around the body (one cord: tail B - knot B - band - knot A - tail A),
# two bow loops and two tails.
Kw, nw = front(*WAIST_KNOT, 2.3 * WAIST_R); uw, vw, ww = frame_at(Kw, nw)
waist_A = place(knots['waist'][0], Kw, uw, vw, ww, WAIST_R); waist_B = place(knots['waist'][1], Kw, uw, vw, ww, WAIST_R)
obstacle(waist_A, WAIST_R); obstacle(waist_B, WAIST_R)
band = []
for t in np.linspace(0, 2 * np.pi, 145)[:-1]:
    d = Vector((-np.sin(t), np.cos(t), 0)); origin = Vector((0, 0, WAIST_Z)) - d * .7; hit = None
    for _ in range(6):
        h = bvh.ray_cast(origin, d, 2)
        if h[0] is None: break
        if np.hypot(h[0].x, h[0].y) <= .245: hit = h; break
        origin = h[0] + d * .002
    if hit is not None: band.append((t, np.array(hit[0]) + np.array([hit[0].x, hit[0].y, 0]) / np.hypot(hit[0].x, hit[0].y) * WAIST_R * 1.15))
# Order from knot entry B (screen right, +x) round the back to entry A (-x); skip the knot sector.
entryA, entryB = waist_A[0], waist_B[0]
angA = np.arctan2(entryA[1], entryA[0]); angB = np.arctan2(entryB[1], entryB[0])
pts = [entryB]
for t, q in sorted(band, key=lambda b: (np.arctan2(b[1][1], b[1][0]) - angB) % (2 * np.pi)):
    ang = (np.arctan2(q[1], q[0]) - angB) % (2 * np.pi)
    if .08 < ang < ((angA - angB) % (2 * np.pi)) - .08: pts.append(q)
pts.append(entryA)
ropes['waist band'] = S.add_rope(resample(catmull(pts, 4), 1.5 * WAIST_R), 1, WAIST_R, bend=.6, pin_first=True, pin_last=True, slack=1.01)
for side, sgn, length in (('A', -1, .105), ('B', 1, .09)):
    p0 = Kw + WAIST_R * (sgn * 4.2 * uw + .8 * vw + .3 * ww); p1 = Kw + WAIST_R * (sgn * 4.2 * uw - 1.6 * vw + .3 * ww)
    t = np.linspace(0, np.pi, 14)
    loop0 = np.array([p0 + (p1 - p0) * (1 - np.cos(tt)) / 2 + sgn * uw * length / np.pi * np.sin(tt) + ww * .012 * np.sin(tt) for tt in t])
    ropes[f'waist loop {side}'] = S.add_rope(resample(loop0, 1.5 * WAIST_R), 1, WAIST_R, bend=.6, pin_first=True, pin_last=True)
knot_end = {'A': waist_A[-1], 'B': waist_B[-1]}
for side, length in (('A', .055), ('B', .07)):
    e = knot_end[side]
    ropes[f'waist tail {side}'] = S.add_rope(resample(np.array([e, e + np.array([0, -.008, -length])]), 1.4 * WAIST_R), 1, WAIST_R, bend=.6, pin_first=True)
    S.set_mass(ropes[f'waist tail {side}'][-1], 8, .0095)
log(f'stage 2: {len(S.x)} particles')
rep2 = S.simulate(collider, seconds=2.5, dt=1 / 240, iterations=24, damping=.985, friction=.6, log=log)
X = np.array(S.x)
paths = {k: X[v] for k, v in ropes.items()}

# ---------------------------------------------------------------- stage 3: tassel fringes
TASSELS = {'neck A': ('neck tail A', .0068, .066, .0018), 'neck B': ('neck tail B', .0068, .066, .0018),
           'shoulder 0': ('shoulder 0', .0062, .085, .0017), 'shoulder 1': ('shoulder 1', .0062, .085, .0017),
           'waist A': ('waist tail A', .0095, .082, .0024), 'waist B': ('waist tail B', .0095, .082, .0024)}
F = RopeSystem(); f_obst = []
for name, idx in ropes.items():                                      # settled cords as obstacles
    q = F.add_rope(X[idx], 1, S.r[idx[0]])
    for i in q: F.pin(i)
for k in (neck_A, neck_B, waist_A, waist_B):
    q = F.add_rope(k, 1, NECK_R if k is neck_A or k is neck_B else WAIST_R)
    for i in q: F.pin(i)
heads = {}; clumps = {}; rng = np.random.default_rng(1615)
N_CLUMPS = 28
for name, (rope, rh, length, rc) in TASSELS.items():
    path = paths[rope]; H = path[-1]
    axis = H - path[-3]; axis /= np.linalg.norm(axis)
    e1 = np.cross(axis, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(axis, e1)
    bind = H + axis * rh * .95; rb = rh * .62
    heads[name] = (H, axis, e1, e2, rh, bind, rb)
    clumps[name] = []
    for k in range(N_CLUMPS):
        phi = 2 * np.pi * k / N_CLUMPS + rng.uniform(-.08, .08)
        radial = np.cos(phi) * e1 + np.sin(phi) * e2
        root = bind + radial * rb
        L = length * rng.uniform(.9, 1.0)
        pts = np.array([root + axis * L * u + radial * rb * .9 * np.sin(min(u * 4, 1) * np.pi / 2) for u in np.linspace(0, 1, 12)])
        idx = F.add_rope(pts, .05, rc, bend=.12, pin_first=True)
        clumps[name].append((phi, idx))
log(f'stage 3: {len(F.x)} particles')
rep3 = F.simulate(collider, seconds=1.6, dt=1 / 300, iterations=16, damping=.97, friction=.5, log=log)
XF = np.array(F.x)

# ---------------------------------------------------------------- geometry
def material(name, rgb, rough, metal=0., sheen=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Sheen Weight'].default_value = sheen
    return m
mats = [material('Braided silk cord / lacquer red', (.16, .008, .008), .66, sheen=.08),
        material('Tassel thread / silk red', (.19, .01, .01), .6, sheen=.15),
        material('Tassel binding / aged brass', (.42, .26, .08), .38, metal=1.),
        material('Tassel core / dark red', (.06, .004, .004), .8)]

def build(name, fill, mat_index):
    bm = bmesh.new(); fill(bm); bm.normal_update()
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    for poly in mesh.polygons: poly.use_smooth = True
    mesh.materials.append(mats[mat_index])
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    return len(mesh.polygons)

def strip_near(path, centre, radius):
    """Drop path points inside a radius of the knot centre (the knot geometry replaces them)."""
    return path[np.linalg.norm(path - centre, axis=1) > radius]

tri = {}
def cords(bm):
    for side, kp in (('A', neck_A), ('B', neck_B)):                   # anchor -> knot -> tail, one cord each
        full = np.vstack([paths[f'neck {side}'][:-1], kp, paths[f'neck tail {side}'][1:]])
        kumihimo(bm, full, NECK_R)
    for i in range(2): kumihimo(bm, paths[f'shoulder {i}'], SHOULDER_R)
    full = np.vstack([paths['waist tail B'][::-1][:-1], waist_B[::-1], paths['waist band'][1:-1], waist_A, paths['waist tail A'][1:]])
    kumihimo(bm, full, WAIST_R)
    for side in 'AB': kumihimo(bm, paths[f'waist loop {side}'], WAIST_R)
tri['cords'] = build('Cords / kumihimo braid', cords, 0)

def tassel_threads(bm):
    for name, (H, axis, e1, e2, rh, bind, rb) in heads.items():
        rc = TASSELS[name][3]
        for phi, idx in clumps[name]:
            fr = XF[idx]
            T, N, B = frames(fr)
            for j in range(4):                                         # threads per clump
                ang = phi + (j - 1.5) * .045
                radial = np.cos(ang) * e1 + np.sin(ang) * e2
                dome = [H - axis * rh * 1.02 * np.cos(t) + radial * rh * np.sin(t) for t in np.linspace(.18, np.pi * .62, 7)]
                off = rc * .55 * (np.cos(j * np.pi / 2 + phi)[None] * N + np.sin(j * np.pi / 2 + phi)[None] * B)
                fringe_pts = fr + off * np.linspace(.3, 1, len(fr))[:, None]
                path = resample(catmull(dome + [bind + radial * (rb + rc * .3)] + list(fringe_pts[1:]), 3), rc * 1.6)
                rr = np.full(len(path), rc * .42); rr[-6:] *= np.linspace(1, .55, 6)
                tube(bm, path, rr, sides=4)
tri['tassel threads'] = build('Tassels / silk threads', tassel_threads, 1)

def bindings(bm):
    for name, (H, axis, e1, e2, rh, bind, rb) in heads.items():
        coil(bm, bind, axis, e1, e2, lambda u: rb + .0012, -.0022, .0022, 4.5, .0009)
tri['bindings'] = build('Tassels / brass binding', bindings, 2)

def cores(bm):
    for name, (H, axis, e1, e2, rh, bind, rb) in heads.items():
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1)
        for v in sph['verts']:
            q = np.array(v.co); v.co = Vector(H + q[0] * rh * .92 * e1 + q[1] * rh * .92 * e2 + q[2] * rh * .98 * (-axis))
tri['cores'] = build('Tassels / core', cores, 3)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
report = {'stage1_knots': 'reef knots tightened by PBD (no gravity, pinned ends, slack 0.94)',
          'stage2': rep2, 'stage3': rep3, 'triangles': tri, 'radii': {'neck': NECK_R, 'shoulder': SHOULDER_R, 'waist': WAIST_R},
          'tassels': {k: {'head_radius': v[1], 'fringe_length': v[2], 'clumps': N_CLUMPS, 'threads_per_clump': 4} for k, v in TASSELS.items()},
          'seconds': time.monotonic() - t_start}
Path(a.output).with_name('tie-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
