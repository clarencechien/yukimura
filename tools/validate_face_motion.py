"""Sample every authored commander clip on the actual Blender deform mesh."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
results=[]
for kind in ['yukimura','ieyasu']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-face.blend'))
    scene=bpy.context.scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    mat=next(i for i,m in enumerate(mesh.data.materials) if m.name.startswith('human skin /'))
    ids={i for p in mesh.data.polygons if p.material_index==mat for i in p.vertices}
    skull=[i for i in ids if mesh.data.vertices[i].co.z>1.82]
    rest=rig.data.bones['body.head'].matrix_local.copy()
    tracks=list(rig.animation_data.nla_tracks)
    for track in tracks:track.mute=True
    for track in tracks:
        action=track.strips[0].action;rig.animation_data.action=action
        start,end=action.frame_range
        worst=0
        for sample in range(13):
            frame=start+(end-start)*sample/12
            scene.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
            evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
            delta=rig.pose.bones['body.head'].matrix@rest.inverted()
            for i in ids:
                assert all(math.isfinite(c) for c in evaluated.data.vertices[i].co)
            # A separate/detached head rig or wrong inverse bind matrix fails this
            # measurement even when the imported model looks fine in its rest pose.
            error=max((evaluated.data.vertices[i].co-delta@mesh.data.vertices[i].co).length for i in skull)
            worst=max(worst,error)
            assert error<.0001, f'{kind}/{track.name}: head drift {error} m'
        results.append({'kind':kind,'clip':track.name,'samples':13,'head_vertices':len(ids),
                        'rigid_cranium_vertices':len(skull),'max_helmet_bone_drift_m':worst})
    rig.animation_data.action=None
out=ROOT/'renders/face-v17';out.mkdir(parents=True,exist_ok=True)
(out/'motion-check.json').write_text(json.dumps({'results':results,'passed':True},indent=2)+'\n')
print('Validated',len(results),'clips /',len(results)*13,'poses',flush=True)
