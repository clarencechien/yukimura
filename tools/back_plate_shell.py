"""Clean back plate (ushiro-dō) shell over the generated one, textured from back-reference.png.

The remeshed generator output is closed, but its thin back plate has tunnels (dark holes) and
no lames. This fits a smooth height field to the generated back surface, adds overlapping
lame relief whose steps sit on the painted gaps of the back source, sinks the borders into
the body so no edge shows, and maps the crisp source directly (planar UV) instead of
resampling it into the atlas. The generated plate stays underneath, untouched.
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np
from PIL import Image
from scipy import ndimage
from mathutils import Matrix
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from trellis_body_materials import rgb_to_hsv, smoothstep

p = argparse.ArgumentParser()
p.add_argument('--model', default='.tmp/v3/projected.glb')
p.add_argument('--back-reference', default='docs/experiments/future-sanada/body-v2/pass2/back-reference.png')
p.add_argument('--alignment', default='docs/experiments/future-sanada/body-v2/pass2/alignment.json')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/pass2')
p.add_argument('--half-width', type=float, default=.145)
p.add_argument('--z-range', type=float, nargs=2, default=(1.135, 1.455))
p.add_argument('--gap-rows', type=float, nargs='+', default=[379, 416, 453, 490, 526, 563, 600], help='Painted lame gaps (back-reference pixels)')
a = p.parse_args()
out = Path(a.output)
fit = json.loads(Path(a.alignment).read_text()); s, u0, v0 = fit['pixels_per_unit'], fit['u0'], fit['v0']

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
co = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nm = np.empty(len(body.data.vertices) * 3, np.float32); body.data.vertices.foreach_get('normal', nm); nm = nm.reshape(-1, 3)

# Height field y(x, z) of the outermost back surface (back = +Y): one ray per cell from behind.
# (The remeshed plate is flat with large triangles, so vertex sampling misses the outer shell.)
from mathutils.bvhtree import BVHTree
from mathutils import Vector
hw, (z0, z1) = a.half_width, a.z_range
margin = .03; step = .003
xs = np.arange(-hw - margin, hw + margin + 1e-9, step); zs = np.arange(z0 - margin, z1 + margin + 1e-9, step)
bm_ = bmesh.new(); bm_.from_mesh(body.data); tree = BVHTree.FromBMesh(bm_); bm_.free()
field = np.full((len(zs), len(xs)), np.nan)
for j, z in enumerate(zs):
    for i, x in enumerate(xs):
        hit = tree.ray_cast(Vector((x, 1.0, z)), Vector((0, -1, 0)), 2.0)
        if hit[0] is not None: field[j, i] = hit[0].y
hits = np.isfinite(field)
# A plate is smooth: robust bivariate polynomial fit. Rays through the plate's tunnels hit deeper
# surfaces and are rejected iteratively (one-sided: only cells below the fit by > 4 mm).
X0, Z0 = np.meshgrid((xs - xs.mean()) / (xs.ptp() / 2), (zs - zs.mean()) / (zs.ptp() / 2))
DEG = 4
terms = [(i, j) for i in range(DEG + 1) for j in range(DEG + 1 - i)]
A = np.stack([X0 ** i * Z0 ** j for i, j in terms], -1)
keep = hits.copy()
for _ in range(8):
    coef, *_ = np.linalg.lstsq(A[keep], field[keep], rcond=None)
    smooth = A @ coef
    keep = hits & (field > smooth - .004)
residual = np.where(keep, field - smooth, 0)
# Keep gentle shape the polynomial misses (|residual| < 3 mm, blurred), never the tunnels.
field = smooth + ndimage.gaussian_filter(np.clip(residual, -.003, .003), 3)
known = keep

# Lame relief: each lame leans out toward its lower edge, the next one starts tucked under it.
gaps_z = sorted((v0 - np.array(a.gap_rows)) / s, reverse=True)       # top to bottom
def relief(z):
    r = np.zeros_like(z)
    edges = [z1 + .05] + gaps_z + [z0 - .05]
    for top, bottom in zip(edges[:-1], edges[1:]):
        inside = (z <= top) & (z > bottom)
        t = (top - z) / max(top - bottom, 1e-6)
        r = np.where(inside, .0055 * t ** 1.5, r)
    return r
X, Z = np.meshgrid(xs, zs)
edge = np.minimum.reduce([smoothstep(0, .02, hw - np.abs(X)), smoothstep(0, .02, Z - z0), smoothstep(0, .02, z1 - Z)])
Y = field + (-.006 + edge * (.009 + relief(Z)))                         # borders sink below the body

# Build the grid mesh with planar UVs into a crop of the back source.
src = Image.open(a.back_reference).convert('RGBA')
cu0, cu1 = int(u0 + s * xs[0]) - 2, int(u0 + s * xs[-1]) + 3
cv0, cv1 = int(v0 - s * zs[-1]) - 2, int(v0 - s * zs[0]) + 3
crop = src.crop((cu0, cv0, cu1, cv1)).resize(((cu1 - cu0) * 2, (cv1 - cv0) * 2), Image.LANCZOS)
gain = np.array(json.loads((out / 'projection-report.json').read_text())['projection']['albedo_gain'], np.float32)
crop_rgb = np.clip(np.asarray(crop.convert('RGB'), np.float32) / 255 * gain, 0, 1)
crop = Image.fromarray((crop_rgb * 255 + .5).astype(np.uint8))
crop_path = out / 'back-plate-color.png'; crop.save(crop_path)
rgb = np.asarray(crop.convert('RGB'), np.float32) / 255
h, sat, val = rgb_to_hsv(rgb)
gold = smoothstep(24, 32, h) * (1 - smoothstep(60, 70, h)) * smoothstep(.25, .4, sat) * smoothstep(.28, .4, val)
red = (1 - smoothstep(14, 24, np.abs(((h + 180) % 360) - 180))) * smoothstep(.3, .45, sat) * (1 - gold)
mr = np.zeros(rgb.shape, np.float32)
mr[..., 1] = red * .52 + gold * .32 + (1 - red - gold).clip(0) * .6
mr[..., 2] = gold + (1 - red - gold).clip(0) * .12
mr_path = out / 'back-plate-metal-rough.png'; Image.fromarray((mr * 255).astype(np.uint8)).save(mr_path)

mesh = bpy.data.meshes.new('Back plate shell'); bm = bmesh.new()
verts = [[bm.verts.new((X[j, i], Y[j, i], Z[j, i])) for i in range(len(xs))] for j in range(len(zs))]
uvl = bm.loops.layers.uv.new('UVMap')
def uv_of(x, z):
    return (((u0 + s * x) - cu0) / (cu1 - cu0), 1 - ((v0 - s * z) - cv0) / (cv1 - cv0))
for j in range(len(zs) - 1):
    for i in range(len(xs) - 1):
        f = bm.faces.new((verts[j][i], verts[j + 1][i], verts[j + 1][i + 1], verts[j][i + 1]))
        for loop in f.loops: loop[uvl].uv = uv_of(loop.vert.co.x, loop.vert.co.z)
bm.normal_update()
if np.mean([f.normal.y for f in bm.faces]) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(mesh); bm.free()
for poly in mesh.polygons: poly.use_smooth = True
shell = bpy.data.objects.new('Back plate shell / reference lames', mesh); bpy.context.collection.objects.link(shell)
mat = bpy.data.materials.new('Back plate lacquer / reference'); mat.use_nodes = True; nodes = mat.node_tree.nodes; links = mat.node_tree.links
bsdf = nodes['Principled BSDF']
tc = nodes.new('ShaderNodeTexImage'); tc.image = bpy.data.images.load(str(crop_path.resolve())); tc.image.pack()
tm = nodes.new('ShaderNodeTexImage'); tm.image = bpy.data.images.load(str(mr_path.resolve())); tm.image.colorspace_settings.name = 'Non-Color'; tm.image.pack()
sep = nodes.new('ShaderNodeSeparateColor')
links.new(tc.outputs['Color'], bsdf.inputs['Base Color']); links.new(tm.outputs['Color'], sep.inputs['Color'])
links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
bsdf.inputs['Coat Weight'].default_value = .08; bsdf.inputs['Coat Roughness'].default_value = .2
mesh.materials.append(mat)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str((out / 'body-v2-pass2.glb').resolve()), export_format='GLB', use_selection=True)
report = {'half_width': hw, 'z_range': [z0, z1], 'grid_step': step, 'cells': list(field.shape), 'ray_hits': int(hits.sum()), 'kept_cells': int(known.sum()), 'fit': f'robust degree-{DEG} polynomial + clipped residual',
          'gap_rows_px': a.gap_rows, 'gap_z': [float(g) for g in gaps_z], 'relief_max': .0055, 'offset_inside': .003, 'border_sink': -.006,
          'shell_triangles': len(mesh.polygons), 'crop_px': [cu0, cv0, cu1, cv1],
          'triangles': sum(len(f.vertices) - 2 for o in bpy.context.scene.objects if o.type == 'MESH' for f in o.data.polygons)}
(out / 'back-plate-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
