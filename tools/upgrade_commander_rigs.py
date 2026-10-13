"""Retarget CC0 full-body deformation bones onto the existing combat controls.

Keeps the expensive painted armor atlas. Replaces rigid gloves/forearms with
continuous weighted anatomical arms and individually fitted kote splints.
Input v13 GLBs are snapshotted once in .tmp; export is staged for review.
"""
from pathlib import Path
import bpy,bmesh,json,math,sys,shutil,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Matrix,Vector
from mpfb_fullbody import Body,ROOT,material,extract_hand_study
from commander_hands import basis,SCALE
from gltf_assets import share_images
STAGE=ROOT/'.tmp/fullbody-v14';STAGE.mkdir(exist_ok=True,parents=True)
OUT=STAGE/'models';OUT.mkdir(exist_ok=True)
STUDY,ARMOR=extract_hand_study();body=Body()
def depth(n):
    p=body.definition[n]['parent'];return 1+depth(p) if p else 0
ORDER=sorted(body.definition,key=depth)
# Canonical source coordinates agree with the hand study: +Y fingers, +Z palm.
o=body.heads['wrist.R'];y=(body.heads['finger3-1.R']-o).normalized();x=body.heads['finger2-1.R']-body.heads['finger5-1.R'];x=(x-y*x.dot(y)).normalized();C=Matrix((x,y,x.cross(y))).to_4x4()@Matrix.Translation(-o)
MIRROR=Matrix.Diagonal(Vector((-1,1,1,1)))

def coarse(n):
    side=n[-1] if n.endswith(('.L','.R')) else ''
    if n.startswith(('finger','metacarpal','wrist')):return 'hand.'+side
    if n.startswith('lowerarm'):return 'forearm.'+side
    if n.startswith('upperarm'):return 'arm.'+side
    if n.startswith('upperleg'):return 'thigh.'+side
    if n.startswith('lowerleg'):return 'shin.'+side
    if n.startswith(('foot','toe')):return 'foot.'+side
    if n.startswith(('neck','head','jaw','eye','orbicularis','levator','temporalis','risorius','oculi','oris')):return 'head'
    return 'pelvis' if n.startswith(('root','pelvis','spine04','spine05')) else 'chest'

def frame(axis,normal):
    y=axis.normalized();z=(normal-y*normal.dot(y)).normalized();x=y.cross(z);return Matrix((x,y,z)).transposed()

def fit_segment(a,b,h,t,normal,targetnormal,width=1):
    source=frame(b-a,normal);dest=frame(t-h,targetnormal)
    scale=Matrix.Diagonal(Vector((width,(t-h).length/(b-a).length,width)))
    return Matrix.Translation(h)@(dest@scale@source.transposed()).to_4x4()@Matrix.Translation(-a)

def run(kind):
    snapshot=STAGE/(kind+'-v13.glb')
    from prepare_commander_base import prepare
    prepare(ROOT/'assets/source/samurai-kit.blend',snapshot,STAGE/(kind+'-source.sha256'))
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=90
    bpy.ops.import_scene.gltf(filepath=str(snapshot))
    rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    for obj in list(scene.objects):
        if obj not in (rig,mesh):bpy.data.objects.remove(obj,do_unlink=True)
    from samurai_rig import bind_hero
    mesh.parent=None
    for mod in list(mesh.modifiers):
        if mod.type=='ARMATURE':mesh.modifiers.remove(mod)
    bpy.data.objects.remove(rig,do_unlink=True)
    rig=bind_hero(mesh,kind,reweight=False,natural_wrists=True)
    oldrest={b.name:b.matrix_local.copy() for b in rig.data.bones}
    oldhead={b.name:b.head_local.copy() for b in rig.data.bones};oldtail={b.name:b.tail_local.copy() for b in rig.data.bones}
    # Save original imported actions, use their actual frame range (NLA import adds an offset).
    actions=[(t.name,t.strips[0].action) for t in rig.animation_data.nla_tracks]
    for t in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(t)
    rig.animation_data.action=None
    # MPFB rest matrices / complete original source rig are retained separately.
    source_rig=body.armature();source_rest={b.name:b.matrix_local.copy() for b in source_rig.data.bones}
    source_mesh,_=body.mesh(source_rig);source_mesh.data.materials.append(material('CC0 anatomical clay',(.28,.33,.36)))
    bpy.data.objects.remove(source_mesh,do_unlink=True);bpy.data.objects.remove(source_rig,do_unlink=True)
    fits={};finger_pose={};canon={}
    for side,sign in [('R',1),('L',-1)]:
        # Reflect the source left hand into the same canonical coordinates.
        canonical=C if side=='R' else C@MIRROR;canon[side]=canonical
        fits['hand.'+side]=Matrix.Translation(oldhead['hand.'+side])@basis(sign).to_4x4()@Matrix.Scale(SCALE,4)@canonical
        palm=(canonical.inverted().to_3x3()@Vector((0,0,1))).normalized()
        for group,first,last in [('arm','upperarm01','upperarm02'),('forearm','lowerarm01','lowerarm02'),('thigh','upperleg01','upperleg02'),('shin','lowerleg01','lowerleg02'),('foot','foot','foot')]:
            n=group+'.'+side;fits[n]=fit_segment(body.heads[first+'.'+side],body.tails[last+'.'+side],oldhead[n],oldtail[n],palm if group in ('arm','forearm') else Vector((0,-1,0)),Vector((0,-1,0)),1.07)
        for n in body.definition:
            if n.endswith('.'+side):
                right=n[:-1]+'R'
                finger_pose[n]=canonical.inverted()@STUDY.get(right,Matrix.Identity(4))@canonical if n.startswith(('finger','metacarpal','wrist')) else Matrix.Identity(4)
    for group,src in [('pelvis','spine05'),('chest','spine02'),('head','head')]:
        fits[group]=Matrix.Translation(oldhead[group])@Matrix.Diagonal(Vector((-1,1,1.12,1)))@Matrix.Translation(-body.heads[src])
    # Keep limb, spine, neck and finger chains; exclude unused face/toe controls.
    keep={n for n in body.definition if n.startswith(('root','spine','pelvis','neck','head','clavicle','shoulder','upperarm','lowerarm','wrist','metacarpal','finger','upperleg','lowerleg','foot'))}
    for n in list(keep):
        p=body.definition[n]['parent']
        while p:keep.add(p);p=body.definition[p]['parent']
    transforms={n:fits[coarse(n)]@finger_pose.get(n,Matrix.Identity(4)) for n in body.definition}
    def matrix_for(n):
        m=transforms[n]@source_rest[n];rot=m.to_quaternion().to_matrix().to_4x4();rot.translation=m.translation;return rot
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for n in body.definition:
        if n not in keep:continue
        b=rig.data.edit_bones.new('body.'+n);b.matrix=matrix_for(n);b.length=(transforms[n]@body.tails[n]-transforms[n]@body.heads[n]).length
    for n in keep:
        p=body.definition[n]['parent'];rig.data.edit_bones['body.'+n].parent=rig.data.edit_bones['body.'+p] if p in keep else rig.data.edit_bones['pelvis']
    bpy.ops.object.mode_set(mode='OBJECT');rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
    # Replace complete old gloves and rigid forearm cylinders; preserve expensive armor UVs.
    remove_groups={g.index for g in mesh.vertex_groups if g.name.startswith(('hand.','forearm.'))}
    bm=bmesh.new();bm.from_mesh(mesh.data);deform=bm.verts.layers.deform.active
    doomed=[v for v in bm.verts if sum(w for g,w in v[deform].items() if g in remove_groups)>.5]
    bmesh.ops.delete(bm,geom=doomed,context='VERTS');bm.to_mesh(mesh.data);bm.free();mesh.data.update()
    # Preserve continuous upper arm -> elbow -> wrist -> fingers. The shoulder cut
    # is hidden inside the chest/sode; nothing is cut or welded at the wrist.
    def is_arm(i):return sum(w for n,w in body.influences[i] if n.startswith(('upperarm','lowerarm','wrist','metacarpal','finger')))>.72
    faces=[(f,u) for f,u in body.faces if all(is_arm(i) for i in f)]
    positions={i:sum((transforms[n]@body.vertices[i]*w for n,w in body.influences[i]),Vector()) for i in {i for f,u in faces for i in f}}
    arms,ids=body.mesh(rig,'continuous arms and articulated gloves',positions,faces,prefix='body.')
    # Remove unused vertex groups before export so unused face bones stay out.
    for g in list(arms.vertex_groups):
        if g.name[5:] not in keep:arms.vertex_groups.remove(g)
    leather=material('commander deerskin and cloth',(.027,.018,.012),.88)
    arms.data.materials.append(leather)
    # One subdivision level preserves finger curvature with a modest runtime cost.
    bpy.context.view_layer.objects.active=arms
    sub=arms.modifiers.new('anatomical silhouette','SUBSURF');sub.levels=1
    bpy.ops.object.modifier_move_up(modifier=sub.name)
    bpy.ops.object.modifier_apply(modifier=sub.name)
    dec=arms.modifiers.new('arm and hand game budget','DECIMATE');dec.ratio=.55;bpy.ops.object.modifier_apply(modifier=dec.name)
    lacquer=material('fitted crimson kote' if kind=='yukimura' else 'fitted black iron kote',(.19,.007,.013) if kind=='yukimura' else (.025,.02,.012),.36,.48)
    parts=[mesh,arms]
    for side in ('R','L'):
        for label,vertices,polys in ARMOR:
            is_hand='tekko' in label
            # Study armor coordinates are canonical; forearm splints follow the
            # source forearm fit, the back-of-hand plate follows the wrist.
            fit=fits['hand.'+side] if is_hand else fits['forearm.'+side]
            v=[fit@canon[side].inverted()@p for p in vertices]
            data=bpy.data.meshes.new(label);data.from_pydata(v,[],polys if side=='R' else [list(reversed(f)) for f in polys]);data.update()
            ob=bpy.data.objects.new(label+' '+side,data);scene.collection.objects.link(ob);data.materials.append(lacquer)
            for p in data.polygons:p.use_smooth=True
            vg=ob.vertex_groups.new(name='body.'+('wrist.' if is_hand else 'lowerarm02.')+side);vg.add(list(range(len(v))),1,'REPLACE')
            bpy.context.view_layer.objects.active=ob
            dec=ob.modifiers.new('mobile plate budget','DECIMATE');dec.ratio=.20 if is_hand else .08;bpy.ops.object.modifier_apply(modifier=dec.name)
            parts.append(ob)
    # Every section needs white vertex color defaults: Blender joins missing
    # corner attributes as zero, which would turn the new armor black.
    for part in parts[1:]:
        for attr in mesh.data.color_attributes:
            ca=part.data.color_attributes.get(attr.name) or part.data.color_attributes.new(name=attr.name,type=attr.data_type,domain=attr.domain)
            for value in ca.data:value.color=(1,1,1,1)
    # Join meshes once: 3 material sections, one shared skeleton, four influences.
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join();mesh.name=kind+'_runtime';mesh.parent=rig
    mesh.data.calc_loop_triangles()
    # Bind armor to matching deformation bones as well; controls remain available
    # for existing gameplay attachment names and animation retargeting.
    armor_map={'pelvis':'spine05','chest':'spine02','head':'head'}
    for side in ('L','R'):
        armor_map.update({'arm.'+side:'upperarm01.'+side,'thigh.'+side:'upperleg01.'+side,'shin.'+side:'lowerleg01.'+side,'foot.'+side:'foot.'+side})
    for old,new in armor_map.items():
        src=mesh.vertex_groups.get(old);dst=mesh.vertex_groups.get('body.'+new) or mesh.vertex_groups.new(name='body.'+new)
        if src:
            for v in mesh.data.vertices:
                for g in v.groups:
                    if g.group==src.index:dst.add([v.index],g.weight,'REPLACE')
            mesh.vertex_groups.remove(src)
    # Bake retargeting. Distal forearm gets wrist roll gradually, without moving
    # the wrist center; this is the deformation absent from the previous model.
    validation=[];rig.animation_data.action=None
    skin_mod=next(m for m in mesh.modifiers if m.type=='ARMATURE');skin_mod.show_viewport=False
    for clip,action in actions:
        twist_angles={}
        rig.animation_data.action=action
        first,last=map(round,action.frame_range)
        for frame_no in range(first,last+1):
            scene.frame_set(frame_no);bpy.context.view_layer.update()
            deltas={n:rig.pose.bones[n].matrix@oldrest[n].inverted() for n in oldrest}
            for n in ORDER:
                if n not in keep:continue
                g=coarse(n);delta=deltas[g];m=delta@rest['body.'+n]
                if n.startswith('lowerarm'):
                    side=n[-1];a=rig.pose.bones['forearm.'+side].head.copy();wrist=rig.pose.bones['hand.'+side].head.copy();axis=(wrist-a).normalized()
                    # Match the hand's transverse frame around the forearm axis.
                    q=(deltas['hand.'+side].to_quaternion()@delta.to_quaternion().inverted()).normalized()
                    projection=axis*Vector((q.x,q.y,q.z)).dot(axis)
                    # Unwrap the longitudinal angle before splitting it. Taking
                    # the shortest quaternion independently at every frame would
                    # jump +180 -> -180 and tear the interpolated wrist off its grip.
                    angle=2*math.atan2(projection.dot(axis),q.w)
                    previous=twist_angles.get(n,0)
                    angle=previous+(angle-previous+math.pi)%math.tau-math.pi
                    twist_angles[n]=angle
                    amount=.22 if n.startswith('lowerarm01') else .72
                    rotation=Matrix.Rotation(angle*amount,4,axis)
                    center=m.translation.copy();m=Matrix.Translation(center)@rotation@Matrix.Translation(-center)@m
                if clip.startswith('fall') and n.startswith('finger'):
                    t=(frame_no-first)/max(1,last-first);release=max(0,min(1,(t-.18)/.5))*.7
                    # Open each joint with FK: preserve bone lengths and let the
                    # children follow the parent instead of fixing world positions.
                    side=n[-1];joint=int(n.split('-')[1].split('.')[0]);degrees=[20,45,25][joint-1]
                    if n.startswith('finger1-'):degrees*=.4
                    axis_world=(fits[g].to_3x3()@canon[side].inverted().to_3x3()@Vector((1,0,0))).normalized()
                    local_axis=(rest['body.'+n].to_3x3().inverted()@axis_world).normalized()
                    parent=rig.pose.bones['body.'+n].parent
                    m=parent.matrix@parent.bone.matrix_local.inverted()@rest['body.'+n]@Matrix.Rotation(-math.radians(degrees)*release,4,local_axis)
                pb=rig.pose.bones['body.'+n];pb.rotation_mode='QUATERNION';pb.matrix=m
                # Parent matrices must update before setting a child's world matrix.
                bpy.context.view_layer.update()
                pb.keyframe_insert('location',frame=frame_no,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=frame_no,group=pb.name)
            if frame_no in (first,(first+last)//2,last):
                skin_mod.show_viewport=True;bpy.context.view_layer.update()
                deps=bpy.context.evaluated_depsgraph_get();e=mesh.evaluated_get(deps)
                assert all(math.isfinite(c) for v in e.data.vertices for c in v.co)
                skin_mod.show_viewport=False
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
        rig.animation_data.action=None
        track=rig.animation_data.nla_tracks.new();track.name=clip;strip=track.strips.new(clip,0,action);strip.action_frame_start=first;strip.action_frame_end=last;track.mute=True
        print(kind,clip,'retargeted',flush=True)
    skin_mod.show_viewport=True
    for pb in rig.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/optimized/commanders'/f'{kind}-fullbody.blend'),compress=True)
    target=OUT/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    textures=share_images(target)
    result={'triangles':len(mesh.data.loop_triangles),'bones':len(rig.data.bones),'source_bones':163,'materials':len(mesh.data.materials),'bytes':target.stat().st_size,'textures':textures,'source':'MPFB CC0','body_vertices':len(body.groups['body']),'retargeted_clips':[c for c,a in actions]}
    (STAGE/f'{kind}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else (sys.argv[1:] if sys.argv[0].endswith('.py') else [])
assert all(k in ('yukimura','ieyasu') for k in args),'Unknown commander'
for kind in args or ['yukimura','ieyasu']:run(kind)
