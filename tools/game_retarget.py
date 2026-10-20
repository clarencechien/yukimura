"""Retarget the game's clips (public/models/yukimura.glb) onto another armature, by bone direction.

Every frame, each mapped target bone gets the world-space rotation its source bone has relative to the
source rest pose, applied after turning the target's rest direction onto the source's rest direction.
Unmapped target bones keep their rest pose relative to their parent. Only the root's travel is copied,
scaled by the leg-length ratio. Both armatures must face -Y; each clip becomes one NLA track.
"""
import bpy
from mathutils import Matrix, Vector

def load_source(path, keep_points_of=None):
    """Import the game rig, drop its meshes; returns the armature, or (armature, rest-pose world points of
    the vertices weighted over half to bone keep_points_of) when that is given."""
    scene = bpy.context.scene; before = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in scene.objects if o not in before]
    src = next(o for o in new if o.type == 'ARMATURE'); src.name = 'source rig'
    pts = []
    for o in new:
        if o.type == 'MESH' and keep_points_of and keep_points_of in o.vertex_groups:
            gi = o.vertex_groups[keep_points_of].index
            pts += [o.matrix_world @ v.co for v in o.data.vertices if any(g.group == gi and g.weight > .5 for g in v.groups)]
    for o in new:
        if o is not src: bpy.data.objects.remove(o, do_unlink=True)
    return (src, pts) if keep_points_of else src

def retarget(src, rig, mapping, clips, legs, anchors=None, grips=None):
    """mapping: {source bone: target bone}; legs: ((src thigh, shin, foot), (tgt thigh, shin, foot)), the
    first entry of mapping is the root. anchors: {source bone: source bone it is held by}, e.g. the weapon
    by the gripping hand: the bone keeps the source's world offset from that hand instead of hanging
    from its parent. grips: {source hand: source bone it holds}, e.g. the second hand on the spear: after
    the copy, that hand's arm is solved with two-bone IK so the hand keeps the source's offset from the
    held bone, the elbow bending toward the same side as the source's. Returns {clip: frames}."""
    anchors = anchors or {}; grips = grips or {}
    scene = bpy.context.scene
    def rest(arm, n): return arm.matrix_world @ arm.data.bones[n].matrix_local
    def leg_len(arm, chain):
        p = [rest(arm, n).translation for n in chain]; return (p[0] - p[1]).length + (p[1] - p[2]).length
    ratio = leg_len(rig, legs[1]) / leg_len(src, legs[0])
    scale = rig.matrix_world.to_scale()[0]
    src_rest = {s: rest(src, s) for s in mapping}; tgt_rest = {t: rest(rig, t) for t in mapping.values()}
    up = Vector((0, 1, 0))
    align = {s: (tgt_rest[t].to_3x3().normalized() @ up).rotation_difference(src_rest[s].to_3x3().normalized() @ up).to_matrix()
             for s, t in mapping.items()}
    def depth(b): return 0 if not b.parent else 1 + depth(b.parent)
    order = sorted(mapping, key=lambda s: (s in anchors, depth(rig.data.bones[mapping[s]])))
    root = next(iter(mapping))
    rig.animation_data_create(); src.animation_data_create(); out = {}
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    for clip in clips:
        act = next(x for x in bpy.data.actions if x.name.split('_')[0] == clip and x.name.endswith('_yukimura_Rig'))
        src.animation_data.action = act
        f0, f1 = act.frame_range; frames = int(round(f1 - f0)) + 1
        new = bpy.data.actions.new(clip); rig.animation_data.action = new
        for f in range(frames):
            scene.frame_set(int(f0) + f)
            for pb in rig.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
            bpy.context.view_layer.update()
            for s in order:
                t = mapping[s]; sp = src.matrix_world @ src.pose.bones[s].matrix
                R = (sp.to_3x3() @ src_rest[s].to_3x3().inverted()) @ align[s] @ tgt_rest[t].to_3x3().normalized()
                pb = rig.pose.bones[t]
                if s == root: head = tgt_rest[t].translation + (sp.translation - src_rest[s].translation) * ratio
                elif s in anchors:
                    hold = anchors[s]; hp = (src.matrix_world @ src.pose.bones[hold].matrix).translation
                    head = rig.matrix_world @ rig.pose.bones[mapping[hold]].head + (sp.translation - hp)
                else: head = rig.matrix_world @ pb.head
                pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(head) @ R.to_4x4() @ Matrix.Scale(scale, 4))
                bpy.context.view_layer.update()
            for hand, held in grips.items():
                _grip(src, rig, mapping, hand, held, scale)
            for pb in rig.pose.bones:
                if pb.name in mapping.values():
                    pb.keyframe_insert('rotation_quaternion', frame=f)
                    if pb.name == mapping[root] or pb.name in {mapping[x] for x in anchors}: pb.keyframe_insert('location', frame=f)
        track = rig.animation_data.nla_tracks.new(); track.name = clip; track.strips.new(clip, 0, new)
        rig.animation_data.action = None; out[clip] = frames
    src.animation_data.action = None
    for pb in rig.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    return out

def rest_bounds(rig, meshes):
    """World-space (min, max) of the skinned meshes in the rest pose (raw vertex data may be in bind space)."""
    pos = rig.data.pose_position; rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for o in meshes:
        e = o.evaluated_get(dg); m = e.to_mesh(); pts += [e.matrix_world @ v.co for v in m.vertices]; e.to_mesh_clear()
    rig.data.pose_position = pos; bpy.context.view_layer.update()
    return Vector([min(q[i] for q in pts) for i in range(3)]), Vector([max(q[i] for q in pts) for i in range(3)])


def place_like_source(src, rig, bone, points, tgt_bone=None):
    """Move rest-pose points that ride on the source's `bone` so that, rigidly bound to the target's bone,
    they follow exactly the source's motion (same world orientation, from the target bone's head)."""
    up = Vector((0, 1, 0)); sr = src.matrix_world @ src.data.bones[bone].matrix_local
    tr = rig.matrix_world @ rig.data.bones[tgt_bone or bone].matrix_local
    align = (tr.to_3x3().normalized() @ up).rotation_difference(sr.to_3x3().normalized() @ up).to_matrix()
    inv = align.inverted()
    return [tr.translation + inv @ (Vector(q) - sr.translation) for q in points]


def _grip(src, rig, mapping, hand, held, scale):
    """Two-bone IK: put the target hand where the source hand sits relative to the held bone."""
    def sw(n): return src.matrix_world @ src.pose.bones[n].matrix
    fore_s = src.pose.bones[hand].parent; arm_s = fore_s.parent
    goal = (rig.matrix_world @ rig.pose.bones[mapping[held]].head) + (sw(hand).translation - sw(held).translation)
    hb = rig.pose.bones[mapping[hand]]; fb = hb.parent; ab = fb.parent
    S = rig.matrix_world @ ab.head
    la = (ab.bone.head_local - ab.bone.tail_local).length * scale; lb = (fb.bone.head_local - fb.bone.tail_local).length * scale
    d_vec = goal - S; d = min(d_vec.length, (la + lb) * .999); dn = d_vec.normalized()
    # the source elbow's side of the shoulder-hand line is the pole
    ss, se, sh = sw(arm_s.name).translation, sw(fore_s.name).translation, sw(hand).translation
    pole = (se - ss) - (sh - ss).normalized() * (se - ss).dot((sh - ss).normalized())
    pole = (pole - dn * pole.dot(dn)).normalized() if pole.length > 1e-6 else Vector((0, 0, -1))
    x = (la * la - lb * lb + d * d) / (2 * d); h = max(la * la - x * x, 0) ** .5
    E = S + dn * x + pole * h; T = S + dn * d
    hand_rot = (rig.matrix_world @ hb.matrix).to_3x3().normalized()
    for pb, head, aim in ((ab, S, E), (fb, E, T)):
        cur = (rig.matrix_world @ pb.matrix).to_3x3().normalized()
        R = (cur @ Vector((0, 1, 0))).rotation_difference(aim - head).to_matrix() @ cur
        pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(head) @ R.to_4x4() @ Matrix.Scale(scale, 4))
        bpy.context.view_layer.update()
    hb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(T) @ hand_rot.to_4x4() @ Matrix.Scale(scale, 4))
    bpy.context.view_layer.update()
