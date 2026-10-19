"""Stage 4a: the MPFB CC0 body fitted to the shipped 92-joint game rig, with its 8 clips.

The game rig's `.L` bones sit at -X while MPFB's sit at +X, so the MPFB body is first mirrored in X
(left/right names swapped). Every kept MPFB bone segment is then mapped onto the game bone of the
same name: swing the source direction onto the game direction, stretch along the bone to the game
length, scale across it by the overall height ratio. Vertices blend those maps with their own
MPFB weights (four strongest), so at rest the body sits in the game rig's pose and proportions and
skins with the game's linear blend. Face/toe/eye bones the game rig dropped hand their weights to
the nearest kept ancestor.

  blender-python tools/part_pipeline/build_body.py --output .tmp/stage4/body.blend
"""
from pathlib import Path
import argparse, json, sys
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mpfb_fullbody import Body, ROOT

p = argparse.ArgumentParser(); p.add_argument('--rig', default=str(ROOT / 'public/models/yukimura.glb')); p.add_argument('--output', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.rig)
rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for o in list(bpy.context.scene.objects):
    if o is not rig and o.type != 'ARMATURE': bpy.data.objects.remove(o, do_unlink=True)
for pb in rig.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
W = rig.matrix_world
game_head = {b.name: W @ b.head_local for b in rig.data.bones}; game_tail = {b.name: W @ b.tail_local for b in rig.data.bones}

body = Body()
swap = lambda n: n[:-2] + {'.L': '.R', '.R': '.L'}[n[-2:]] if n.endswith(('.L', '.R')) else n
mirror = lambda v: Vector((-v.x, v.y, v.z))
# Mirrored source: positions reflected, and each bone takes the name of its mirror twin.
src_head = {swap(n): mirror(v) for n, v in body.heads.items()}; src_tail = {swap(n): mirror(v) for n, v in body.tails.items()}
parent = {swap(n): (swap(d['parent']) if d['parent'] else None) for n, d in body.definition.items()}
kept = {n for n in src_head if 'body.' + n in game_head}
def kept_ancestor(n):
    while n and n not in kept: n = parent[n]
    return n
g = (game_head['body.head'].z - game_head['body.foot.L'].z) / (src_head['head'].z - src_head['foot.L'].z)   # overall height ratio

# The game's body.* bones are pivots: their tails all point up (the original fit went through a
# mirror), so segment directions come from joint to joint: a bone's head to the head of the kept
# child that starts at its tail. Leaves (finger tips, head, feet) reuse the parent's linear map.
def chain_child(n):
    kids = [c for c in kept if parent[c] == n and (src_head[c] - src_tail[n]).length < 1e-4]
    if not kids:   # skipped intermediate bones (e.g. dropped twist helpers): nearest kept descendant at the tail
        kids = [c for c in kept if kept_ancestor(parent[c]) == n]
        kids = sorted(kids, key=lambda c: (src_head[c] - src_tail[n]).length)[:1]
    return kids[0] if kids else None

# The commander under the armour is heavier than the MPFB default: limbs are thickened across
# their bones (joints stay on the game rig) and the torso is widened about its own axis.
BULK = {'upperleg': 1.45, 'lowerleg': 1.35, 'upperarm': 1.3, 'lowerarm': 1.2}
TORSO_BULK = (1.12, 1.2)
def bulk(n): return next((k for p, k in BULK.items() if n.startswith(p)), 1.0)

def frame_scale(ds, dg, k=1.0):
    y = ds.normalized(); x = y.orthogonal().normalized(); z = y.cross(x)
    F = Matrix((x, y, z)).transposed().to_4x4()
    return F @ Matrix.Diagonal(Vector((g * k, dg.length / ds.length, g * k, 1))) @ F.inverted()

# Torso bones share one affine map (least squares over the torso joints) plus a per-bone
# translation that lands each joint exactly: per-bone swings tore the clavicles and hips apart.
import numpy as np
TORSO = ('root', 'spine', 'pelvis', 'clavicle', 'shoulder01', 'neck', 'head')
torso = [n for n in kept if n.startswith(TORSO)]
X = np.array([[*src_head[n], 1] for n in torso]); Y = np.array([list(game_head['body.' + n]) for n in torso])
sol = np.linalg.lstsq(X, Y, rcond=None)[0].T
A = Matrix([list(sol[i]) for i in range(3)] + [[0, 0, 0, 1]])
axis = Vector((0, float(np.mean([game_head['body.' + n].y for n in torso])), 0))
A = Matrix.Translation(axis) @ Matrix.Diagonal(Vector((*TORSO_BULK, 1, 1))) @ Matrix.Translation(-axis) @ A
maps = {n: Matrix.Translation(game_head['body.' + n] - A @ src_head[n]) @ A for n in torso}
def depth(n): return 0 if not parent[n] else 1 + depth(parent[n])
for n in sorted(kept, key=depth):                                  # parents first: leaves reuse their parent's map
    if n in maps: continue
    c = chain_child(n)
    if c is not None:
        ds, dg = src_head[c] - src_head[n], game_head['body.' + c] - game_head['body.' + n]
        swing = ds.normalized().rotation_difference(dg.normalized()).to_matrix().to_4x4()
        maps[n] = Matrix.Translation(game_head['body.' + n]) @ swing @ frame_scale(ds, dg, bulk(n)) @ Matrix.Translation(-src_head[n])
    else:
        k = kept_ancestor(parent[n]) if parent[n] else None
        lin = maps[k].to_3x3().to_4x4() if k in maps else Matrix.Diagonal(Vector((g, g, g, 1)))
        maps[n] = Matrix.Translation(game_head['body.' + n]) @ lin @ Matrix.Translation(-src_head[n])


# Mirrored mesh: positions reflected, faces reversed (reflection flips winding), weights renamed.
faces = [(list(reversed(f)), list(reversed(u))) for f, u in body.faces]
infl = {i: [(swap(n), w) for n, w in ws] for i, ws in body.influences.items()}
positions = {}
for i in {i for f, u in faces for i in f}:
    v = mirror(body.vertices[i]); acc = {}
    for n, w in infl[i]:
        k = kept_ancestor(n); acc[k] = acc.get(k, 0) + w
    positions[i] = sum((maps[k] @ v * w for k, w in acc.items()), Vector())
    infl[i] = list(acc.items())
body.influences = infl
body.definition = {n: {'parent': parent[n]} for n in kept}
obj, ids = body.mesh(rig, 'MPFB body', positions, faces, prefix='body.')

# Report how far the fitted joints land from the game joints (should be ~0 by construction for the
# bone heads; the useful number is the body surface staying around the bones).
resid = {n: round((maps[n] @ src_head[n] - game_head['body.' + n]).length, 5) for n in kept}
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
print(json.dumps({'kept_bones': len(kept), 'height_ratio': round(g, 4), 'vertices': len(obj.data.vertices), 'faces': len(obj.data.polygons),
                  'max_head_residual': max(resid.values()), 'actions': [x.name for x in bpy.data.actions]}))
