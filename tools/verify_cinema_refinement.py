"""Reopen and check the saved derivative with the pinned Blender Python runtime."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent.parent
path=ROOT/'assets/cinema/first-person-refined.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
s=bpy.context.scene
assert (s.render.resolution_x,s.render.resolution_y)==(3840,2160)
assert s.render.image_settings.color_depth=='16'
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
assert not missing,missing
troops=[o for o in s.objects if o.name.startswith('Tokugawa formation')]
assert len({o.data.name for o in troops})==4
poses=[]
for frame in (1,120,240):
    s.frame_set(frame)
    joints=[]
    for side in ('L','R'):
        grip=bpy.data.objects['II articulated grip '+side]
        fore=bpy.data.objects['II proportioned kote '+side]
        wrist=grip.matrix_world@Vector((0,0,.105))
        foretip=fore.matrix_world@Vector((0,0,.34))
        error=(wrist-foretip).length
        assert error<.00001,(frame,side,error)
        length=(foretip-fore.matrix_world.translation).length
        assert abs(length-.34)<.00001
        hand=bpy.data.objects['II anatomically separated glove '+side]
        assert hand.parent==grip
        joints.append({'side':side,'wrist_gap_m':error,'forearm_length_m':length})
    poses.append({'frame':frame,'camera':list(s.camera.location),'joints':joints})
assert len({tuple(p['camera']) for p in poses})==3
report={'scene_reopened':True,'resolution':[3840,2160],'bits_per_channel':16,'missing_external_images':missing,
        'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'troops':len(troops),'shared_troop_pose_meshes':4,
        'poses':poses,'note':'Checks connectivity and saved scene integrity; visual anatomy still requires artistic review.'}
(ROOT/'renders/first-person-refined/scene-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
