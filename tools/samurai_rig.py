"""Lightweight rigid armour rig with deforming cape, authored locally in Blender."""
import bpy
import math
from mathutils import Vector

def bone_for_part(name):
    side='L' if '.-1' in name else 'R'
    if name.startswith(('antler','kabuto','helmet.coin','face','eye','menpo','mask','gold_fan','neck')):return 'head'
    if name.startswith('cape'):return 'cape'
    if name.startswith(('yari','katana','glove.1','finger.1')):return 'hand.R'
    if name.startswith(('glove.-1','finger.-1')):return 'hand.L'
    if name.startswith(('forearm','bracer','kote')):return 'forearm.'+side
    if name.startswith(('upper_arm','elbow','sode')):return 'arm.'+side
    if name.startswith(('thigh','haidate','knee')):return 'thigh.'+side
    if name.startswith(('shin','boot','sandal')):return 'shin.'+side
    if name.startswith(('kusazuri','waist','obi','wakizashi')):return 'pelvis'
    return 'chest'

def point(x,y,z,leg=False):
    x*=.82;y*=.90
    if leg:
        side=-1 if x<0 else 1;x+=side*.055;y+=side*.075
    if z>1.40:x*=.86;y*=.92;z=1.75+(z-1.40)*.88
    else:z*=1.25
    y-=max(0,z-1.05)*.10
    return (x,y,z)

def bind_hero(mesh):
    bpy.ops.object.select_all(action='DESELECT')
    data=bpy.data.armatures.new('Sanada articulated armour')
    rig=bpy.data.objects.new('SanadaRig',data);bpy.context.collection.objects.link(rig)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,a,b,parent=None):
        eb=data.edit_bones.new(name);eb.head=a;eb.tail=b
        if parent:eb.parent=data.edit_bones[parent]
    bone('pelvis',point(0,0,.88),point(0,0,1.03))
    bone('chest',point(0,0,1.03),point(0,0,1.38),'pelvis')
    bone('head',point(0,0,1.40),point(0,0,1.80),'chest')
    bone('cape',point(0,.17,1.36),point(0,.45,.75),'chest')
    for side,sign in [('L',-1),('R',1)]:
        bone('arm.'+side,point(sign*.31,0,1.32),point(sign*.43,-.025,1.10),'chest')
        bone('forearm.'+side,point(sign*.43,-.025,1.10),point(sign*.47,-.16,.94),'arm.'+side)
        bone('hand.'+side,point(sign*.47,-.16,.94),point(sign*.47,-.16,.86),'forearm.'+side)
        bone('thigh.'+side,point(sign*.145,0,.85,True),point(sign*.145,.015,.45,True),'pelvis')
        bone('shin.'+side,point(sign*.145,.015,.45,True),point(sign*.145,-.015,.10,True),'thigh.'+side)
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh.parent=rig
    mod=mesh.modifiers.new('articulated armour','ARMATURE');mod.object=rig
    # Blend the cape attachment into the torso: its collar stays secured while the hem moves.
    cape=mesh.vertex_groups.get('cape');chest=mesh.vertex_groups.get('chest')
    if cape and chest:
        for v in mesh.data.vertices:
            if any(g.group==cape.index for g in v.groups):
                w=max(0,min(1,(1.68-v.co.z)/.72))
                cape.add([v.index],w,'REPLACE');chest.add([v.index],1-w,'REPLACE')
    rig.animation_data_create()
    for name,frames in [('idle',60),('run',24),('slash',12),('reverse',14),('thrust',16),('spin',24)]:
        action=bpy.data.actions.new(name);rig.animation_data.action=action
        for frame in range(0,frames+1,2):
            phase=frame/frames*math.tau
            for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
            pose=rig.pose.bones
            if name=='idle':
                pose['chest'].rotation_euler.x=.022*math.sin(phase)
                pose['head'].rotation_euler.y=.018*math.sin(phase)
                pose['cape'].rotation_euler.x=.065*math.sin(phase+.6)
            elif name=='run':
                for side,sign in [('L',1),('R',-1)]:
                    gait=math.sin(phase)*sign
                    pose['thigh.'+side].rotation_euler.x=gait*.55
                    pose['shin.'+side].rotation_euler.x=-max(0,-gait)*.65
                    pose['arm.'+side].rotation_euler.x=-gait*.24-.13
                    pose['forearm.'+side].rotation_euler.x=-.18
                pose['chest'].rotation_euler.x=.06
                pose['chest'].rotation_euler.y=.055*math.sin(phase)
                pose['cape'].rotation_euler.x=.16+.10*math.sin(phase*2)
                pose['pelvis'].location.y=.016*(1-math.cos(phase*2))
            else:
                # Separate silhouettes with the strike at roughly 1/3 of each clip.
                t=frame/frames
                pulse=math.sin(min(1,t/.68)*math.pi) if t<.68 else 0
                sweep=math.sin((t-.10)*math.tau)*.68*math.sin(t*math.pi)
                sign=-1 if name=='reverse' else 1
                pose['chest'].rotation_euler.y=sweep*.8*sign
                pose['arm.R'].rotation_euler.x=-pulse*.65
                pose['arm.R'].rotation_euler.z=sweep*sign
                pose['forearm.R'].rotation_euler.x=-pulse*.24
                pose['arm.L'].rotation_euler.x=-pulse*.40
                pose['arm.L'].rotation_euler.z=pulse*.26
                pose['cape'].rotation_euler.x=pulse*.28
                pose['head'].rotation_euler.y=-sweep*.30*sign
                if name=='thrust':
                    pose['chest'].rotation_euler.x=pulse*.18
                    pose['chest'].rotation_euler.y=0
                    pose['arm.R'].rotation_euler.x=-pulse*1.10
                    pose['arm.R'].rotation_euler.z=-pulse*.18
                    pose['hand.R'].rotation_euler.x=-pulse*.40
                    pose['arm.L'].rotation_euler.x=-pulse*.80
                    pose['thigh.L'].rotation_euler.x=-pulse*.22
                    pose['shin.L'].rotation_euler.x=-pulse*.25
                if name=='spin':
                    pose['arm.R'].rotation_euler.x=-pulse*.65
                    pose['arm.R'].rotation_euler.z=pulse*.85
                    pose['arm.L'].rotation_euler.z=-pulse*.7
                    pose['chest'].rotation_euler.y=sweep
                    pose['cape'].rotation_euler.x=pulse*.45
            for pb in pose:
                pb.keyframe_insert('rotation_euler',frame=frame,group=pb.name)
                pb.keyframe_insert('location',frame=frame,group=pb.name)
        rig.animation_data.action=None
        track=rig.animation_data.nla_tracks.new();track.name=name
        strip=track.strips.new(name,0,action);strip.action_frame_start=0;strip.action_frame_end=frames
        track.mute=True
    # Reset the exported rest state; NLA tracks still export as independent clips.
    for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
    mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.context.scene.render.fps=30
    return rig
