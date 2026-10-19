"""Body v2: 1536 TRELLIS.2 body + lacquer/gilding material split + finished head study.

Run with Blender 4.3 bpy (render env). Original generated GLBs stay untouched.
  python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-1615/body-high.glb
"""
from pathlib import Path
import argparse, json, sys, time
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from trellis_body_materials import correct

p = argparse.ArgumentParser()
p.add_argument('--body', required=True)
p.add_argument('--head', default='docs/experiments/future-sanada/head-study/refined/head-preview.glb')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/refined')
p.add_argument('--head-fit', default='docs/experiments/future-sanada/body-v2/head-fit.json', help='Head scale/translation in normalized body space')
p.add_argument('--no-head', action='store_true', help='Material pass only; keep the generated head')
p.add_argument('--min-island', type=int, default=0, help='Drop disconnected fragments smaller than this many faces (0 = off; TRELLIS shells have cracks, so real plates split into islands)')
a = p.parse_args()
out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
started = time.monotonic()
bpy.ops.wm.read_factory_settings(use_empty=True)

def import_glb(path):
    """Import a GLB, bake world transforms into mesh data and drop empties."""
    before = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.gltf(filepath=str(Path(path).resolve()))
    new = [o for o in bpy.data.objects if o.name not in before]
    for o in new:
        if o.type == 'MESH':
            world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    return [o for o in bpy.data.objects if o.name not in before]

body = import_glb(a.body)
assert len(body) == 1, f'expected one generated body mesh, got {len(body)}'
body = body[0]; body.name = 'Generated body v2 / corrected lacquer'
points = np.array([v.co for v in body.data.vertices])
low, high = points.min(0), points.max(0)
normal = Matrix.Scale(2 / (high[2] - low[2]), 4) @ Matrix.Translation((-(high[0] + low[0]) / 2, -(high[1] + low[1]) / 2, -low[2]))
body.data.transform(normal)
report = {'body_source': a.body, 'normalization': {'scale': 2 / float(high[2] - low[2]), 'original_low': low.tolist(), 'original_high': high.tolist()}}

# Geometry cleanup: degenerate faces and tiny floating fragments only; no smoothing of the shell.
bm = bmesh.new(); bm.from_mesh(body.data)
before_faces = len(bm.faces)
# glTF import splits vertices along UV seams; weld them (UVs live on loops) before testing connectivity.
welded = bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges[:])
bm.faces.ensure_lookup_table()
seen = set(); dropped = 0; islands = 0
for f in (bm.faces if a.min_island else []):
    if f.index in seen: continue
    stack = [f]; group = []; seen.add(f.index)
    while stack:
        g = stack.pop(); group.append(g)
        for e in g.edges:
            for n in e.link_faces:
                if n.index not in seen: seen.add(n.index); stack.append(n)
    islands += 1
    if len(group) < a.min_island:
        dropped += len(group)
        bmesh.ops.delete(bm, geom=group, context='FACES_ONLY')
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(body.data); bm.free()
report['cleanup'] = {'faces_before': before_faces, 'islands': islands, 'fragment_faces_removed': dropped, 'faces_after': len(body.data.polygons)}

# Material split on the generated textures.
material = body.data.materials[0]; nodes = material.node_tree.nodes; links = material.node_tree.links
bsdf = nodes['Principled BSDF']
color_node = bsdf.inputs['Base Color'].links[0].from_node
mr_node = next(n for n in nodes if n.type == 'TEX_IMAGE' and n.name != color_node.name)  # bpy wrappers are not identity-stable
def pixels(image):
    arr = np.empty(image.size[0] * image.size[1] * 4, np.float32); image.pixels.foreach_get(arr)
    return arr.reshape(image.size[1], image.size[0], 4)
def new_image(name, arr, colorspace):
    im = bpy.data.images.new(name, arr.shape[1], arr.shape[0], alpha=True)
    im.colorspace_settings.name = colorspace; im.pixels.foreach_set(arr.astype(np.float32).ravel()); im.pack(); return im
color, mr, coat, stats = correct(pixels(color_node.image), pixels(mr_node.image))
color_node.image = new_image('Body v2 corrected base color', color, 'sRGB')
mr_node.image = new_image('Body v2 lacquer-aware metallic roughness', mr, 'Non-Color'); mr_node.image.scale(2048, 2048); mr_node.image.pack()  # low-frequency; keeps the GLB under GitHub's 100 MB
coat_node = nodes.new('ShaderNodeTexImage'); coat_node.image = new_image('Body v2 lacquer coat', coat, 'Non-Color'); coat_node.image.scale(1024, 1024); coat_node.image.pack()
uv_source = color_node.inputs['Vector'].links[0].from_node if color_node.inputs['Vector'].links else None
if uv_source: links.new(uv_source.outputs[0], coat_node.inputs['Vector'])
coat_split = nodes.new('ShaderNodeSeparateColor'); links.new(coat_node.outputs['Color'], coat_split.inputs['Color'])
links.new(coat_split.outputs['Red'], bsdf.inputs['Coat Weight']); bsdf.inputs['Coat Roughness'].default_value = .2
material.name = 'Body v2 lacquer / gilding / under-armour'
report['materials'] = stats

head_objects = []
if not a.no_head:
    fit = json.loads(Path(a.head_fit).read_text())
    head_objects = import_glb(a.head)
    place = Matrix.Translation(fit['translation']) @ Matrix.Scale(fit['scale'], 4)
    for o in head_objects: o.data.transform(place)
    # Remove the generated head by region + proximity, not a box, so collar and shoulder tops survive:
    # everything in the antler band, the helmet/face core, and body skin coincident with the new head.
    from scipy.spatial import cKDTree
    head_pts = np.concatenate([np.array([v.co for v in o.data.vertices]) for o in head_objects])
    tree = cKDTree(head_pts)
    cut = fit['remove_rules']
    bm = bmesh.new(); bm.from_mesh(body.data)
    candidates = [v for v in bm.verts if v.co.z > cut['near_head_z_min']]
    dist, _ = tree.query(np.array([v.co for v in candidates]))
    old = [v for v, d in zip(candidates, dist)
           if v.co.z > cut['antler_band_z_min']
           or (v.co.z > cut['core_z_min'] and abs(v.co.x) < cut['core_abs_x_max'])
           or d < cut['near_head_distance']]
    bmesh.ops.delete(bm, geom=old, context='VERTS'); bm.to_mesh(body.data); bm.free()
    report['removed_generated_head_vertices'] = len(old); report['head_removal_rules'] = cut
    report['head'] = {'source': a.head, 'scale': fit['scale'], 'translation': fit['translation'], 'meshes': len(head_objects)}

for poly in body.data.polygons: poly.use_smooth = True
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
report['triangles'] = sum(len(f.vertices) - 2 for o in meshes for f in o.data.polygons)
report['meshes'] = len(meshes)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str((out / 'body-v2.glb').resolve()), export_format='GLB', use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out / 'body-v2.blend').resolve()), compress=True)
report['seconds'] = time.monotonic() - started
(out / 'refinement-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
