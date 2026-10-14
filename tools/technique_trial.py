"""Offline grip-pose study on the existing commander deformation skeleton."""
import bpy
import math
from mathutils import Vector, Matrix
from samurai_rig import bind_hero


def apply_technique(rig, mesh, kind):
    clips=['idle','run'] if kind=='yukimura' else ['thrust']
    data=bpy.data.meshes.new('temporary control solver')
    data.from_pydata([(0,0,0),(.01,0,0),(0,.01,0)],[],[(0,1,2)])
    dummy=bpy.data.objects.new('temporary control solver',data)
    bpy.context.scene.collection.objects.link(dummy)
    solver=bind_hero(dummy,kind,reweight=False,natural_wrists=True,
                     technique_trial=True,clip_filter=clips)
    controls=['weapon']+[n+'.'+side for side in ['L','R'] for n in ['arm','forearm','hand']]
    rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
    for name in controls:
        assert max(abs(v) for row in solver.data.bones[name].matrix_local-rest[name] for v in row)<.00001
    tracks={t.name:t for t in rig.animation_data.nla_tracks}
    for t in rig.animation_data.nla_tracks:t.mute=True
    def depth(b):return 1+depth(b.parent) if b.parent else 0
    body=sorted([b for b in rig.data.bones if b.name.startswith(('body.upperarm','body.lowerarm','body.wrist','body.finger','body.metacarpal'))],key=depth)
    mod=next(m for m in mesh.modifiers if m.type=='ARMATURE');mod.show_viewport=False
    report=[]
    for track in solver.animation_data.nla_tracks:
        clip=track.name;source=track.strips[0].action;action=tracks[clip].strips[0].action
        solver.animation_data.action=source;rig.animation_data.action=action
        first,last=map(round,action.frame_range)
        assert list(source.frame_range)==list(action.frame_range)
        twist_angles={}
        for frame in range(first,last+1):
            bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
            deltas={n:solver.pose.bones[n].matrix@rest[n].inverted() for n in controls}
            for n in controls:
                rig.pose.bones[n].matrix=solver.pose.bones[n].matrix.copy()
                bpy.context.view_layer.update()
            for bone in body:
                name=bone.name;side=name[-1]
                group=('arm' if name.startswith('body.upperarm') else 'forearm' if name.startswith('body.lowerarm') else 'hand')+'.'+side
                delta=deltas[group];matrix=delta@rest[name]
                if name.startswith('body.lowerarm'):
                    a=solver.pose.bones['forearm.'+side].head
                    axis=(solver.pose.bones['hand.'+side].head-a).normalized()
                    q=(deltas['hand.'+side].to_quaternion()@delta.to_quaternion().inverted()).normalized()
                    projection=axis*Vector((q.x,q.y,q.z)).dot(axis)
                    angle=2*math.atan2(projection.dot(axis),q.w)
                    previous=twist_angles.get(name,0)
                    angle=previous+(angle-previous+math.pi)%math.tau-math.pi;twist_angles[name]=angle
                    amount=.22 if name.startswith('body.lowerarm01') else .72
                    center=matrix.translation.copy()
                    matrix=Matrix.Translation(center)@Matrix.Rotation(angle*amount,4,axis)@Matrix.Translation(-center)@matrix
                rig.pose.bones[name].matrix=matrix;bpy.context.view_layer.update()
            for name in controls+[b.name for b in body]:
                pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
                pb.keyframe_insert('location',frame=frame,group=name)
                pb.keyframe_insert('rotation_quaternion',frame=frame,group=name)
        for curve in action.fcurves:
            for key in curve.keyframe_points:key.interpolation='LINEAR'
        report.append({'clip':clip,'frames':last-first+1})
        print(kind,clip,'technique trial baked',flush=True)
    rig.animation_data.action=None;mod.show_viewport=True
    for pb in rig.pose.bones:
        pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
    bpy.data.objects.remove(dummy,do_unlink=True);bpy.data.objects.remove(solver,do_unlink=True)
    return {'changed_clips':report,'new_bones':0,'new_textures':0,'runtime_ik':False}
