"""Check the saved MPFB-derived hand, provenance, deformation and grip clearance."""
from pathlib import Path
import hashlib,json,math
import bpy

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/open-hand'
source=ROOT/'assets/vendor/mpfb'
for f in json.loads((source/'provenance.json').read_text())['files']:
    assert hashlib.sha256((source/f['file']).read_bytes()).hexdigest()==f['sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/cinema/open-hand-study.blend'))
s=bpy.context.scene;rig=bpy.data.objects['Open hand rig'];hand=bpy.data.objects['MPFB right hand — CC0 anatomy base']
assert len(rig.data.bones)==22
assert sum(b.name.startswith('finger') for b in rig.data.bones)==15
errors=[abs(sum(g.weight for g in v.groups)-1) for v in hand.data.vertices]
assert max(errors)<1e-5,max(errors)
assert hand.data.uv_layers.active is not None
report={'upstream_hashes_verified':True,'scene_reopened':True,'source_asset_license':'CC0-1.0','bones':22,'finger_bones':15,'weighted_base_vertices':len(hand.data.vertices),'base_faces':len(hand.data.polygons),'maximum_weight_sum_error':max(errors),'poses':[]}
posecoords=[]
study=json.loads((OUT/'anatomy.json').read_text());sy,sz=study['shaft_yz'];slope=study['shaft_slope_y_over_x'];radius=study['shaft_radius_m']
for frame in (1,24):
    s.frame_set(frame);bpy.context.view_layer.update()
    evaluated=hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    coords=[tuple(v.co) for v in evaluated.data.vertices];posecoords.append(coords)
    assert all(math.isfinite(c) for p in coords for c in p)
    clearance=min(math.sqrt((p[1]-sy-slope*p[0])**2/(1+slope*slope)+(p[2]-sz)**2)-radius for p in coords)
    report['poses'].append({'frame':frame,'evaluated_vertices':len(coords),'minimum_vertex_shaft_clearance_m':clearance})
    if frame==24:assert clearance>=-1e-5,clearance
assert any(sum((a-b)**2 for a,b in zip(p,q))>.0001 for p,q in zip(*posecoords))
armor=[o for o in s.objects if o.get('study_component')=='open-source-hand-kote']
assert len([o for o in armor if o.name.startswith('perforated red shino splint')])==7
assert all(o.parent==rig and o.parent_type=='BONE' for o in armor)
report['bone_attached_armor_and_stitch_objects']=len(armor)
report['splints']=7;report['attachment_holes']=14
report['limitations']='Grip clearance checks evaluated vertices, not every face interior or finger-to-finger collision. Contact correction is Blender-specific and not yet baked for a game engine. Frames 1 and 24 are test poses, not an approved grasp animation.'
(OUT/'scene-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
