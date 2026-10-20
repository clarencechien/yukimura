"""Retarget the game's clips (public/models/yukimura.glb) onto another armature, by bone direction.

Every frame, each mapped target bone gets the world-space rotation its source bone has relative to the
source rest pose, applied after turning the target's rest direction onto the source's rest direction.
Unmapped target bones keep their rest pose relative to their parent. Only the root's travel is copied,
scaled by the leg-length ratio. Both armatures must face -Y; each clip becomes one NLA track.
"""
import bpy
from mathutils import Matrix, Vector

def load_source(path):
    """Import the game rig, drop its meshes; returns the armature."""
    scene = bpy.context.scene; before = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in scene.objects if o not in before]
    src = next(o for o in new if o.type == 'ARMATURE'); src.name = 'source rig'
    for o in new:
        if o is not src: bpy.data.objects.remove(o, do_unlink=True)
    return src

def retarget(src, rig, mapping, clips, legs):
    """mapping: {source bone: target bone}; legs: ((src thigh, shin, foot), (tgt thigh, shin, foot)), the
    first entry of mapping is the root. Returns {clip: frames}."""
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
    order = sorted(mapping, key=lambda s: depth(rig.data.bones[mapping[s]]))
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
                head = (tgt_rest[t].translation + (sp.translation - src_rest[s].translation) * ratio) if s == root else rig.matrix_world @ pb.head
                pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(head) @ R.to_4x4() @ Matrix.Scale(scale, 4))
                bpy.context.view_layer.update()
            for pb in rig.pose.bones:
                if pb.name in mapping.values():
                    pb.keyframe_insert('rotation_quaternion', frame=f)
                    if pb.name == mapping[root]: pb.keyframe_insert('location', frame=f)
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
