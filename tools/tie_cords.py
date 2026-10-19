"""Tie the neck, shoulder and waist cords with physics (reference illustration as the target).

Knots: decorative ball knots (monkey's fist) where the reference has them.
Stage 2 (cords): the cords from the mask and shoulder fittings, the waist band and the knot tails
are position-based-dynamics ropes that drape under gravity onto the armour (collision with
friction, cord-to-cord repulsion) down to heavy tassel heads.
Stage 3 (tassels): each tassel hangs as one weighted bundle: a centreline rope as thick as the
fringe, pinned under the binding, drapes onto the armour; its threads are laid around it.
Geometry: smooth cords carrying kongo-gumi braid normal/colour maps, tassel heads of threads
folded over a core with a brass binding, 120 fringe threads per tassel.
"""
from pathlib import Path
import argparse, json, sys, time
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cord_geometry import catmull, frames, tube, resample, braid_tube, braid_textures, monkey_fist, coil
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
solid = [o for o in objs if not o.name.startswith('Energy seam')]   # linings included: tassels must not fall into the neck
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

# ---------------------------------------------------------------- stage 2: cords
S = RopeSystem(); obstacles = []
def obstacle(points, radius):
    idx = S.add_rope(points, 1, radius)
    for i in idx: S.pin(i)
    obstacles.append(idx); return idx

# Neck knot (ball) and its two cords from the mask; tails to the tassel heads.
NECK_BALL = (2.6 + 1.5) * NECK_R
Kn, nn = front(*NECK_KNOT, NECK_BALL * .8); un, vn, wn = frame_at(Kn, nn)
obstacle(np.array([Kn + NECK_BALL * .45 * d for d in (0 * un, un, -un, vn, -vn, wn)]), NECK_BALL * .62)
ropes = {}; neck_ends = {}
for side, sgn, anchor in (('A', -1, NECK_ANCHORS[0]), ('B', 1, NECK_ANCHORS[1])):
    top, _ = front(*anchor, 1.3 * NECK_R)
    mid1, _ = front(anchor[0] * .9, anchor[1] - .03, 1.6 * NECK_R); mid2, _ = front(anchor[0] * .6, anchor[1] - .06, 1.8 * NECK_R)
    entry = Kn + NECK_BALL * (sgn * .55 * un + .45 * vn)              # hidden inside the ball
    pts = resample(catmull([top, mid1, mid2, entry], 8), 1.4 * NECK_R)
    ropes[f'neck {side}'] = S.add_rope(pts, 1, NECK_R, bend=.5, pin_first=True, pin_last=True, slack=1.03)
    exit_pt = Kn + NECK_BALL * (sgn * .32 * un - .62 * vn)
    tail = resample(np.array([exit_pt, exit_pt + np.array([sgn * .004, -.004, -.03])]), 1.4 * NECK_R)
    ropes[f'neck tail {side}'] = S.add_rope(tail, 1, NECK_R, bend=.5, pin_first=True)
    S.set_mass(ropes[f'neck tail {side}'][-1], 6, .0085)
# Shoulder cords: short braid from the fitting to a tassel head.
for i, anchor in enumerate(SHOULDER_ANCHORS):
    top, _ = front(*anchor, 1.4 * SHOULDER_R)
    pts = resample(np.array([top, top + np.array([0, -.004, -.045])]), 1.4 * SHOULDER_R)
    ropes[f'shoulder {i}'] = S.add_rope(pts, 1, SHOULDER_R, bend=.5, pin_first=True)
    S.set_mass(ropes[f'shoulder {i}'][-1], 6, .0075)
# Waist: knot, the band around the body (one cord: tail B - knot B - band - knot A - tail A),
# two bow loops and two tails.
WAIST_BALL = (2.6 + 1.5) * WAIST_R
Kw, nw = front(*WAIST_KNOT, WAIST_BALL * .8); uw, vw, ww = frame_at(Kw, nw)
obstacle(np.array([Kw + WAIST_BALL * .45 * d for d in (0 * uw, uw, -uw, vw, -vw, ww)]), WAIST_BALL * .62)
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
entryA, entryB = Kw - WAIST_BALL * .55 * uw, Kw + WAIST_BALL * .55 * uw
angA = np.arctan2(entryA[1], entryA[0]); angB = np.arctan2(entryB[1], entryB[0])
pts = [entryB]
for t, q in sorted(band, key=lambda b: (np.arctan2(b[1][1], b[1][0]) - angB) % (2 * np.pi)):
    ang = (np.arctan2(q[1], q[0]) - angB) % (2 * np.pi)
    if .08 < ang < ((angA - angB) % (2 * np.pi)) - .08: pts.append(q)
pts.append(entryA)
ropes['waist band'] = S.add_rope(resample(catmull(pts, 4), 1.5 * WAIST_R), 1, WAIST_R, bend=.6, pin_first=True, pin_last=True, slack=1.01)
for side, sgn, length in (('A', -1, .028), ('B', 1, .036)):
    e = Kw + WAIST_BALL * (sgn * .34 * uw - .6 * vw + .3 * ww)      # front of the ball: hang clear of the skirt
    ropes[f'waist tail {side}'] = S.add_rope(resample(np.array([e, e + np.array([0, -.008, -length])]), 1.4 * WAIST_R), 1, WAIST_R, bend=.6, pin_first=True)
    S.set_mass(ropes[f'waist tail {side}'][-1], 8, .011)
log(f'stage 2: {len(S.x)} particles')
rep2 = S.simulate(collider, seconds=2.5, dt=1 / 240, iterations=24, damping=.985, friction=.6, max_speed=2., log=log)
X = np.array(S.x)
paths = {k: X[v] for k, v in ropes.items()}

# ---------------------------------------------------------------- stage 3: tassel fringes
# A tassel hangs as one bundle: its centreline is a rope as thick as the fringe, pinned under the
# binding, draped by gravity onto the armour. Threads are laid around it afterwards.
TASSELS = {'neck A': ('neck tail A', .011, .05), 'neck B': ('neck tail B', .011, .05),
           'shoulder 0': ('shoulder 0', .009, .07), 'shoulder 1': ('shoulder 1', .009, .07),
           'waist A': ('waist tail A', .013, .075), 'waist B': ('waist tail B', .013, .075)}
profile = lambda u: 1 + .8 * np.sin(np.minimum(u * 2.2, 1) * np.pi / 2) - .35 * u ** 2   # x binding radius
F = RopeSystem()
for name, idx in ropes.items():                                      # settled cords as obstacles
    q = F.add_rope(X[idx], 1, S.r[idx[0]])
    for i in q: F.pin(i)
for K_, ball in ((Kn, NECK_BALL), (Kw, WAIST_BALL)):
    q = F.add_rope(np.array([K_, K_ + np.array([0, 0, -1e-4])]), 1, ball * .8)
    for i in q: F.pin(i)
heads = {}; centre_lines = {}
for name, (rope, rh, length) in TASSELS.items():
    path = paths[rope]; H = path[-1]
    axis = H - path[-3]; axis /= np.linalg.norm(axis)
    e1 = np.cross(axis, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(axis, e1)
    bind = H + axis * rh * .95; rb = rh * .68
    heads[name] = (H, axis, e1, e2, rh, bind, rb, length)
    u_lv = np.linspace(0, 1, 11)
    # Fringe starts straight down from under the binding (weighted silk), slightly off the armour.
    down = np.array([0, -.25, -1.]); down /= np.linalg.norm(down)
    line = np.array([bind + down * length * u for u in u_lv])
    idx = F.add_rope(line, 1, rb * 1.4, bend=.8, pin_first=True)   # weighted silk: hangs as a bundle
    F.pin(idx[1])                                                     # leaves the binding along its axis
    for k in range(len(idx) - 3): F.link(idx[k], idx[k + 3], stiffness=.6)   # longer-range bending stiffness
    centre_lines[name] = idx
log(f'stage 3: {len(F.x)} particles')
rep3 = F.simulate(collider, seconds=1.5, dt=1 / 300, iterations=20, damping=.97, friction=.4, max_speed=1.5, log=log)
XF = np.array(F.x)

# ---------------------------------------------------------------- geometry
def material(name, rgb, rough, metal=0., sheen=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Sheen Weight'].default_value = sheen
    return m
mats = [material('Braided silk cord / lacquer red', (.2, .01, .009), .72),
        material('Tassel thread / silk red', (.3, .016, .014), .55),
        material('Tassel binding / aged brass', (.42, .26, .08), .38, metal=1.),
        material('Tassel core / dark red', (.06, .004, .004), .8)]

tex_dir = Path(a.output).parent; bcol, bnrm = braid_textures(tex_dir)
bm_ = mats[0]; nt = bm_.node_tree; bs = nt.nodes['Principled BSDF']
ct = nt.nodes.new('ShaderNodeTexImage'); ct.image = bpy.data.images.load(str(bcol.resolve())); ct.image.pack()
nt_img = nt.nodes.new('ShaderNodeTexImage'); nt_img.image = bpy.data.images.load(str(bnrm.resolve())); nt_img.image.colorspace_settings.name = 'Non-Color'; nt_img.image.pack()
nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.
nt.links.new(ct.outputs['Color'], bs.inputs['Base Color']); nt.links.new(nt_img.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])

def build(name, fill, mat_index):
    bm = bmesh.new(); fill(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])                        # closed tubes: outward
    bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.normal_update()            # glTF tangents need tris
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    for poly in mesh.polygons: poly.use_smooth = True
    mesh.materials.append(mats[mat_index])
    for m in mats: m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = .3
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    return len(mesh.polygons)

def strip_near(path, centre, radius):
    """Drop path points inside a radius of the knot centre (the knot geometry replaces them)."""
    return path[np.linalg.norm(path - centre, axis=1) > radius]

tri = {}
def cords(bm):
    for side in 'AB':                                                 # anchor -> ball, ball -> tail
        braid_tube(bm, paths[f'neck {side}'], NECK_R); braid_tube(bm, paths[f'neck tail {side}'], NECK_R)
    for i in range(2): braid_tube(bm, paths[f'shoulder {i}'], SHOULDER_R)
    braid_tube(bm, paths['waist band'], WAIST_R)
    for side in 'AB': braid_tube(bm, paths[f'waist tail {side}'], WAIST_R)
    monkey_fist(bm, Kn, un, vn, wn, NECK_R, cord=braid_tube); monkey_fist(bm, Kw, uw, vw, ww, WAIST_R, cord=braid_tube)
tri['cords'] = build('Cords / kumihimo braid', cords, 0)

def tassel_threads(bm):
    rng = np.random.default_rng(1615)
    for name, (H, axis, e1, e2, rh, bind, rb, length) in heads.items():
        line = XF[centre_lines[name]]
        line = resample(catmull(list(line), 4), length / 14)
        T, N, B = frames(line)
        u = np.linspace(0, 1, len(line)); r = rb * profile(u)
        # Thread frames follow the draped centreline; align N with the head's e1 so the dome and
        # fringe angles match.
        rot = np.arctan2(np.dot(N[0], e2), np.dot(N[0], e1))
        for j in range(120):
            phi = rng.uniform(0, 2 * np.pi); rho = np.sqrt(rng.uniform(.3, 1)); end = rng.uniform(.9, 1.)
            radial = np.cos(phi) * e1 + np.sin(phi) * e2
            dome = [H - axis * rh * 1.02 * np.cos(t) + radial * rh * np.sin(t) for t in np.linspace(.18, np.pi * .62, 6)]
            ang = phi - rot
            wob = rng.normal(0, .12, 2)
            fr = line + (rho * r)[:, None] * ((np.cos(ang) + wob[0] * u)[:, None] * N + (np.sin(ang) + wob[1] * u)[:, None] * B)
            fr = fr[: max(int(len(fr) * end), 3)]
            path = resample(catmull(dome + [bind + radial * rb * 1.05] + list(fr[1:]), 3), rb * .6)
            rr = np.full(len(path), rb * .09); rr[-4:] *= np.linspace(1, .5, 4)
            tube(bm, path, rr, sides=3)
tri['tassel threads'] = build('Tassels / silk threads', tassel_threads, 1)

def bindings(bm):
    for name, (H, axis, e1, e2, rh, bind, rb, length) in heads.items():
        coil(bm, bind, axis, e1, e2, lambda u: rb + .0012, -.0022, .0022, 4.5, .0009)
tri['bindings'] = build('Tassels / brass binding', bindings, 2)

def cores(bm):
    for name, (H, axis, e1, e2, rh, bind, rb, length) in heads.items():
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1)
        for v in sph['verts']:
            q = np.array(v.co); v.co = Vector(H + q[0] * rh * .92 * e1 + q[1] * rh * .92 * e2 + q[2] * rh * .98 * (-axis))
tri['cores'] = build('Tassels / core', cores, 3)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True, export_tangents=True)
report = {'knots': 'monkey fist ball knots, 2 x 3 wraps woven over/under, rolled 45 deg', 'cord_surface': 'smooth tube + tileable kongo-gumi braid normal/colour maps', 'tassel_model': 'draped centreline rope (bundle radius) + 120 threads in a bulging profile',
          'stage2': rep2, 'stage3': rep3, 'tassel_centrelines': {k: XF[v].round(4).tolist() for k, v in centre_lines.items()}, 'heads': {k: {'centre': v[0].round(4).tolist(), 'axis': v[1].round(3).tolist()} for k, v in heads.items()}, 'neck_knot': Kn.round(4).tolist(), 'waist_knot': Kw.round(4).tolist(), 'triangles': tri, 'radii': {'neck': NECK_R, 'shoulder': SHOULDER_R, 'waist': WAIST_R},
          'tassels': {k: {'head_radius': v[1], 'fringe_length': v[2], 'threads': 120} for k, v in TASSELS.items()},
          'seconds': time.monotonic() - t_start}
Path(a.output).with_name('tie-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
