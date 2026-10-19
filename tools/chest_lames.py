"""Rebuild the front of the dō as clean overlapping lames (okegawa-dō) after the reference.

TRELLIS's chest is a lumpy single shell that merged two of the reference's lames. The lame
outlines are traced in the reference itself (arched gap curves, quadratic fits), carried into the
model through the inverse of the silhouette + optical-flow mapping of project_reference.py, and
built on a smoothed fit of the chest: each lame leans out to a rolled lower edge with gold edging
and tucks its top under the lame above. Texture coordinates are the reference pixels themselves,
so painted gaps, lacing and gold clips line up with the geometry by construction. The old surface
in the area is pushed back behind the lames.
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np
import cv2
from scipy import ndimage
from PIL import Image
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cord_geometry import tube, resample

p = argparse.ArgumentParser()
p.add_argument('--model', required=True, help='Character with the generated cords cleared')
p.add_argument('--output', required=True)
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--flow-cache', default='.tmp/v3/flow.npz')
a = p.parse_args()
out = Path(a.output).parent; out.mkdir(parents=True, exist_ok=True)

# Gap curves traced in reference.png: v(u) = c0 (u - 460)^2 + c1 (u - 460) + c2 (pixels).
# 0 = top edge of the top lame, 1-5 = gaps, 6 = bottom edge. Lame u extents from the lacquer.
CURVES = [(-1.5e-04, -.05388, 431.09), (1.87e-03, -.03879, 452.95), (7.7e-04, -.02853, 490.86),
          (1.91e-03, -.04647, 521.58), (2.2e-03, -.04635, 558.11), (1.8e-03, -.04217, 598.46),
          (5.0e-04, -.03063, 642.75)]
U_RANGE = [(392, 548), (388, 552), (386, 553), (388, 552), (392, 550), (398, 548)]
LEAN, BASE, TUCK_PX, THICK = .0055, .0022, 4.5, .0025
ROLL_R, GILT_R = .0026, .0010
def curve(k, u): c = CURVES[k]; return c[0] * (u - 460) ** 2 + c[1] * (u - 460) + c[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
bm = bmesh.new(); bm.from_mesh(body.data); tree = BVHTree.FromBMesh(bm); bm.free()

# 1. Smoothed chest field y(x, z) from rays (robust polynomial + clipped residual, as the back plate).
gx = np.arange(-.19, .09, .002); gz = np.arange(1.15, 1.48, .002)
Y = np.full((len(gz), len(gx)), np.nan)
for j, z in enumerate(gz):
    for i, x in enumerate(gx):
        h = tree.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
        if h[0] is not None: Y[j, i] = h[0].y
hits = np.isfinite(Y)
X0, Z0 = np.meshgrid((gx - gx.mean()) / np.ptp(gx), (gz - gz.mean()) / np.ptp(gz))
terms = [(i, j) for i in range(5) for j in range(5 - i)]
A = np.stack([X0 ** i * Z0 ** j for i, j in terms], -1)
keep = hits.copy()
for _ in range(8):
    coef, *_ = np.linalg.lstsq(A[keep], Y[keep], rcond=None); fit = A @ coef
    keep = hits & (np.abs(Y - fit) < .006)                             # lumps and holes out
field = fit + ndimage.gaussian_filter(np.clip(np.where(keep, Y - fit, 0), -.003, .003), 3)
def surf(x, z):
    return ndimage.map_coordinates(field, [(np.asarray(z) - gz[0]) / .002, (np.asarray(x) - gx[0]) / .002], order=1, mode='nearest')

cache = np.load(a.flow_cache); flow = cache['flow']; s_px, u0, v0 = float(cache['pixels_per_unit']), float(cache['u0']), float(cache['v0'])
def flow_at(q):
    return np.stack([ndimage.map_coordinates(flow[..., c], [q[:, 1], q[:, 0]], order=1, mode='nearest') for c in range(2)], -1)
def ref_of(x, z):
    """model (x, z) -> reference pixel."""
    q = np.stack([u0 + s_px * np.asarray(x, float).ravel(), v0 - s_px * np.asarray(z, float).ravel()], -1)
    return q + flow_at(q)
def model_of(u, v):
    """reference pixel -> model (x, z): solve q + flow(q) = R by fixed-point iteration."""
    R = np.stack([np.asarray(u, float).ravel(), np.asarray(v, float).ravel()], -1); q = R.copy()
    for _ in range(12): q = R - flow_at(q)
    return (q[:, 0] - u0) / s_px, (v0 - q[:, 1]) / s_px

# The flow field is noisy at the centimetre scale and kinks lame edges: geometry uses a smooth cubic
# fit of the inverse mapping over the chest (texture still uses the exact reference pixels).
gu, gv = np.meshgrid(np.arange(380, 561, 5.), np.arange(420, 651, 5.))
gx_, gz_ = model_of(gu, gv)
def basis(u, v):
    u = (np.asarray(u, float).ravel() - 470) / 90; v = (np.asarray(v, float).ravel() - 535) / 115
    return np.stack([u ** i * v ** j for i in range(4) for j in range(4 - i)], -1)
Bm = basis(gu, gv)
cx_, *_ = np.linalg.lstsq(Bm, gx_, rcond=None); cz_, *_ = np.linalg.lstsq(Bm, gz_, rcond=None)
map_rms = float(np.sqrt(np.mean((Bm @ cx_ - gx_) ** 2 + (Bm @ cz_ - gz_) ** 2)))
def model_smooth(u, v):
    B = basis(u, v); return B @ cx_, B @ cz_

# 2. Push the old lumpy surface back behind the lames (it stays as the dark interior of the gaps).
co = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
near = (co[:, 0] > -.22) & (co[:, 0] < .12) & (co[:, 2] > 1.13) & (co[:, 2] < 1.5) & (co[:, 1] < -.02)
R = ref_of(co[near, 0], co[near, 2])
inside = (R[:, 0] > 384) & (R[:, 0] < 556) & (R[:, 1] > curve(0, R[:, 0]) - 3) & (R[:, 1] < curve(6, R[:, 0]) + 2)
idx = np.where(near)[0][inside]
behind = surf(co[idx, 0], co[idx, 2]) + .0015
push = co[idx, 1] < behind
co[idx[push], 1] = behind[push]; pushed = idx[push]
body.data.vertices.foreach_set('co', co.ravel()); body.data.update()

# 3. Texture: the reference crop itself (UVs are reference pixels).
ref = np.asarray(Image.open(a.reference).convert('RGB'))
c0 = np.array([378, 420]); c1 = np.array([562, 652])
crop = ref[c0[1]:c1[1], c0[0]:c1[0]]
scale = 3
crop = cv2.resize(crop, (crop.shape[1] * scale, crop.shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
gain = np.array([.86, .91, .85])                                       # projection albedo gain (pass 3 report)
tex_path = out / 'chest-lames-color.png'
Image.fromarray(np.clip(crop * gain, 0, 255).astype(np.uint8)).save(tex_path)
def uv_px(u, v):
    return np.stack([(np.asarray(u) - c0[0]) / (c1[0] - c0[0]), 1 - (np.asarray(v) - c0[1]) / (c1[1] - c0[1])], -1)

# 4. Lames: front face, back face, side walls; rolled lower edge and gold edging as tubes.
def material(name, rgb, rough, metal=0., coat=0., image=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    if image:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(image.resolve())); t.image.pack()
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m
lacquer = material('Chest lames / reference lacquer', (.1, .01, .008), .42, coat=.1, image=tex_path)
roll_mat = material('Chest lames / rolled edge lacquer', (.07, .006, .005), .38, coat=.15)
gilt = material('Chest lames / gold edging', (.42, .26, .08), .35, metal=1.)

lame_bm = bmesh.new(); uvl = lame_bm.loops.layers.uv.new('UVMap'); edge_bm = bmesh.new(); gilt_bm = bmesh.new()
nx, nt = 70, 12
report = []
for k in range(len(CURVES) - 1):
    ul, ur = U_RANGE[k]
    us = np.linspace(ul, ur, nx); ts = np.linspace(0, 1, nt)                 # t: 0 = lower edge, 1 = top
    U = np.repeat(us[None], nt, 0); T = np.repeat(ts[:, None], nx, 1)
    Vb, Vt = curve(k + 1, U), curve(k, U) - TUCK_PX                       # top tucks under the lame above
    V = Vb + T * (Vt - Vb)
    X, Z = model_smooth(U, V); X = X.reshape(nt, nx); Z = Z.reshape(nt, nx)
    frac = np.clip((Vb - V) / np.maximum(Vb - curve(k, U), 1), 0, 1)      # 0 at the lower edge, 1 at the gap above
    lean = LEAN * (1 - frac) ** 1.4
    Yf = surf(X, Z) - BASE - lean
    front = [[lame_bm.verts.new((X[j, i], Yf[j, i], Z[j, i])) for i in range(nx)] for j in range(nt)]
    back = [[lame_bm.verts.new((X[j, i], Yf[j, i] + THICK, Z[j, i])) for i in range(nx)] for j in range(nt)]
    UV = uv_px(U, V)
    for j in range(nt - 1):
        for i in range(nx - 1):
            f = lame_bm.faces.new((front[j][i], front[j][i + 1], front[j + 1][i + 1], front[j + 1][i]))
            for loop, (jj, ii) in zip(f.loops, [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]): loop[uvl].uv = UV[jj, ii]
            lame_bm.faces.new((back[j][i], back[j + 1][i], back[j + 1][i + 1], back[j][i + 1]))
    for j in (0, nt - 1):                                              # top / bottom walls
        for i in range(nx - 1):
            q = (front[j][i], back[j][i], back[j][i + 1], front[j][i + 1]) if j == 0 else (front[j][i], front[j][i + 1], back[j][i + 1], back[j][i])
            lame_bm.faces.new(q)
    for i in (0, nx - 1):                                              # side walls
        for j in range(nt - 1):
            q = (front[j][i], front[j + 1][i], back[j + 1][i], back[j][i]) if i == 0 else (front[j][i], back[j][i], back[j + 1][i], front[j + 1][i])
            lame_bm.faces.new(q)
    lower = np.stack([X[0], Yf[0] + THICK * .4, Z[0]], -1)
    tube(edge_bm, resample(lower, .003), ROLL_R)                       # rolled lower edge
    gold = np.stack([X[0], Yf[0] - ROLL_R * .55, Z[0] + ROLL_R * .9], -1)
    tube(gilt_bm, resample(gold, .003), GILT_R, sides=6)               # gold edging just above the roll
    report.append({'lame': k, 'u': [ul, ur], 'z_centre': float(Z[nt // 2, nx // 2]), 'x': [float(X[0, 0]), float(X[0, -1])]})

def finish(bmx, name, mat):
    bmesh.ops.recalc_face_normals(bmx, faces=bmx.faces[:]); bmesh.ops.triangulate(bmx, faces=bmx.faces[:])
    mesh = bpy.data.meshes.new(name); bmx.to_mesh(mesh); bmx.free()
    for poly in mesh.polygons: poly.use_smooth = True
    mesh.materials.append(mat); obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    return len(mesh.polygons)
tri = {'lames': finish(lame_bm, 'Chest lames / okegawa-do', lacquer), 'rolled edges': finish(edge_bm, 'Chest lames / rolled edges', roll_mat),
       'gold edging': finish(gilt_bm, 'Chest lames / gold edging', gilt)}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
rep = {'smooth_map_rms': map_rms, 'reference_curves': CURVES, 'u_ranges': U_RANGE, 'lean': LEAN, 'tuck_px': TUCK_PX, 'thickness': THICK,
       'field_kept_cells': int(keep.sum()), 'field_cells': int(hits.sum()), 'old_vertices_pushed_back': int(len(pushed)),
       'crop_px': [int(c0[0]), int(c0[1]), int(c1[0]), int(c1[1])], 'triangles': tri, 'lames': report}
(out / 'chest-lames-report.json').write_text(json.dumps(rep, indent=2) + '\n'); print(json.dumps({k: v for k, v in rep.items() if k != 'lames'}))
