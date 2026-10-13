"""Prepare a compact CC0 anatomical grip from the editable open-hand study."""
from pathlib import Path
import bpy,bmesh,json,hashlib
ROOT=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/cinema/open-hand-study.blend'))
bpy.context.scene.frame_set(24)
o=bpy.data.objects['MPFB right hand — CC0 anatomy base'];o.modifiers['anatomical surface smoothing'].levels=1
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
m=bpy.data.meshes.new_from_object(o.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,-.012,0),plane_no=(0,1,0),clear_inner=True);bm.to_mesh(m);bm.free()
obj=bpy.data.objects.new('compact continuous glove',m);bpy.context.scene.collection.objects.link(obj)
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
mod=obj.modifiers.new('whole-character hand budget','DECIMATE');mod.ratio=.12;bpy.ops.object.modifier_apply(modifier=mod.name)
obj.data.calc_loop_triangles()
a=json.loads((ROOT/'renders/open-hand/anatomy.json').read_text())
report={'anatomy_license':'CC0-1.0','plate_provenance':'Original procedural armor from tools/open_hand_armor.py; not part of the MPFB source assets','upstream':'https://github.com/makehumancommunity/mpfb2','commit':json.loads((ROOT/'assets/vendor/mpfb/provenance.json').read_text())['commit'],'source_blend_sha256':hashlib.sha256((ROOT/'assets/cinema/open-hand-study.blend').read_bytes()).hexdigest(),'shaft_center':[0,*a['shaft_yz']],'shaft_axis':[1,a['shaft_slope_y_over_x'],0],'shaft_radius':a['shaft_radius_m'],'vertices':[list(v.co) for v in obj.data.vertices],'faces':[list(p.vertices) for p in obj.data.polygons],'triangles':len(obj.data.loop_triangles)}
plate=bpy.data.objects['fitted crimson tekko'];ep=plate.evaluated_get(deps);pm=ep.to_mesh()
report['plate']={'vertices':[list(plate.matrix_world@v.co) for v in pm.vertices],'faces':[list(p.vertices) for p in pm.polygons]};ep.to_mesh_clear()
(ROOT/'assets/vendor/mpfb/commander-grip.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print('Compact hand triangles',report['triangles'])
