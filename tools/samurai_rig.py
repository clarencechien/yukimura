"""Two-hand spear poses and planted gait, solved offline and baked to glTF bones."""
import bpy
import math
from mathutils import Vector, Matrix

def bone_for_part(name):
    side='L' if '.-1' in name else 'R'
    if name.startswith(('antler','kabuto','helmet.coin','face','eye','menpo','mask','gold_fan','neck','jingasa')):return 'head'
    if name.startswith('cape'):return 'cape'
    if name.startswith(('yari','katana')):return 'weapon'
    if name.startswith(('glove','finger')):return 'hand.'+side
    if name.startswith(('forearm','bracer','kote')):return 'forearm.'+side
    if name.startswith(('upper_arm','elbow','sode')):return 'arm.'+side
    if name.startswith(('thigh','haidate','knee')):return 'thigh.'+side
    if name.startswith(('boot','sandal')):return 'foot.'+side
    if name.startswith('shin'):return 'shin.'+side
    if name.startswith(('kusazuri','waist','obi','wakizashi')):return 'pelvis'
    return 'chest'

def point(x,y,z,leg=False):
    x*=.82;y*=.90
    if leg:
        side=-1 if x<0 else 1;x+=side*.055;y+=side*.075
    if z>1.40:x*=.86;y*=.92;z=1.75+(z-1.40)*.88
    else:z*=1.25
    y-=max(0,z-1.05)*.10
    return Vector((x,y,z))

def weapon_point(p):
    # One rigid transform keeps shafts, collars and blades aligned at all heights.
    return point(.47,-.16,.91)+Matrix.Rotation(.28,3,'X') @ Vector(((p.x-.47)*.90,(p.y+.16)*.90,(p.z-.91)*1.10))

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def sample(keys,t):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
    return keys[-1][1]

def bind_hero(mesh,kind='yukimura',reweight=True):
    hero=kind=='yukimura'
    bpy.ops.object.select_all(action='DESELECT')
    data=bpy.data.armatures.new(kind+' articulated armour')
    rig=bpy.data.objects.new(kind+'_Rig',data);bpy.context.collection.objects.link(rig)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,a,b,parent=None):
        eb=data.edit_bones.new(name);eb.head=a;eb.tail=b
        if parent:eb.parent=data.edit_bones[parent]
    bone('pelvis',point(0,0,.88),point(0,0,1.03))
    bone('chest',point(0,0,1.03),point(0,0,1.38),'pelvis')
    bone('head',point(0,0,1.40),point(0,0,1.80),'chest')
    bone('cape',point(0,.17,1.36),point(0,.32,.90),'chest')
    bone('cape_tip',point(0,.32,.90),point(0,.57,.35),'cape')
    origin=point(.47,-.16,.91);axis=(weapon_point(Vector((.47,-.16,1.91)))-origin).normalized()
    bone('weapon',origin,origin+axis*.35,'chest')
    for side,sign in [('L',-1),('R',1)]:
        bone('arm.'+side,point(sign*.31,0,1.32),point(sign*.43,-.025,1.10),'chest')
        bone('forearm.'+side,point(sign*.43,-.025,1.10),point(sign*.47,-.16,.94),'arm.'+side)
        bone('hand.'+side,point(sign*.47,-.16,.94),point(sign*.47,-.16,.86),'forearm.'+side)
        bone('thigh.'+side,point(sign*.145,0,.85,True),point(sign*.145,.015,.45,True),'pelvis')
        bone('shin.'+side,point(sign*.145,.015,.45,True),point(sign*.145,-.015,.13,True),'thigh.'+side)
        bone('foot.'+side,point(sign*.145,-.015,.13,True),point(sign*.145,-.21,.07,True),'shin.'+side)
    bpy.ops.object.mode_set(mode='OBJECT');mesh.parent=rig
    mod=mesh.modifiers.new('articulated armour','ARMATURE');mod.object=rig
    cape=mesh.vertex_groups.get('cape');chest=mesh.vertex_groups.get('chest');tip=mesh.vertex_groups.get('cape_tip') or mesh.vertex_groups.new(name='cape_tip')
    if reweight and cape and chest:
        for v in mesh.data.vertices:
            if any(g.group==cape.index for g in v.groups):
                root=max(0,min(1,(v.co.z-1.25)/.45));hem=max(0,min(1,(1.18-v.co.z)/.55))
                cape.add([v.index],1-root-hem,'REPLACE');chest.add([v.index],root,'REPLACE');tip.add([v.index],hem,'REPLACE')
    pelvis=mesh.vertex_groups.get('pelvis')
    if reweight and pelvis:
        for v in mesh.data.vertices:
            if v.co.z<1.1 and abs(v.co.x)>.10 and any(g.group==pelvis.index for g in v.groups):
                w=max(0,min(.75,(1.12-v.co.z)*1.7));side='L' if v.co.x<0 else 'R';leg=mesh.vertex_groups.get('thigh.'+side)
                if leg:pelvis.add([v.index],1-w,'REPLACE');leg.add([v.index],w,'REPLACE')
    pose=rig.pose.bones;rest={b.name:b.matrix_local.copy() for b in data.bones}
    rig.animation_data_create();max_error=0
    def orient(name,head,tail):
        b=data.bones[name];q=(b.tail_local-b.head_local).rotation_difference(tail-head)
        pose[name].matrix=Matrix.Translation(head) @ q.to_matrix().to_4x4() @ rest[name].to_3x3().to_4x4()
        bpy.context.view_layer.update()
    def ik(first,second,target,pole):
        b=data.bones[first];parent=pose[first].parent
        head=(parent.matrix @ parent.bone.matrix_local.inverted()) @ b.head_local
        l1=b.length;l2=data.bones[second].length;delta=target-head
        d=max(.02,min(delta.length,(l1+l2)*.998));axis=delta.normalized()
        bend=Vector(pole)-head;bend-=axis*bend.dot(axis);bend.normalize()
        along=(l1*l1-l2*l2+d*d)/(2*d)
        elbow=head+axis*along+bend*math.sqrt(max(0,l1*l1-along*along))
        end=head+axis*d;orient(first,head,elbow);orient(second,elbow,end)
        return end,(end-target).length
    clips=[('idle',48),('run',24),('slash',30),('reverse',30),('thrust',30),('spin',36),('dash',18),('hurt',18)] if hero else [('idle',48),('run',24),('thrust',30),('hurt',18),('fall',42),('fall_back',42)]
    for name,frames in clips:
        action=bpy.data.actions.new(name);rig.animation_data.action=action
        for frame in range(frames+1):
            t=frame/frames;phase=t*math.tau
            for pb in pose:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
            twist=0;lean=.06;drop=.045;stride=0;grip=Vector((.22,-.23,1.38));axis=Vector((-.78,-.24,.58));spacing=.42
            if name=='idle':drop+=.008*math.sin(phase);lean+=.012*math.sin(phase)
            elif name=='run':
                drop=.06+.025*math.cos(phase*2);lean=.15;twist=.10*math.sin(phase)
                grip=Vector((.24,-.24,1.39));axis=Vector((-.79,-.33,.52))
            elif name in ('slash','reverse','spin'):
                impact=.44 if name=='spin' else .34;sign=-1 if name=='reverse' else 1
                twist=sign*sample([(0,0),(.19,-.58),(impact,.48),(.66,.73),(1,0)],t)
                height=sample([(0,.58),(.18,.82),(impact,.10),(.65,-.22),(1,.58)],t)
                axis=Vector((-.80,-.32,height));grip.z+=.065*math.sin(t*math.pi)
                stride=math.sin(t*math.pi)*.20;drop+=.075*math.sin(t*math.pi);lean=.09
            elif name=='thrust':
                push=sample([(0,0),(.23,-.05),(.38,.17),(.59,.17),(1,0)],t)
                grip=Vector((.04,.045-push,1.40));axis=Vector((-.12,-.98,.13));spacing=.30
                stride=.25*math.sin(t*math.pi);drop+=.08*math.sin(t*math.pi);lean=.15*math.sin(t*math.pi)+.06
            elif name=='dash':lean=.28;drop=.18;stride=.24;axis=Vector((-.78,-.5,.05));grip.z=1.35
            elif name in ('hurt','fall','fall_back'):
                recoil=math.sin(min(1,t/.7)*math.pi) if name=='hurt' else smooth(t)
                lean=-recoil*.28;drop+=recoil*.18;twist=recoil*.18;axis=Vector((-.78,.1,.55));grip.z-=recoil*.08
            pose['pelvis'].matrix=Matrix.Translation((.015*math.sin(phase) if name=='run' else 0,0,-drop)) @ rest['pelvis']
            pose['chest'].rotation_quaternion=(Matrix.Rotation(lean,4,'X') @ Matrix.Rotation(twist,4,'Y')).to_quaternion()
            pose['head'].rotation_quaternion=Matrix.Rotation(-twist*.35,4,'Y').to_quaternion()
            pose['cape'].rotation_quaternion=Matrix.Rotation(.12+(.16 if name in ('run','dash') else .04)*math.sin(phase+.5),4,'X').to_quaternion()
            pose['cape_tip'].rotation_quaternion=(Matrix.Rotation(.13*math.sin(phase-1),4,'X') @ Matrix.Rotation(.09*math.sin(phase),4,'Y')).to_quaternion()
            bpy.context.view_layer.update()
            for side,sign in [('L',-1),('R',1)]:
                ankle=point(sign*.145,-.015,.13,True)
                if name=='run':
                    u=(t+(0 if side=='L' else .5))%1
                    if u<.6:ankle.y+=-.36+.72*u/.6
                    else:q=(u-.6)/.4;ankle.y+=.36-.72*smooth(q);ankle.z+=.17*math.sin(q*math.pi)
                else:ankle.y+=sign*stride
                end,_=ik('thigh.'+side,'shin.'+side,ankle,(sign*.18,-1,.55))
                direction=data.bones['foot.'+side].tail_local-data.bones['foot.'+side].head_local
                orient('foot.'+side,end,end+direction)
            if kind=='ieyasu':spacing=.10
            body=pose['chest'].matrix @ rest['chest'].inverted()
            world_grip=body@grip;world_axis=(body.to_3x3()@axis).normalized()
            orient('weapon',world_grip,world_grip+world_axis*.35)
            for side,sign in [('L',-1),('R',1)]:
                target=world_grip+(world_axis*spacing if side=='L' else Vector((0,0,0)))
                end,error=ik('arm.'+side,'forearm.'+side,target+Vector((0,0,.038)),body@Vector((sign*.65,-.05,1.12)))
                max_error=max(max_error,error);orient('hand.'+side,end,end+Vector((0,0,-.1)))
            if name in ('fall','fall_back'):
                # An articulated collapse: recoil, one knee gives way, hand contact,
                # hip/shoulder impact and a small settle. The actor root stays upright.
                back=name=='fall_back'
                collapse=sample([(0,0),(.16,0),(.46,.30),(.74,.91),(1,1)],t)
                pitch=sample([(0,0),(.16,-.16),(.43,.32),(.78,1.48),(1,1.46)],t)
                if back:pitch=-sample([(0,0),(.16,.13),(.42,.18),(.78,1.44),(1,1.43)],t)
                height=sample([(0,1.055),(.16,.98),(.43,.65),(.78,.31),(.87,.335),(1,.30)],t)
                roll=sample([(0,0),(.43,.12),(.80,.30),(1,.38)],t)*(1 if back else -1)
                pivot=Vector((.08*collapse,.10*collapse,height))
                rotation=Matrix.Rotation(pitch,4,'X') @ Matrix.Rotation(roll,4,'Z')
                pose['pelvis'].matrix=Matrix.Translation(pivot) @ rotation @ rest['pelvis'].to_3x3().to_4x4()
                pose['chest'].rotation_quaternion=Matrix.Rotation(-.11 if back else .18,4,'X').to_quaternion()
                pose['head'].rotation_quaternion=Matrix.Rotation(.16 if back else -.20,4,'X').to_quaternion()
                pose['cape'].rotation_quaternion=Matrix.Rotation(-.04,4,'X').to_quaternion()
                pose['cape_tip'].rotation_quaternion=Matrix.Rotation(.05,4,'X').to_quaternion()
                bpy.context.view_layer.update()
                for side,sign in [('L',-1),('R',1)]:
                    initial=point(sign*.145,-.015,.13,True)
                    target=Vector((sign*(.26 if back else .32),(-.73 if back else .64)+( .19 if side=='L' else -.13),.12))
                    ankle=initial.lerp(target,collapse)
                    end,_=ik('thigh.'+side,'shin.'+side,ankle,(sign*.55,-.5 if not back else .5,.36))
                    orient('foot.'+side,end,end+Vector((sign*.035,-.13,.035)))
                body=pose['chest'].matrix @ rest['chest'].inverted()
                # Left palm breaks the fall; the weapon arm loosens separately.
                for side,sign in [('L',-1),('R',1)]:
                    start=body@Vector((sign*.24,-.25,1.38))
                    target=Vector((sign*(.48 if side=='L' else .57),(.68 if back else -.75)+sign*.17,.18))
                    hand=start.lerp(target,smooth((t-.18)/.60))
                    end,_=ik('arm.'+side,'forearm.'+side,hand,(sign*.72,-.2,.45))
                    orient('hand.'+side,end,end+Vector((sign*.08,-.035,-.035)))
                    if side=='R':
                        axis=Vector((-.75,-.22,.65)).lerp(Vector((.10,-.99,.035)),collapse).normalized()
                        orient('weapon',end-Vector((0,0,.02)),end-Vector((0,0,.02))+axis*.35)
                # Keep the deformed body/weapon above the ground throughout contact.
                bpy.context.view_layer.update()
                evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
                deformed=evaluated.to_mesh()
                floor=min(v.co.z for v in deformed.vertices)
                evaluated.to_mesh_clear()
                if floor<.012:
                    matrix=pose['pelvis'].matrix.copy();matrix.translation.z+=.012-floor;pose['pelvis'].matrix=matrix
                    bpy.context.view_layer.update()
            for pb in pose:
                pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name);pb.keyframe_insert('location',frame=frame,group=pb.name)
        for fcurve in action.fcurves:
            for key in fcurve.keyframe_points:key.interpolation='LINEAR'
        rig.animation_data.action=None
        track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,action);strip.action_frame_start=0;strip.action_frame_end=frames;track.mute=True
    for pb in pose:pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0)
    mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh;bpy.context.scene.render.fps=30
    rig['max_hand_target_error']=max_error;print(f'{kind}: maximum authoring hand IK residual {max_error:.4f} m')
    return rig
