"""Build the reference's glowing energy slits as thin emissive strips on the body surface.

Each slit centre line (find_energy_seams.py, reference pixels) is mapped onto the model:
reference pixel -> render pixel by inverting the projection's optical flow (fixed point),
render pixel -> (x, z) by the silhouette fit, then a ray from the front finds the body
surface. A slightly domed strip sits 1.5 mm proud of the surface and glows orange.
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np
from scipy import ndimage
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--seams', default='docs/experiments/future-sanada/body-v2/pass3/energy-seams.json')
p.add_argument('--flow-cache', default='.tmp/v3/flow.npz')
p.add_argument('--output', required=True)
p.add_argument('--samples', type=int, default=12)
a = p.parse_args()
seams = json.loads(Path(a.seams).read_text())['seams']
cache = np.load(a.flow_cache); flow = cache['flow']; s, u0, v0 = float(cache['pixels_per_unit']), float(cache['u0']), float(cache['v0'])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
bm = bmesh.new(); bm.from_mesh(body.data); tree = BVHTree.FromBMesh(bm); bm.free()

def flow_at(q):
    return np.array([ndimage.map_coordinates(flow[..., c], [[q[1]], [q[0]]], order=1, mode='nearest')[0] for c in range(2)])

def to_surface(ref_px):
    q = np.array(ref_px, float)
    for _ in range(8): q = np.array(ref_px) - flow_at(q)            # q + flow(q) = reference pixel
    x, z = (q[0] - u0) / s, (v0 - q[1]) / s
    hit = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 2.0)
    if hit[0] is None: return None, None
    n = np.array(hit[1]); n = -n if n[1] > 0 else n                    # face the front ray (-Y)
    return np.array(hit[0]), n

mat = bpy.data.materials.new('Energy seam / orange glow'); mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (1, .45, .1, 1); bsdf.inputs['Roughness'].default_value = .3
bsdf.inputs['Emission Color'].default_value = (1, .3, .04, 1); bsdf.inputs['Emission Strength'].default_value = 6
slot_mat = bpy.data.materials.new('Energy seam slot / dark recess'); slot_mat.use_nodes = True
sb = slot_mat.node_tree.nodes['Principled BSDF']; sb.inputs['Base Color'].default_value = (.018, .016, .016, 1); sb.inputs['Roughness'].default_value = .55; sb.inputs['Metallic'].default_value = .3

report = []
for seam in seams:
    p0, p1 = np.array(seam['p0']), np.array(seam['p1'])
    pts, nrms = [], []
    for t in np.linspace(0, 1, a.samples):
        P, N = to_surface(p0 + (p1 - p0) * t)
        if P is not None: pts.append(P); nrms.append(N)
    if len(pts) < 3: report.append({'name': seam['name'], 'status': 'no surface hit'}); continue
    pts, nrms = np.array(pts), np.array(nrms)
    # Rays can land on a neighbouring plate: drop samples far from the median depth.
    keep = np.abs(pts[:, 1] - np.median(pts[:, 1])) < .02
    pts, nrms = pts[keep], nrms[keep]
    pts = ndimage.uniform_filter1d(pts, 3, axis=0, mode='nearest')
    width = max(seam['width_px'], 3.0) * .8 / s
    def strip(name, w, lift, dome, material):
        """Domed strip along the surface; the reference slits sit in a dark rounded slot."""
        mesh = bpy.data.meshes.new(name); bm = bmesh.new(); rows = []
        for i, (P, N) in enumerate(zip(pts, nrms)):
            T = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; T /= max(np.linalg.norm(T), 1e-9)
            side = np.cross(N, T); side /= max(np.linalg.norm(side), 1e-9)
            taper = 1 if 0 < i < len(pts) - 1 else .5                   # rounded ends
            rows.append([bm.verts.new(Vector(P + N * (lift + dome * np.cos(k * np.pi / 4)) + side * w / 2 * taper * np.sin(k * np.pi / 4)))
                         for k in range(-2, 3)])
        for r0, r1 in zip(rows[:-1], rows[1:]):
            for k in range(4): bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
        bm.normal_update()
        if np.mean([f.normal.dot(Vector(nrms[0])) for f in bm.faces]) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        bm.to_mesh(mesh); bm.free()
        for poly in mesh.polygons: poly.use_smooth = True
        mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    strip(f'Energy seam slot / {seam["name"]}', width * 2.6, .0018, .0002, slot_mat)
    strip(f'Energy seam / {seam["name"]}', width, .0024, .0008, mat)
    length = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
    report.append({'name': seam['name'], 'samples_kept': int(keep.sum()), 'length': length, 'width': width,
                   'centre': pts.mean(0).round(4).tolist(), 'status': 'built'})

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)
Path(a.output).with_name('energy-seam-report.json').write_text(json.dumps({'seams': report, 'emission_strength': 6, 'slot_width_factor': 2.6, 'slot_lift': .0018, 'strip_lift': .0024}, indent=2) + '\n')
for r in report: print(r)
