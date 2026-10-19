"""Rebuild the lamellar plates (dō front and back, kusazuri, sode) as level, regular lames.

Every panel is defined in a view frame (angle around Z as in render_body_v2.py): s = screen
horizontal, z = height, d = depth along the view. Rays from the view give the plate surface; a
robust polynomial fit removes the generator's lumps. Lames are LEVEL in model space (constant z,
even pitch): each leans out to a rolled lower edge with gold edging and tucks its top under the
lame above. Lame faces sample the reference illustration directly, straightened per lame:
  chest: between the traced reference gap curves (the figure is turned in the illustration, so
         the painted lames arch and slant; straightening makes them level on the model);
  kusazuri / sode: the reference's front skirt panel (lacing rows, gold wave on the bottom lame).
The generated surface under a panel is pushed behind the lames.
"""
from pathlib import Path
import argparse, json, sys
import bpy, bmesh
import numpy as np
from scipy import ndimage
from PIL import Image
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cord_geometry import tube, resample

p = argparse.ArgumentParser()
p.add_argument('--model', required=True, help='Character with the generated cords cleared')
p.add_argument('--output', required=True)
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--only', help='Comma-separated panel names (debugging)')
a = p.parse_args()
out = Path(a.output).parent; out.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- reference atlases (pixels)
# Chest gap curves v(u) = c0 (u-460)^2 + c1 (u-460) + c2: top edge, five gaps, bottom edge.
CHEST_CURVES = [(-1.5e-04, -.05388, 431.09), (1.87e-03, -.03879, 452.95), (7.7e-04, -.02853, 490.86),
                (1.91e-03, -.04647, 521.58), (2.2e-03, -.04635, 558.11), (1.8e-03, -.04217, 598.46),
                (5.0e-04, -.03063, 642.75)]
CHEST_U = [(392, 548), (388, 552), (386, 553), (388, 552), (392, 550), (398, 548)]
def chest_v(k, u): c = CHEST_CURVES[k]; return c[0] * (u - 460) ** 2 + c[1] * (u - 460) + c[2]
# Front skirt panel: level lames between these rows (u 390-512). The top lame is painted over by
# the tassels, so it reuses the second lame's rows.
SKIRT_ROWS = [(754, 790), (754, 790), (790, 830), (830, 872), (872, 946)]
SKIRT_U = (390, 512)
ATLAS = {'chest': {'heights': [1] * 6}, 'chest-back': {'heights': [1] * 6}, 'skirt': {'heights': [36, 36, 40, 42, 74]}}
def ref_uv(atlas, k, fs, t):
    """Reference pixel for lame k at horizontal fraction fs (0 left .. 1 right), height fraction t
    (0 lower edge .. 1 the gap above; > 1 is the tucked part, hidden)."""
    if atlas == 'chest-back':                                         # no painted tassels on the back
        atlas, k = 'chest', max(k, 1)
    if atlas == 'chest':
        u0, u1 = CHEST_U[k]; u = u0 + fs * (u1 - u0)
        vb, vt = chest_v(k + 1, u), chest_v(k, u)
    else:
        u = SKIRT_U[0] + fs * (SKIRT_U[1] - SKIRT_U[0]); vt, vb = SKIRT_ROWS[k]
    return u, vb + t * (vt - vb)

# ---------------------------------------------------------------- panels
# view: degrees (0 front, 180 back, 90 from +x, -90 from -x); s, z: extents in the view frame.
PANELS = [
    # The top lames reach further toward the left shoulder (covers the flattened generated paddle).
    {'name': 'do front', 'view': 0, 's': (-.2, .07), 'z': (1.165, 1.455), 'atlas': 'chest', 'wrap': .012,
     'extend': {'s1': .135, 'z_min': 1.355}},
    {'name': 'do back', 'view': 180, 's': (-.15, .15), 'z': (1.16, 1.45), 'atlas': 'chest-back', 'wrap': .012},
    {'wrap': .006, 'name': 'kusazuri left side', 'view': 90, 's': (-.03, .12), 'z': (.73, .98), 'atlas': 'skirt'},
    {'wrap': .006, 'name': 'kusazuri right side', 'view': -90, 's': (-.12, .03), 'z': (.72, .95), 'atlas': 'skirt'},
    {'wrap': .006, 'name': 'kusazuri front right', 'view': 0, 's': (-.195, -.005), 'z': (.70, 1.07), 'atlas': 'skirt'},
    {'wrap': .006, 'name': 'kusazuri front left', 'view': 45, 's': (-.08, .07), 'z': (.775, 1.07), 'atlas': 'skirt'},
    {'wrap': .006, 'name': 'kusazuri back centre', 'view': 180, 's': (-.037, .153), 'z': (.70, 1.0), 'atlas': 'skirt'},
    {'wrap': .006, 'name': 'kusazuri back left', 'view': 180, 's': (-.213, -.08), 'z': (.735, 1.01), 'atlas': 'skirt'},
    {'wrap': .006, 'name': 'kusazuri back right', 'view': -140, 's': (.01, .25), 'z': (.72, .99), 'atlas': 'skirt'},
    {'wrap': .045, 'name': 'sode left', 'view': 90, 's': (-.085, .09), 'z': (1.345, 1.52), 'atlas': 'skirt'},
    {'wrap': .04, 'name': 'sode right', 'view': -135, 's': (-.08, .14), 'z': (1.29, 1.53), 'atlas': 'skirt'},
]
if a.only: PANELS = [q for q in PANELS if q['name'] in a.only.split(',')]
LEAN, BASE, TUCK, THICK = .0055, .0022, .006, .0025
ROLL_R, GILT_R = .0026, .0010

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
# The pass-2 back plate shell is replaced by real lames ('do back'): remove it first.
for o in [o for o in bpy.context.scene.objects if o.name.startswith('Back plate shell')]:
    if any(q['name'] == 'do back' for q in PANELS): bpy.data.objects.remove(o)
bm0 = bmesh.new(); bm0.from_mesh(body.data); tree = BVHTree.FromBMesh(bm0); bm0.free()
co = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)

ref_img = np.asarray(Image.open(a.reference).convert('RGB')).astype(np.float32)
H_REF, W_REF = ref_img.shape[:2]
gain = np.array([.86, .91, .85])                                      # projection albedo gain (pass 3 report)
tex_path = out / 'plates-color.png'
Image.fromarray(np.clip(ref_img * gain, 0, 255).astype(np.uint8)).save(tex_path)

def material(name, rgb, rough, metal=0., coat=0., image=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    if image:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(image.resolve())); t.image.pack()
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m
lacquer = material('Plates / reference lacquer', (.1, .01, .008), .42, coat=.1, image=tex_path)
dark = material('Plates / underside lacquer', (.03, .006, .005), .5)
roll_mat = material('Plates / rolled edge lacquer', (.07, .006, .005), .38, coat=.15)
gilt = material('Plates / gold edging', (.42, .26, .08), .35, metal=1.)

def frame(view):
    t = np.radians(view)
    return np.array([np.cos(t), np.sin(t), 0.]), np.array([-np.sin(t), np.cos(t), 0.])   # right, forward

reports = []
lame_bm = bmesh.new(); uvl = lame_bm.loops.layers.uv.new('UVMap'); edge_bm = bmesh.new(); gilt_bm = bmesh.new()
for P in PANELS:
    r, f = frame(P['view']); zh = np.array([0, 0, 1.])
    (s0, s1), (zb, zt) = P['s'], P['z']
    step = .003
    gs = np.arange(s0 - .01, (P['extend']['s1'] if 'extend' in P else s1) + .0101, step); gz = np.arange(zb - .01, zt + .0101, step)
    D = np.full((len(gz), len(gs)), np.nan)
    for j, z in enumerate(gz):
        for i, s in enumerate(gs):
            o = s * r + z * zh - f * 1.2
            h = tree.ray_cast(Vector(o), Vector(f), 2.4)
            if h[0] is not None: D[j, i] = np.dot(np.array(h[0]), f)
    hits = np.isfinite(D); med = np.nanmedian(D)
    ok = hits & (D > med - .05) & (D < med + .05)                    # occluders / holes out
    S0, Z0 = np.meshgrid((gs - gs.mean()) / np.ptp(gs), (gz - gz.mean()) / np.ptp(gz))
    terms = [(i, j) for i in range(4) for j in range(4 - i)]
    A = np.stack([S0 ** i * Z0 ** j for i, j in terms], -1)
    keep = ok.copy()
    for _ in range(8):
        coef, *_ = np.linalg.lstsq(A[keep], D[keep], rcond=None); fit = A @ coef
        keep = ok & (np.abs(D - fit) < .007)
    field = fit + ndimage.gaussian_filter(np.clip(np.where(keep, D - fit, 0), -.003, .003), 3)
    def depth(s, z):
        return ndimage.map_coordinates(field, [(np.asarray(z) - gz[0]) / step, (np.asarray(s) - gs[0]) / step], order=1, mode='nearest')
    def world(s, z, d): return s[..., None] * r + z[..., None] * zh + d[..., None] * f

    # push the generated surface under the panel behind the lames
    vs, vz, vd = co @ r, co[:, 2], co @ f
    ext = P.get('extend')
    def s_hi(z): return np.where(np.asarray(z) >= ext['z_min'], ext['s1'], s1) if ext else np.full(np.shape(z), s1)
    inside = (vs > s0 - .004) & (vs < s_hi(vz) + .004) & (vz > zb - .004) & (vz < zt + .004)
    fd = depth(vs[inside], vz[inside])
    idx = np.where(inside)[0]
    win = (vd[idx] > fd - .035) & (vd[idx] < fd + .0015)
    wrap = P.get('wrap', 0.)                                          # plate ends curve back around the body
    vfs = np.clip((vs[inside] - s0) / (s_hi(vz[inside]) - s0), 0, 1)
    idx = idx[win]; target = fd[win] + .0015 + wrap * (2 * vfs[win] - 1) ** 4
    co[idx] += ((target - vd[idx]))[:, None] * f

    # lames
    at = P['atlas']; n = len(ATLAS[at]['heights']); hts = np.array(ATLAS[at]['heights'], float)
    edges = zt - np.concatenate([[0], np.cumsum(hts)]) / hts.sum() * (zt - zb)   # level boundaries, top -> bottom
    nx, nt = 40, 9
    for k in range(n):
        top, bot = edges[k], edges[k + 1]
        s1k = float(s_hi(bot))
        ss = np.linspace(s0, s1k, nx); ts = np.linspace(0, 1 + TUCK / (top - bot), nt)
        Sg, Tg = np.meshgrid(ss, ts); Zg = bot + Tg * (top - bot)
        lean = LEAN * np.clip(1 - Tg, 0, 1) ** 1.4
        Df = depth(Sg, Zg) - BASE - lean + wrap * (2 * (Sg - s0) / (s1k - s0) - 1) ** 4
        Fw = world(Sg, Zg, Df); Bw = world(Sg, Zg, Df + THICK)
        front = [[lame_bm.verts.new(Fw[j, i]) for i in range(nx)] for j in range(nt)]
        back = [[lame_bm.verts.new(Bw[j, i]) for i in range(nx)] for j in range(nt)]
        fs = (Sg - s0) / (s1k - s0)                                     # screen-left is texture-left
        U, V = ref_uv(at, k, fs, Tg)
        UV = np.stack([U / W_REF, 1 - V / H_REF], -1)
        for j in range(nt - 1):
            for i in range(nx - 1):
                fc = lame_bm.faces.new((front[j][i], front[j][i + 1], front[j + 1][i + 1], front[j + 1][i]))
                for loop, (jj, ii) in zip(fc.loops, [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]): loop[uvl].uv = UV[jj, ii]
                lame_bm.faces.new((back[j][i], back[j + 1][i], back[j + 1][i + 1], back[j][i + 1])).material_index = 1
        for j in (0, nt - 1):
            for i in range(nx - 1):
                q = (front[j][i], back[j][i], back[j][i + 1], front[j][i + 1]) if j == 0 else (front[j][i], front[j][i + 1], back[j][i + 1], back[j][i])
                lame_bm.faces.new(q).material_index = 1
        for i in (0, nx - 1):
            for j in range(nt - 1):
                q = (front[j][i], front[j + 1][i], back[j + 1][i], back[j][i]) if i == 0 else (front[j][i], back[j][i], back[j + 1][i], front[j + 1][i])
                lame_bm.faces.new(q).material_index = 1
        lower = Fw[0] + f * THICK * .4
        tube(edge_bm, resample(lower, .006), ROLL_R, sides=6)
        tube(gilt_bm, resample(Fw[0] - f * ROLL_R * .55 + zh * ROLL_R * .9, .006), GILT_R, sides=5)
    reports.append({'panel': P['name'], 'view': P['view'], 's': P['s'], 'z': P['z'], 'atlas': at, 'lames': n,
                    'level_edges_z': [round(float(e), 4) for e in edges], 'rays_hit': int(hits.sum()), 'rays_kept': int(keep.sum()),
                    'generated_vertices_pushed_back': int(len(idx))})
    print(reports[-1]['panel'], reports[-1]['rays_kept'], '/', reports[-1]['rays_hit'], flush=True)
body.data.vertices.foreach_set('co', co.ravel()); body.data.update()

def finish(bmx, name, mats):
    bmesh.ops.recalc_face_normals(bmx, faces=bmx.faces[:]); bmesh.ops.triangulate(bmx, faces=bmx.faces[:])
    mesh = bpy.data.meshes.new(name); bmx.to_mesh(mesh); bmx.free()
    for poly in mesh.polygons: poly.use_smooth = True
    for m in mats: mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    return len(mesh.polygons)
tri = {'lames': finish(lame_bm, 'Plates / lames', [lacquer, dark]), 'rolled edges': finish(edge_bm, 'Plates / rolled edges', [roll_mat]),
       'gold edging': finish(gilt_bm, 'Plates / gold edging', [gilt])}
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
rep = {'lean': LEAN, 'tuck': TUCK, 'thickness': THICK, 'texture': 'reference.png x albedo gain, straightened per lame', 'wrap': 'depth += wrap * (2 s_frac - 1)^4', 'panels': reports, 'triangles': tri}
(out / 'lame-panels-report.json').write_text(json.dumps(rep, indent=2) + '\n'); print(json.dumps(tri))
