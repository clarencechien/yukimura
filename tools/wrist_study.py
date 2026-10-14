"""Authored palm frames and elbow poles; baked onto the existing 92-bone rig.

No wrist-angle optimiser. The source JSON defines contact orientation as well as
position. Finger FK corrections preserve joint centres and follow their parents.
"""
import sys, math, json
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from commander_hands import basis, SCALE, DATA
from samurai_rig import sample
from gltf_assets import share_images
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.tmp/wrist-v22/models'
CONFIG=ROOT/'assets/source/weapon-grips.json'

def frame(axis,normal):
    y=axis.normalized();z=normal-y*normal.dot(y)
    if z.length<1e-5:raise ValueError('Degenerate grip frame')
    z.normalize();return Matrix((y.cross(z),y,z)).transposed()

def hand_delta(rig,side,center,axis,radial):
    b=basis(1 if side=='R' else -1)
    wrist=rig.data.bones['hand.'+side].head_local
    offset=b@Vector(DATA['shaft_center'])*SCALE
    shaft=b@Vector(DATA['shaft_axis'])
    # The radial direction is authored in the torso frame, independent of elbow
    # solving; preserve the full hand frame instead of optimising a scalar angle.
    rot=frame(axis,radial)@frame(shaft,-offset).transposed()
    return Matrix.Translation(center)@rot.to_4x4()@Matrix.Translation(-wrist-offset)

def arm_matrices(rig,side,body,wrist,pole):
    a=rig.data.bones['arm.'+side];b=rig.data.bones['forearm.'+side]
    shoulder=body@a.head_local;v=wrist-shoulder;d=v.length;direction=v.normalized()
    if not abs(a.length-b.length)+.005<d<a.length+b.length-.004:
        raise ValueError(f'{side} unreachable authored wrist {d:.4f}, reach {a.length+b.length:.4f}')
    bend=pole-shoulder;bend-=direction*bend.dot(direction)
    if bend.length<.02:raise ValueError('Elbow pole singularity')
    bend.normalize();along=(a.length*a.length-b.length*b.length+d*d)/(2*d)
    elbow=shoulder+direction*along+bend*math.sqrt(max(0,a.length*a.length-along*along))
    plane=(elbow-shoulder).cross(wrist-elbow).normalized()
    rest_plane=(a.tail_local-a.head_local).cross(b.tail_local-b.head_local).normalized()
    result={}
    for bone,h,t in [(a,shoulder,elbow),(b,elbow,wrist)]:
        rot=frame(t-h,plane)@frame(bone.tail_local-bone.head_local,rest_plane).transposed()
        result[bone.name]=Matrix.Translation(h)@rot.to_4x4()@Matrix.Translation(-bone.head_local)
    return result,elbow

def finger_offsets(rig,side,settings,opposition=0):
    b=basis(1 if side=='R' else -1)
    # A reflection changes axial-vector handedness for the mirrored left hand.
    axis=b@Vector((1,0,0))*(1 if side=='R' else -1)
    result={}
    for finger in range(1,6):
        parent=Matrix.Identity(4)
        if finger==1:
            pivot=rig.data.bones[f'body.finger1-1.{side}'].head_local
            z=b@Vector((0,0,1))*(1 if side=='R' else -1)
            parent=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(opposition),4,z)@Matrix.Translation(-pivot)
        for joint,degrees in enumerate(settings[str(finger)],1):
            name=f'body.finger{finger}-{joint}.{side}'
            pivot=rig.data.bones[name].head_local
            parent=parent@Matrix.Translation(pivot)@Matrix.Rotation(math.radians(degrees),4,axis)@Matrix.Translation(-pivot)
            result[name]=parent.copy()
    return result

def run(kind,export=True):
    config=json.loads(CONFIG.read_text())[kind]
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'assets/optimized/commanders/{kind}-trial.blend'))
    scene=bpy.context.scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
    tracks={t.name:t for t in rig.animation_data.nla_tracks}
    for t in tracks.values():t.mute=True
    skin=next(m for m in mesh.modifiers if m.type=='ARMATURE');skin.show_viewport=False
    def depth(b):return 1+depth(b.parent) if b.parent else 0
    bodybones=sorted([b for b in rig.data.bones if b.name.startswith(('body.upperarm','body.lowerarm','body.wrist','body.finger','body.metacarpal'))],key=depth)
    offsets={s:finger_offsets(rig,s,config['fingers'],config.get('thumb_opposition',0)) for s in ['L','R']}
    reports=[]
    for clip in config['clips']:
        settings=config['clips'][clip]
        action=tracks[clip].strips[0].action;rig.animation_data.action=action
        first,last=map(round,action.frame_range);twist={}
        for f in range(first,last+1):
            t=(f-first)/(last-first);scene.frame_set(f);bpy.context.view_layer.update()
            body=rig.pose.bones['chest'].matrix@rest['chest'].inverted()
            grip=Vector(settings['center']);axis=Vector(settings['axis']).normalized()
            if clip=='thrust':grip.y-=sample([(0,0),(.22,-.035),(.40,.06),(.60,.06),(1,0)],t)
            center=body@grip;axis=(body.to_3x3()@axis).normalized()
            weapon=rig.data.bones['weapon'];rot=(weapon.tail_local-weapon.head_local).rotation_difference(axis)
            deltas={'weapon':Matrix.Translation(center)@rot.to_matrix().to_4x4()@Matrix.Translation(-weapon.head_local)}
            row={'frame':f,'clip':clip,'hands':{}}
            for side in ['R','L']:
                target=center+axis*(settings['spacing'] if side=='L' else 0)
                radial=body.to_3x3()@Vector(settings['radial'][side])
                hd=hand_delta(rig,side,target,axis,radial);wrist=hd@rig.data.bones['hand.'+side].head_local
                matrices,elbow=arm_matrices(rig,side,body,wrist,body@Vector(settings['pole'][side]))
                deltas.update(matrices);deltas['hand.'+side]=hd
                palm=hd.to_3x3()@basis(1 if side=='R' else -1)@Vector((0,1,0))
                row['hands'][side]={'wrist':list(wrist),'elbow':list(elbow),'contact':list(target),'palm_axis':list(palm),
                    'axis_angle_degrees':math.degrees((wrist-elbow).angle(palm))}
            for name in ['weapon','arm.R','forearm.R','hand.R','arm.L','forearm.L','hand.L']:
                rig.pose.bones[name].matrix=deltas[name]@rest[name];bpy.context.view_layer.update()
            for bone in bodybones:
                name=bone.name;side=name[-1]
                group=('arm' if name.startswith('body.upperarm') else 'forearm' if name.startswith('body.lowerarm') else 'hand')+'.'+side
                delta=deltas[group];matrix=delta@offsets[side].get(name,Matrix.Identity(4))@rest[name]
                if name.startswith('body.lowerarm'):
                    a=rig.pose.bones['forearm.'+side].head;axis2=(rig.pose.bones['hand.'+side].head-a).normalized()
                    q=(deltas['hand.'+side].to_quaternion()@delta.to_quaternion().inverted()).normalized()
                    angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis2),q.w)
                    old=twist.get(name,0);angle=old+(angle-old+math.pi)%math.tau-math.pi;twist[name]=angle
                    amount=.22 if name.startswith('body.lowerarm01') else .72
                    point=matrix.translation.copy()
                    matrix=Matrix.Translation(point)@Matrix.Rotation(angle*amount,4,axis2)@Matrix.Translation(-point)@matrix
                rig.pose.bones[name].matrix=matrix;bpy.context.view_layer.update()
            for name in list(deltas)+[b.name for b in bodybones]:
                pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
                pb.keyframe_insert('location',frame=f,group=name);pb.keyframe_insert('rotation_quaternion',frame=f,group=name)
            reports.append(row)
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
        print(kind,clip,'authored palm/pole and finger FK baked',flush=True)
    rig.animation_data.action=None;skin.show_viewport=True
    for pb in rig.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
    # The parameter block is stored with the editable scene as well as in Git.
    block=bpy.data.texts.get('Weapon grip controls.json') or bpy.data.texts.new('Weapon grip controls.json')
    block.clear();block.write(json.dumps(config,indent=2))
    bpy.context.preferences.filepaths.save_version=0
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT.parent/f'{kind}-pose-check.json').write_text(json.dumps(reports,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'assets/optimized/commanders/{kind}-grip-study.blend'),compress=True)
    if export:
        bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True)
        target=OUT/f'{kind}.glb'
        bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,
            export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,
            export_vertex_color='ACTIVE',export_all_vertex_colors=False)
        share_images(target)

if __name__=='__main__':
    args=[a for a in sys.argv[1:] if a in ['yukimura','ieyasu']]
    for kind in args or ['yukimura','ieyasu']:run(kind)
