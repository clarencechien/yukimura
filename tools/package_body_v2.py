"""Lighter inspection GLB for the offline viewer; the full refined GLB stays the edit base."""
from pathlib import Path
import argparse, json
import bpy

p = argparse.ArgumentParser()
p.add_argument('--directory', default='docs/experiments/future-sanada/body-v2/refined')
p.add_argument('--ratio', type=float, default=.45)
a = p.parse_args()
out = Path(a.directory)
bpy.ops.wm.open_mainfile(filepath=str((out / 'body-v2.blend').resolve()))
body = bpy.data.objects['Generated body v2 / corrected lacquer']
bpy.context.view_layer.objects.active = body
modifier = body.modifiers.new('Inspection body simplification', 'DECIMATE'); modifier.ratio = a.ratio
bpy.ops.object.modifier_apply(modifier=modifier.name)
for image in bpy.data.images:
    if image.type == 'IMAGE' and max(image.size) > 2048: image.scale(2048, 2048); image.pack()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str((out / 'body-v2-preview.glb').resolve()), export_format='GLB', use_selection=True)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
report = {'decimate_ratio': a.ratio, 'body_triangles': sum(len(f.vertices) - 2 for f in body.data.polygons),
          'total_triangles': sum(len(f.vertices) - 2 for o in meshes for f in o.data.polygons), 'meshes': len(meshes),
          'max_texture': 2048, 'bytes': (out / 'body-v2-preview.glb').stat().st_size}
(out / 'preview-report.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
