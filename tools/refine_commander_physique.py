"""Shape the existing v14 skinned meshes; preserve bind poses and grip contacts.

Run after upgrade_commander_rigs.py. Always reads its unchanged v14 .blend,
so repeat builds do not accumulate the morph. No subdivision or animation bake.
"""
from pathlib import Path
import sys, json, math
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_assets import share_images

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / '.tmp/physique-v15'
OUT = STAGE / 'models'
OUT.mkdir(parents=True, exist_ok=True)


def smooth(a, b, value):
    t = max(0., min(1., (value-a)/(b-a)))
    return t*t*(3-2*t)


def profile(t, knots):
    for (a, x), (b, y) in zip(knots, knots[1:]):
        if t <= b:
            return x+(y-x)*smooth(a, b, t)
    return knots[-1][1]


def reshape(mesh, rig, kind):
    assert not mesh.get('physique_revision'), 'Expected the unmodified v14 source'
    groups = {g.index: g.name for g in mesh.vertex_groups}
    # Ieyasu has a heavier build; Yukimura remains an athletic spearman.
    heavy = 1.12 if kind == 'ieyasu' else 1.
    axes = {n: (rig.data.bones[n].head_local.copy(),
                rig.data.bones[n].tail_local-rig.data.bones[n].head_local)
            for n in ('arm.R','arm.L','forearm.R','forearm.L',
                      'thigh.R','thigh.L','shin.R','shin.L')}
    materials = {}
    for polygon in mesh.data.polygons:
        for i in polygon.vertices:
            materials[i] = polygon.material_index

    def radial(p, bone, knots, depth=1.):
        start, axis = axes[bone]
        t = (p-start).dot(axis)/axis.length_squared
        center = start+axis*t
        offset = p-center
        gain = (profile(t, knots)-1)*heavy
        # The back/front volume is slightly fuller than the lateral silhouette.
        front = Vector((0,-1,0))
        front = (front-axis*front.dot(axis)/axis.length_squared).normalized()
        return offset*gain+front*offset.dot(front)*gain*(depth-1)

    before = [v.co.copy() for v in mesh.data.vertices]
    for vertex in mesh.data.vertices:
        if vertex.index not in materials:
            continue  # Loose source vertices are omitted by the glTF exporter.
        p = vertex.co.copy()
        weights = [(groups[g.group],g.weight) for g in vertex.groups]
        delta = Vector()
        material = materials[vertex.index]
        for name, weight in weights:
            side = name[-1]
            if name.startswith('body.upperarm'):
                if material == 1:
                    # Deltoid/biceps volume, tapering into the elbow; avoid a tube.
                    delta += radial(p,'arm.'+side,[(0,1.42),(.35,1.70),(.65,1.62),(1,1.28)],1.1)*weight
                elif material == 0:
                    # Existing shoulder lamellae already have ample coverage.
                    delta += radial(p,'arm.'+side,[(0,1.06),(.5,1.08),(1,1.08)])*weight
            elif name.startswith('body.lowerarm'):
                # Skin and kote splints use the same envelope, preserving clearance.
                delta += radial(p,'forearm.'+side,[(0,1.28),(.30,1.64),(.60,1.52),(1,1.16)],1.08)*weight
            elif name.startswith('body.wrist'):
                start, axis = axes['forearm.'+side]
                t = (p-start).dot(axis)/axis.length_squared
                # Fade at the heel of the hand. Fingers and weapon contact stay put.
                fade = 1-smooth(.90,1.25,t)
                delta += radial(p,'forearm.'+side,[(0,1.16),(1,1.16)])*weight*fade
            elif name.startswith(('body.spine','body.clavicle','body.shoulder','body.neck')):
                chest = smooth(1.12,1.55,p.z)
                # Broader chest/back with a narrower belt; no global X scale.
                delta += Vector((p.x*(.035+.07*chest)*heavy,
                                 (p.y+.045)*(.025+.07*chest)*heavy,0))*weight
            elif name.startswith('body.upperleg'):
                delta += radial(p,'thigh.'+side,[(0,1.09),(.4,1.12),(1,1.06)])*weight
            elif name.startswith('body.lowerleg'):
                delta += radial(p,'shin.'+side,[(0,1.06),(.35,1.10),(1,1.02)])*weight
        vertex.co += delta
    # Lift the dark cloth enough that the new volume can read in the same light.
    leather = mesh.data.materials[1]
    leather.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.047,.035,.026,1)
    mesh['physique_revision'] = 'v15'
    mesh.data.update()
    changed = [i for i,v in enumerate(mesh.data.vertices) if (v.co-before[i]).length>1e-7]
    finger_only = [v for v in mesh.data.vertices if v.groups and
                   all(groups[g.group].startswith('body.finger') for g in v.groups)]
    assert all((v.co-before[v.index]).length<1e-7 for v in finger_only)
    assert all(math.isfinite(c) for v in mesh.data.vertices for c in v.co)
    return {'changed_vertices':len(changed), 'vertices':len(before),
            'max_displacement_m':max((v.co-before[v.index]).length for v in mesh.data.vertices),
            'unchanged_finger_vertices':len(finger_only),
            'topology_changed':False,'bind_pose_changed':False,
            'extra_textures':0,'source':'v14 fullbody .blend',
            'upper_arm_peak_radius_multiplier':1+.70*heavy,
            'forearm_peak_radius_multiplier':1+.64*heavy}


def run(kind):
    source=ROOT/'assets/optimized/commanders'/f'{kind}-fullbody.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH' and o.parent==rig)
    report=reshape(mesh,rig,kind)
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(source.with_name(f'{kind}-physique.blend')),compress=True)
    target=OUT/f'{kind}.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,
        export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',
        export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    textures=share_images(target)
    mesh.data.calc_loop_triangles()
    info={'triangles':len(mesh.data.loop_triangles),'bones':len(rig.data.bones),'source_bones':163,
          'materials':len(mesh.data.materials),'bytes':target.stat().st_size,'textures':textures,
          'physique':report}
    (STAGE/f'{kind}.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info),flush=True)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    assert all(k in ('yukimura','ieyasu') for k in args)
    for kind in args or ['yukimura','ieyasu']:run(kind)
