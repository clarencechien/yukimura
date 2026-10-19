"""Lighter inspection GLB for the offline viewer; the full refined GLB stays the edit base."""
from pathlib import Path
import argparse, json
import bpy

p = argparse.ArgumentParser()
p.add_argument('--directory', default='docs/experiments/future-sanada/body-v2/refined')
p.add_argument('--ratio', type=float, default=.45)
p.add_argument('--model', help='Start from a GLB instead of body-v2.blend (e.g. the pass-2 model)')
p.add_argument('--name', default='body-v2-preview')
p.add_argument('--join', action='store_true', help='Join all parts into one object after decimating the body only')
a = p.parse_args()
out = Path(a.directory)
if a.model:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(Path(a.model).resolve()))
else:
    bpy.ops.wm.open_mainfile(filepath=str((out / 'body-v2.blend').resolve()))
body = bpy.data.objects['Generated body v2 / corrected lacquer']
bpy.context.view_layer.objects.active = body
modifier = body.modifiers.new('Inspection body simplification', 'DECIMATE'); modifier.ratio = a.ratio
bpy.ops.object.modifier_apply(modifier=modifier.name)
for image in bpy.data.images:
    if image.type == 'IMAGE' and max(image.size) > 2048: image.scale(2048, 2048); image.pack()
bpy.ops.object.select_all(action='SELECT')
if a.join:                                                             # same single-object layout as merge_character.py
    bpy.context.view_layer.objects.active = body; bpy.ops.object.join(); body.name = 'Sanada / future akazonae (body v2, joined)'
bpy.ops.export_scene.gltf(filepath=str((out / f'{a.name}.glb').resolve()), export_format='GLB', use_selection=True, export_tangents=True)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
report = {'decimate_ratio': a.ratio, 'joined': a.join, 'body_triangles': None if a.join else sum(len(f.vertices) - 2 for f in body.data.polygons),
          'total_triangles': sum(len(f.vertices) - 2 for o in meshes for f in o.data.polygons), 'meshes': len(meshes),
          'max_texture': 2048, 'bytes': (out / f'{a.name}.glb').stat().st_size}
(out / f'{a.name}-report.json' if a.model else out / 'preview-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
