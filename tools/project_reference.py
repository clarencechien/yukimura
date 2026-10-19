"""Project the sharp reference illustration onto the dō and skirt of body v2.

TRELLIS.2 textures are blurred versions of the same image the model was generated from, so
the front of the torso / skirt takes its colour straight from reference.png. Alignment is a
silhouette fit (scale + offset, orthographic) refined by dense optical flow between a flat
front render of the model and the reference. Visibility comes from a z-buffer of baked texel
positions. The back has no reference; it uses back-reference.png (build_back_reference.py)
through the same mapping. Metallic / roughness / coat are re-derived for projected texels.

Run with Blender 4.3 bpy + NumPy + SciPy + OpenCV (render env).
"""
from pathlib import Path
import argparse, json, sys, time
import bpy, bmesh
import numpy as np
import cv2
from scipy import ndimage
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from trellis_body_materials import rgb_to_hsv, smoothstep, REFERENCE_RED_HUE

p = argparse.ArgumentParser()
p.add_argument('--model', default='docs/experiments/future-sanada/body-v2/refined/body-v2.glb')
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--back-reference', default='docs/experiments/future-sanada/body-v2/pass2/back-reference.png')
p.add_argument('--alignment', default='docs/experiments/future-sanada/body-v2/pass2/alignment.json')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/pass2')
p.add_argument('--output-glb', default='.tmp/v3/projected.glb', help='Intermediate; back_plate_shell.py writes the final pass-2 GLB')
p.add_argument('--flow-cache', default='.tmp/v3/flow.npz', help='Smoothed render->reference flow, reused by energy_seam_strips.py')
p.add_argument('--fill-holes', type=int, default=48, help='Fill boundary loops up to this many edges inside the dō / skirt')
a = p.parse_args()
out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
started = time.monotonic(); report = {'model': a.model}

# Regions in normalized body space (height 2, front = -Y). Torso / skirt only, as reviewed.
# abs_x: (min, max) band; back: whether the composed back source applies (only the dō has one).
REGIONS = {
    'do': {'abs_x': (0, .185), 'z': (1.04, 1.47), 'back': True},       # front chest / back plate incl. waist band
    'skirt': {'abs_x': (0, .27), 'z': (.56, 1.12), 'back': True},      # kusazuri (overlaps the dō: no seam dip)
    'arms': {'abs_x': (.17, .47), 'z': (.74, 1.47), 'back': False},    # sode, gauntlets, gloves
    'legs': {'abs_x': (0, .26), 'z': (0, .62), 'back': False},         # knees, shins, boots
}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
head = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name != body.name]

def in_regions(co):
    keep = np.zeros(len(co), bool)
    for r in REGIONS.values():
        keep |= (np.abs(co[:, 0]) >= r['abs_x'][0]) & (np.abs(co[:, 0]) < r['abs_x'][1]) & (co[:, 2] > r['z'][0]) & (co[:, 2] < r['z'][1])
    return keep

# 1. Close small holes in the dō / skirt (torn generated shells). New loops copy neighbour UVs.
print('filling holes', flush=True)
bm = bmesh.new(); bm.from_mesh(body.data); uv = bm.loops.layers.uv.active
# glTF import splits vertices on UV seams; weld (UVs live on loops) so only real holes are boundaries.
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6); bm.edges.index_update()
boundary = [e for e in bm.edges if e.is_boundary]
filled = 0
if a.fill_holes:
    seen = set(); loops = []
    for e in boundary:
        if e.index in seen: continue
        group = []; stack = [e]; seen.add(e.index)
        while stack:
            g = stack.pop(); group.append(g)
            for v in g.verts:
                for n in v.link_edges:
                    if n.is_boundary and n.index not in seen: seen.add(n.index); stack.append(n)
        loops.append(group)
    for group in loops:
        centre = np.mean([np.array(v.co) for e in group for v in e.verts], 0)
        if 3 <= len(group) <= a.fill_holes and in_regions(centre[None])[0]:
            new = bmesh.ops.holes_fill(bm, edges=group, sides=len(group))['faces']
            for f in new:
                for loop in f.loops:
                    donor = next((l for l in loop.vert.link_loops if l.face not in new), None)
                    if donor: loop[uv].uv = donor[uv].uv
            bmesh.ops.triangulate(bm, faces=new); filled += 1
    bm.to_mesh(body.data)
report['holes'] = {'boundary_edges_before': len(boundary), 'loops_filled': filled}
print('holes', report['holes'], flush=True)
bm.free()

# 2. Rasterize per-texel object-space position and normal in UV space (NumPy, no Cycles bake).
material = body.data.materials[0]; nodes = material.node_tree.nodes
bsdf = nodes['Principled BSDF']
color_node = bsdf.inputs['Base Color'].links[0].from_node
mr_node = bsdf.inputs['Metallic'].links[0].from_node
while mr_node.type != 'TEX_IMAGE': mr_node = mr_node.inputs[0].links[0].from_node
coat_node = bsdf.inputs['Coat Weight'].links[0].from_node
while coat_node.type != 'TEX_IMAGE': coat_node = coat_node.inputs[0].links[0].from_node
size = color_node.image.size[0]
t = time.monotonic()
mesh = body.data; mesh.calc_loop_triangles()
tri_loops = np.empty(len(mesh.loop_triangles) * 3, np.int32); mesh.loop_triangles.foreach_get('loops', tri_loops); tri_loops = tri_loops.reshape(-1, 3)
loop_vert = np.empty(len(mesh.loops), np.int32); mesh.loops.foreach_get('vertex_index', loop_vert)
uvs = np.empty(len(mesh.loops) * 2, np.float32); mesh.uv_layers.active.data.foreach_get('uv', uvs); uvs = uvs.reshape(-1, 2)
co = np.empty(len(mesh.vertices) * 3, np.float32); mesh.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
vn = np.empty(len(mesh.vertices) * 3, np.float32); mesh.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)
pos = np.zeros((size, size, 4), np.float32); nrm = np.zeros((size, size, 3), np.float32)
T = uvs[tri_loops] * size - .5                      # texel centres at integer coords
V = loop_vert[tri_loops]
lo = np.floor(T.min(1)).astype(int); hi = np.ceil(T.max(1)).astype(int)
extent = (hi - lo).max(1) + 1
for bucket in [2, 4, 8, 16, 32, 64, 128, 256]:
    sel = np.where((extent <= bucket) & (extent > bucket // 2) if bucket > 2 else extent <= 2)[0]
    gy, gx = np.mgrid[0:bucket, 0:bucket]; offs = np.stack([gx.ravel(), gy.ravel()], 1)
    for chunk in np.array_split(sel, max(1, len(sel) * bucket * bucket // 8_000_000 + 1)):
        if not len(chunk): continue
        px = lo[chunk, None, :] + offs[None]                       # (n, k, 2)
        a_, b_, c_ = T[chunk, 0, None], T[chunk, 1, None], T[chunk, 2, None]
        v0, v1, v2 = b_ - a_, c_ - a_, px - a_
        den = v0[..., 0] * v1[..., 1] - v1[..., 0] * v0[..., 1]
        den = np.where(np.abs(den) < 1e-12, 1e-12, den)
        w1 = (v2[..., 0] * v1[..., 1] - v1[..., 0] * v2[..., 1]) / den
        w2 = (v0[..., 0] * v2[..., 1] - v2[..., 0] * v0[..., 1]) / den
        w0 = 1 - w1 - w2
        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4) & (px[..., 0] >= 0) & (px[..., 1] >= 0) & (px[..., 0] < size) & (px[..., 1] < size)
        ti, ki = np.nonzero(inside)
        w = np.stack([w0[ti, ki], w1[ti, ki], w2[ti, ki]], 1)[..., None]
        verts = V[chunk[ti]]
        x, y = px[ti, ki, 0], px[ti, ki, 1]
        pos[y, x, :3] = (co[verts] * w).sum(1); pos[y, x, 3] = 1
        nrm[y, x] = (vn[verts] * w).sum(1)
nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-8)
report['rasterize_seconds'] = time.monotonic() - t; report['texels_covered'] = int((pos[..., 3] > 0).sum())
print('rasterized', report['rasterize_seconds'], report['texels_covered'], flush=True)
scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
covered = pos[..., 3] > .5
P = pos[..., :3]; N = nrm

# 3. Alignment: silhouette fit + optical flow between a flat front render and the reference.
def load(path):
    im = bpy.data.images.load(str(Path(path).resolve())); arr = np.empty(im.size[0] * im.size[1] * 4, np.float32)
    im.pixels.foreach_get(arr); return arr.reshape(im.size[1], im.size[0], 4)[::-1]  # top row first
ref = load(a.reference); back_ref = load(a.back_reference); H, W = ref.shape[:2]
fit = json.loads(Path(a.alignment).read_text())
s, u0, v0 = fit['pixels_per_unit'], fit['u0'], fit['v0']
# Flat front render of the model's current base colour, same pixel grid as the reference.
for o in head: o.hide_render = True
flat = bpy.data.materials.new('flat base colour'); flat.use_nodes = True; fn = flat.node_tree.nodes
em = fn.new('ShaderNodeEmission'); tex = fn.new('ShaderNodeTexImage'); tex.image = color_node.image
uvn = fn.new('ShaderNodeUVMap'); uvn.uv_map = body.data.uv_layers.active.name
flat.node_tree.links.new(uvn.outputs['UV'], tex.inputs['Vector']); flat.node_tree.links.new(tex.outputs['Color'], em.inputs['Color'])
flat.node_tree.links.new(em.outputs['Emission'], fn['Material Output'].inputs['Surface'])
body.data.materials[0] = flat
cam = bpy.data.objects.new('ref cam', bpy.data.cameras.new('ref cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.sensor_fit = 'VERTICAL'; cam.data.ortho_scale = H / s
cam.location = ((W / 2 - u0) / s, -5, (v0 - H / 2) / s); cam.rotation_euler = (np.pi / 2, 0, 0)
scene.render.resolution_x, scene.render.resolution_y = W, H; scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'; scene.cycles.samples = 4
scene.render.filepath = str((out / 'flat-front.png').resolve()); scene.render.image_settings.color_mode = 'RGBA'
bpy.ops.render.render(write_still=True)
body.data.materials[0] = material
flat_img = load(out / 'flat-front.png')
def gray(img):
    g = (img[..., :3] @ [.299, .587, .114]) * (img[..., 3] > .5)
    return np.clip(g * 255, 0, 255).astype(np.uint8)
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
flow = dis.calc(gray(flat_img), gray(ref), None)            # render pixel -> reference pixel
both = (flat_img[..., 3] > .5) & (ref[..., 3] > .5)
mag = np.linalg.norm(flow, axis=-1)
valid = both & (mag < 40)
# Smooth, masked: normalized convolution so background zeros do not drag the field.
sigma = 6
wsum = ndimage.gaussian_filter(valid.astype(np.float32), sigma)
flow_s = np.stack([ndimage.gaussian_filter(flow[..., i] * valid, sigma) / np.maximum(wsum, 1e-3) for i in range(2)], -1)
print('flow done', flush=True)
Path(a.flow_cache).parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(a.flow_cache, flow=flow_s.astype(np.float32), pixels_per_unit=s, u0=u0, v0=v0)
report['flow'] = {'median_px': float(np.median(mag[valid])), 'p90_px': float(np.quantile(mag[valid], .9)), 'smoothing_sigma_px': sigma}

# 4. Visibility from front and back via z-buffers of the texel positions (body only).
mask = covered & in_regions(P.reshape(-1, 3)).reshape(size, size)
u = u0 + s * P[..., 0]; v = v0 - s * P[..., 2]
ui = np.clip(np.round(u).astype(int), 0, W - 1); vi = np.clip(np.round(v).astype(int), 0, H - 1)
sel = covered
front_z = np.full((H, W), np.inf, np.float32); back_z = np.full((H, W), -np.inf, np.float32)
np.minimum.at(front_z, (vi[sel], ui[sel]), P[..., 1][sel]); np.maximum.at(back_z, (vi[sel], ui[sel]), P[..., 1][sel])
front_z = ndimage.grey_erosion(np.where(np.isinf(front_z), 9, front_z), size=3)   # fill splat gaps
back_z = ndimage.grey_dilation(np.where(np.isinf(back_z), -9, back_z), size=3)
eps = .012
vis_front = P[..., 1] <= front_z[vi, ui] + eps
vis_back = P[..., 1] >= back_z[vi, ui] - eps
face_front = smoothstep(.15, .5, -N[..., 1]); face_back = smoothstep(.15, .5, N[..., 1])

def sample(img, uu, vv):
    """Bilinear sample an image (top row first) at float pixel coordinates."""
    return np.stack([ndimage.map_coordinates(img[..., c], [vv, uu], order=1, mode='nearest') for c in range(img.shape[-1])], -1)

idx = np.where(mask & ((vis_front & (face_front > 0)) | (vis_back & (face_back > 0))))
uu, vv = u[idx], v[idx]
fl = sample(flow_s, uu, vv)
front_px = sample(ref, uu + fl[:, 0], vv + fl[:, 1])
back_px = sample(back_ref, uu, vv)
wf = (vis_front[idx] * face_front[idx]) * front_px[:, 3]
wb = (vis_back[idx] * face_back[idx]) * back_px[:, 3]
alpha_edge = ndimage.binary_erosion(ref[..., 3] > .9, iterations=3).astype(np.float32)
wf *= sample(alpha_edge[..., None], uu + fl[:, 0], vv + fl[:, 1])[:, 0]
wb *= sample(ndimage.binary_erosion(back_ref[..., 3] > .9, iterations=3).astype(np.float32)[..., None], uu, vv)[:, 0]
# Soften the region borders in 3D so the projection fades into the generated texture.
pz = P[idx][:, 2]; px = np.abs(P[idx][:, 0])
border = np.zeros_like(pz); back_border = np.zeros_like(pz)
for r in REGIONS.values():
    lo_fade = smoothstep(0, .02, px - r['abs_x'][0]) if r['abs_x'][0] > 0 else np.ones_like(px)
    fade = np.minimum.reduce([lo_fade, smoothstep(0, .02, r['abs_x'][1] - px), smoothstep(0, .02, pz - r['z'][0]), smoothstep(0, .02, r['z'][1] - pz)])
    border = np.maximum(border, fade)
    if r['back']: back_border = np.maximum(back_border, fade)
wf *= border; wb *= back_border

def pixels(image):
    arr = np.empty(image.size[0] * image.size[1] * 4, np.float32); image.pixels.foreach_get(arr)
    return arr.reshape(image.size[1], image.size[0], 4)
color = pixels(color_node.image)
mr_small = mr_node.image; mr = pixels(mr_small)
coat_small = coat_node.image; coat = pixels(coat_small)
old = color[idx][:, :3]
# Back skirt: no source to project. Its generated albedo is clean red panels with gold edging
# (the pale look in renders is rim light on lacquer); painting borrowed front panels doubled the
# lacing and smeared a side cord across it. Keep it, only smooth TRELLIS's blotches with an
# edge-preserving filter so lacing and gold edges stay.
skirt_back = (1 - smoothstep(1.04, 1.08, pz)) * smoothstep(.56, .60, pz) * (1 - smoothstep(.25, .27, px))
wb *= 1 - skirt_back
clean = cv2.bilateralFilter(np.ascontiguousarray(color[..., :3]), 9, .12, 4)[idx]
cleanup = vis_back[idx] * face_back[idx] * skirt_back * border
back_rgb = back_px[:, :3]
# Front: keep the bright red cords and tassels; their 3D position differs from the painted ones.
ho, so, vo = rgb_to_hsv(old)
cord = (1 - smoothstep(8, 14, np.abs(((ho + 180) % 360) - 180))) * smoothstep(.65, .75, so) * smoothstep(.38, .48, vo)
wf *= 1 - cord
new_rgb = (front_px[:, :3] * wf[:, None] + back_rgb * wb[:, None]) / np.maximum(wf + wb, 1e-6)[:, None]
w = np.clip(wf + wb, 0, 1)
# The reference carries painted key light; match its mean level to the generated albedo here.
gain = np.clip(old[w > .5].mean(0) / np.maximum(new_rgb[w > .5].mean(0), 1e-4), .6, 1.2)
new_rgb = np.clip(new_rgb * gain, 0, 1)
color[idx[0], idx[1], :3] = old * (1 - w[:, None]) + new_rgb * w[:, None]
cb = np.clip(cleanup, 0, 1)[:, None]
color[idx[0], idx[1], :3] = color[idx[0], idx[1], :3] * (1 - cb) + clean * cb
report['projection'] = {'texels_front': int((wf > .5).sum()), 'texels_back': int((wb > .5).sum()), 'texels_skirt_back_cleaned': int((cleanup > .5).sum()), 'cord_texels_kept': int((cord > .5).sum()), 'skirt_back_bilateral': {'d': 9, 'sigma_color': .12, 'sigma_space': 4}, 'albedo_gain': gain.tolist(), 'visibility_eps': eps}

# 5. Re-derive metallic / roughness / coat for projected texels from the new colour.
h, sat, val = rgb_to_hsv(new_rgb)
hue_red = np.abs(((h + 180) % 360) - 180)
gold = smoothstep(24, 32, h) * (1 - smoothstep(60, 70, h)) * smoothstep(.25, .4, sat) * smoothstep(.28, .4, val)
red = (1 - smoothstep(14, 24, hue_red)) * smoothstep(.3, .45, sat) * smoothstep(.06, .12, val) * (1 - gold)
dark = (1 - smoothstep(.1, .2, val)) * (1 - red) * (1 - gold)
rest = np.clip(1 - red - gold - dark, 0, 1)
metal = gold + dark * .12 + rest * .2; rough = red * .52 + gold * .32 + dark * .6 + rest * .55
# MR / coat images may be smaller than the colour texture; write through scaled indices.
def write_scaled(img_arr, values, channels):
    sh = img_arr.shape[0]; yy = (idx[0] * sh // size); xx = (idx[1] * sh // size)
    for c, val_ in channels.items():
        cur = img_arr[yy, xx, c]; img_arr[yy, xx, c] = cur * (1 - w) + val_ * w
write_scaled(mr, None, {1: rough, 2: metal})
write_scaled(coat, None, {0: red * .1, 1: red * .1, 2: red * .1})
# Energy seams are 1-3 px slits in the reference, finer than the alignment error; they are
# built as surface strips by energy_seam_strips.py instead of painted here.
# Pass-2 sheen: the lacquer read as a pale pink wash under the studio rim light. Raise the
# roughness floor of non-metal texels everywhere and thin the coat.
nonmetal = mr[..., 2] < .3
mr[..., 1] = np.where(nonmetal, np.maximum(mr[..., 1], .52), mr[..., 1]); coat[..., :3] *= .66
report['sheen'] = {'nonmetal_roughness_floor': .52, 'coat_scale': .66}
color_node.image.pixels.foreach_set(color.ravel()); color_node.image.pack()
mr_small.pixels.foreach_set(mr.ravel()); mr_small.pack(); coat_small.pixels.foreach_set(coat.ravel()); coat_small.pack()

# 6. Export.
for o in head: o.hide_render = False
bpy.data.objects.remove(cam)
bpy.ops.object.select_all(action='DESELECT')
for o in [body] + head: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(Path(a.output_glb).resolve()), export_format='GLB', use_selection=True)
report['triangles'] = sum(len(f.vertices) - 2 for o in [body] + head for f in o.data.polygons)
report['regions'] = {k: {**v, 'abs_x': list(v['abs_x']), 'z': list(v['z'])} for k, v in REGIONS.items()}; report['seconds'] = time.monotonic() - started
(out / 'projection-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
