"""Put the game's clips on Tripo's auto-rig, so both rigging lines can be compared on the same motion
(and to check that a Tripo rig can use the game's existing animation).

Tripo exports face +X at 1 unit tall; the rig is turned to face -Y and scaled to 2 m like the open line.
The game names its +X side '.R', which is Mixamo's Left once both face -Y.

  blender-python tools/rig_tripo_gameclips.py --glb docs/.../rig/tripo/rig-model_url.glb \
      --output .tmp/rig-tripo/tripo-gameclips.glb --clips idle,run,slash,hurt
"""
from pathlib import Path
import argparse, json, math, sys
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0, str(Path(__file__).parent)); import game_retarget

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--glb', required=True); p.add_argument('--output', required=True)
p.add_argument('--source', default=str(ROOT / 'public/models/yukimura.glb')); p.add_argument('--clips', default='idle,run,slash,hurt')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
src = game_retarget.load_source(a.source)
before = set(scene.objects)
bpy.ops.import_scene.gltf(filepath=a.glb)
new = [o for o in scene.objects if o not in before]
rig = next(o for o in new if o.type == 'ARMATURE')
meshes = [o for o in new if o.type == 'MESH' and o.parent is rig]
for o in new:
    if o is not rig and o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
if rig.animation_data:
    rig.animation_data.action = None
    for t in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(t)
bpy.context.view_layer.update()
lo, hi = game_retarget.rest_bounds(rig, meshes); zmin = lo.z; s = 2.0 / (hi.z - lo.z)
rig.matrix_world = Matrix.Translation((0, 0, -zmin * s)) @ Matrix.Rotation(-math.pi / 2, 4, 'Z') @ Matrix.Scale(s, 4) @ rig.matrix_world
bpy.context.view_layer.update()
M = 'mixamorig:'
mapping = {'pelvis': M + 'Hips', 'chest': M + 'Spine', 'head': M + 'Neck'}
for g, x in (('R', 'Left'), ('L', 'Right')):
    mapping.update({f'arm.{g}': f'{M}{x}Arm', f'forearm.{g}': f'{M}{x}ForeArm', f'hand.{g}': f'{M}{x}Hand',
                    f'thigh.{g}': f'{M}{x}UpLeg', f'shin.{g}': f'{M}{x}Leg', f'foot.{g}': f'{M}{x}Foot'})
clips = game_retarget.retarget(src, rig, mapping, a.clips.split(','),
                               (('thigh.R', 'shin.R', 'foot.R'), (M + 'LeftUpLeg', M + 'LeftLeg', M + 'LeftFoot')))
bpy.data.objects.remove(src, do_unlink=True)
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
for o in meshes: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out.resolve()), export_format='GLB', use_selection=True, export_animations=True, export_animation_mode='NLA_TRACKS')
print(json.dumps({'clips': clips, 'bones': len(rig.data.bones), 'mapped': len(mapping)}))
