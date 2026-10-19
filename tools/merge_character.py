"""Join body v2 into one character object and audit the head/body seam for see-through gaps.

The helmet (head study) and the regenerated body are separate rigid shells. For armour a
literal vertex weld between unrelated meshes is not meaningful (the helmet will ride one head
bone); what matters is that no gap at the junction lets the eye see through, and that the
character ships as one object. The audit fires rays from all around and above at points
inside the neck and the collar line and counts rays that hit nothing before reaching them.
"""
from pathlib import Path
import argparse, json
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--output', required=True)
p.add_argument('--rays', type=int, default=3000)
a = p.parse_args()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH':
        world = o.matrix_world.copy(); o.parent = None; o.matrix_world = Matrix.Identity(4); o.data.transform(world)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
objs = list(bpy.context.scene.objects)
parts = {o.name: len(o.data.polygons) for o in objs}

# Seam audit: targets inside the neck / behind the collar line, rays from a sphere of
# directions (upper hemisphere and horizon; from below is inside the torso).
bm = bmesh.new()
for o in objs: bm.from_mesh(o.data)
tree = BVHTree.FromBMesh(bm); bm.free()
rng = np.random.default_rng(1615)
def audit(targets, label):
    leaks = []
    for i in range(a.rays):
        d = rng.normal(size=3); d[2] = abs(d[2]) * .6 - .1; d /= np.linalg.norm(d)   # mostly horizontal / from above
        t = targets[rng.integers(len(targets))]
        origin = Vector(t + d * 1.5)
        hit = tree.ray_cast(origin, Vector(-d), 1.5 - 1e-4)
        if hit[0] is None:
            # Reaching the target unobstructed can be a natural opening (under the shikoro flare).
            # A defect is seeing through: the same line continued past the target hits nothing.
            through = tree.ray_cast(Vector(t), Vector(-d), 1.5)[0] is None
            leaks.append({'target': np.round(t, 4).tolist(), 'from': np.round(d, 3).tolist(), 'see_through_to_background': through})
    return {'label': label, 'rays': a.rays, 'reached_unobstructed': len(leaks),
            'see_through_to_background': sum(l['see_through_to_background'] for l in leaks), 'examples': leaks[:20]}
neck = np.array([[r * np.cos(t), .026 + r * np.sin(t), z] for t in np.linspace(0, 2 * np.pi, 24, endpoint=False) for r in (0, .03) for z in np.linspace(1.42, 1.56, 8)])
# Collar targets must be inside the torso: midpoint between the front and back surfaces.
collar = []
for x in np.linspace(-.16, .16, 17):
    for z in np.linspace(1.40, 1.50, 6):
        f = tree.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2); b = tree.ray_cast(Vector((x, 1, z)), Vector((0, -1, 0)), 2)
        if f[0] is not None and b[0] is not None and b[0].y - f[0].y > .05: collar.append([x, (f[0].y + b[0].y) / 2, z])
collar = np.array(collar)
audits = [audit(neck, 'neck interior (head/body junction)'), audit(collar, 'inside the torso along the collar line')]

# Join everything into one object (material slots preserved).
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
body = next(o for o in objs if o.data.materials and o.data.materials[0].name.startswith('Body v2'))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = 'Sanada / future akazonae (body v2, joined)'
bpy.ops.export_scene.gltf(filepath=str(Path(a.output).resolve()), export_format='GLB', use_selection=True)   # tangents omitted: glTF clients derive MikkTSpace (keeps the file < 100 MB)
report = {'parts_joined': len(parts), 'part_faces': parts, 'materials': len(body.data.materials),
          'triangles': sum(len(f.vertices) - 2 for f in body.data.polygons), 'seam_audit': audits,
          'note': 'Rigid shells joined into one object; the helmet is not vertex-welded to the body, by design.'}
Path(a.output).with_name('merge-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'part_faces'}))
