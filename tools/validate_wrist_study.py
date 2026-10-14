"""Validate evaluated finger skin against a nominal 19.8 mm shaft radius.

This point-sampled check does not claim complete triangle/armor collision tests
or anatomical correctness. Images and animation remain part of the review.
"""
import bpy,sys,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from samurai_rig import point,weapon_point
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.tmp/wrist-v22'
report={'shaft_radius_m':.0198,'allowed_surface_compression_m':.002,'sampled_frames_per_clip':11,
        'scope':'finger vertices with >60% weight in that digit, cylinder proxy; not full triangle or armor collision',
        'models':{},'passed':False}
for kind in ['yukimura','ieyasu']:
    versions={}
    for version,suffix in [('before','trial'),('after','grip-study'),('exported','grip-study')]:
        source=ROOT/f'assets/optimized/commanders/{kind}-{suffix}.blend'
        bpy.ops.wm.open_mainfile(filepath=str(source))
        if version=='exported':
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.context.scene.render.fps=90
            bpy.ops.import_scene.gltf(filepath=str(OUT/f'models/{kind}.glb'))
        scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
        mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig and any('deerskin' in m.name for m in o.data.materials))
        names={g.index:g.name for g in mesh.vertex_groups};digits={}
        for side in ['L','R']:
            for finger in range(1,6):
                ids=[v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith(f'body.finger{finger}-') and names[g.group].endswith('.'+side))>.6]
                assert len(ids)>300
                digits[f'{side}{finger}']=ids
        origin=point(.47,-.16,.91);axis=(weapon_point(Vector((.47,-.16,1.91)))-origin).normalized()
        rest=rig.data.bones['weapon'].matrix_local.copy();clips={}
        for track in rig.animation_data.nla_tracks:track.mute=True
        for clip in ['idle','thrust']:
            action=next(t for t in rig.animation_data.nla_tracks if t.name==clip).strips[0].action;rig.animation_data.action=action
            first,last=action.frame_range;values={key:[] for key in digits}
            for fraction in np.linspace(0,1,11):
                frame=first+(last-first)*float(fraction);scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
                deps=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(deps)
                assert len(ev.data.vertices)==len(mesh.data.vertices)
                delta=rig.pose.bones['weapon'].matrix@rest.inverted()
                o=np.array(delta@origin);a=np.array(delta.to_3x3()@axis);a/=np.linalg.norm(a)
                for key,ids in digits.items():
                    v=np.array([ev.data.vertices[i].co for i in ids])-o
                    v-=np.outer(v@a,a);r=np.linalg.norm(v,axis=1)
                    assert np.isfinite(r).all()
                    values[key].append({'min_radius_m':float(min(r)),'q05_radius_m':float(np.quantile(r,.05)),'max_compression_m':float(max(0,.0198-min(r)))})
            clips[clip]={key:{'vertices':len(digits[key]),'min_radius_m':min(x['min_radius_m'] for x in rows),
                'max_q05_radius_m':max(x['q05_radius_m'] for x in rows),
                'max_compression_m':max(x['max_compression_m'] for x in rows)} for key,rows in values.items()}
        versions[version]={'blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'clips':clips}
    for clip,digits in versions['exported']['clips'].items():
        for key,data in digits.items():
            assert data['max_compression_m']<.002,(kind,clip,key,data)
            if key.endswith('1'):assert data['max_q05_radius_m']<.025,(kind,clip,key,data)
    model=OUT/f'models/{kind}.glb';versions['glb_sha256']=hashlib.sha256(model.read_bytes()).hexdigest()
    versions['grip_check']=json.loads((OUT/f'grip-check/{kind}.json').read_text())
    report['models'][kind]=versions
    print(kind,'finger clearance and thumb approach passed',flush=True)
report['passed']=True
report['config_sha256']=hashlib.sha256((ROOT/'assets/source/weapon-grips.json').read_bytes()).hexdigest()
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
