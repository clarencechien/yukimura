"""Sample every authored commander clip on the actual Blender deform mesh."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
results=[]
sculpt='--sculpt' in sys.argv
visor='--visor' in sys.argv or sculpt
menpo=visor or '--menpo' in sys.argv
for kind in ['yukimura','ieyasu']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-{"sculpt" if sculpt else "visor" if visor else "menpo" if menpo else "face"}.blend'))
    scene=bpy.context.scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    mat=next(i for i,m in enumerate(mesh.data.materials) if m.name.startswith('human skin /'))
    ids={i for p in mesh.data.polygons if p.material_index==mat for i in p.vertices}
    skull=[i for i in ids if mesh.data.vertices[i].co.z>1.82]
    mask=json.loads(mesh['menpo']) if menpo else None
    shell=list(range(mask['first_vertex'],mask['first_vertex']+mask['shell_vertices'])) if menpo else []
    mask_ids=list(range(mask['first_vertex'],len(mesh.data.vertices))) if menpo else []
    skin_polys=[list(p.vertices) for p in mesh.data.polygons if p.material_index==mat]
    rest=rig.data.bones['body.head'].matrix_local.copy()
    tracks=list(rig.animation_data.nla_tracks)
    for track in tracks:track.mute=True
    for track in tracks:
        action=track.strips[0].action;rig.animation_data.action=action
        start,end=action.frame_range
        worst=0;clearance=1
        for sample in range(13):
            frame=start+(end-start)*sample/12
            scene.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
            evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
            delta=rig.pose.bones['body.head'].matrix@rest.inverted()
            for i in ids:
                assert all(math.isfinite(c) for c in evaluated.data.vertices[i].co)
            # A separate/detached head rig or wrong inverse bind matrix fails this
            # measurement even when the imported model looks fine in its rest pose.
            error=max((evaluated.data.vertices[i].co-delta@mesh.data.vertices[i].co).length for i in skull+mask_ids)
            worst=max(worst,error)
            assert error<.0001, f'{kind}/{track.name}: head drift {error} m'
            if menpo:
                tree=BVHTree.FromPolygons([v.co for v in evaluated.data.vertices],skin_polys)
                for i in shell:
                    p=evaluated.data.vertices[i].co
                    hit,normal,_,distance=tree.find_nearest(p)
                    signed=distance if (p-hit).dot(normal)>=0 else -distance
                    clearance=min(clearance,signed)
        results.append({'kind':kind,'clip':track.name,'samples':13,'head_vertices':len(ids),
                        'rigid_cranium_vertices':len(skull),'max_helmet_bone_drift_m':worst})
        if menpo:
            results[-1].update({'mask_vertices':len(mask_ids),'minimum_skin_clearance_m':clearance})
            assert clearance>.0001, f'{kind}/{track.name}: mask intersects skin ({clearance} m)'
    rig.animation_data.action=None
out=ROOT/('renders/menpo-v20' if sculpt else 'renders/menpo-v19' if visor else 'renders/menpo-v18' if menpo else 'renders/face-v17');out.mkdir(parents=True,exist_ok=True)
(out/'motion-check.json').write_text(json.dumps({'results':results,'passed':True},indent=2)+'\n')
print('Validated',len(results),'clips /',len(results)*13,'poses',flush=True)
