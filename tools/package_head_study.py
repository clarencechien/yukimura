"""Build a smaller inspection head and a static body fitting, never a game replacement."""
from pathlib import Path
import json
import bpy,bmesh
from mathutils import Matrix,Vector

root=Path('docs/experiments/future-sanada');out=root/'head-study'
bpy.ops.wm.open_mainfile(filepath=str((out/'refined/head-refined.blend').resolve()))
base=bpy.data.objects['Generated shell with local corrections']
bpy.context.view_layer.objects.active=base
modifier=base.modifiers.new('Inspection shell simplification','DECIMATE');modifier.ratio=.30
bpy.ops.object.modifier_apply(modifier=modifier.name)
for image in bpy.data.images:
 if image.type=='IMAGE' and max(image.size)>2048:image.scale(2048,2048);image.pack()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str((out/'refined/head-preview.glb').resolve()),export_format='GLB',use_selection=True)
head_triangles=sum(len(f.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for f in o.data.polygons)

# Separate static fit. Original body file remains untouched.
head=list(bpy.context.scene.objects)
for o in head:
 if o.type=='MESH':o.data.transform(Matrix.Translation((0,-.005,1.44))@Matrix.Scale(.26,4))
bpy.ops.import_scene.gltf(filepath=str((root/'future-sanada.glb').resolve()))
body=[o for o in bpy.context.scene.objects if o not in head and o.type=='MESH']
points=[o.matrix_world@Vector(c) for o in body for c in o.bound_box]
lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
normal=Matrix.Scale(2/(hi.z-lo.z),4)@Matrix.Translation((-(hi.x+lo.x)/2,-(hi.y+lo.y)/2,-lo.z))
removed=0
for o in body:
 transform=normal@o.matrix_world;o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(transform)
 bm=bmesh.new();bm.from_mesh(o.data)
 old_head=[v for v in bm.verts if v.co.z>1.56 and abs(v.co.x)<.235]
 removed+=len(old_head);bmesh.ops.delete(bm,geom=old_head,context='VERTS');bm.to_mesh(o.data);bm.free()
 o.name='Body with old head region removed'
fit=out/'fitting';fit.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in head+body:
 if o.type=='MESH':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str((fit/'static-fit.glb').resolve()),export_format='GLB',use_selection=True)
report={'head_preview_triangles':head_triangles,'head_scale':.26,'head_translation':[0,-.005,1.44],'body_normalized_height_before_fit':2,'removed_old_head_vertices':removed,'limitations':['Static overlapping assembly, not welded or skinned','No neck deformation or shoulder collision certification','Body materials and anatomy still need refinement','Inspection preview is not a validated mobile LOD']}
(fit/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
