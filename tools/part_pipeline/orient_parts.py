"""Stage 4b: find each generated part's facing direction from its mirror symmetry.

TRELLIS returns a part upright (Z up) but turned the way the drawing showed it (three-quarter
view). For each yaw, mirror the vertex cloud across the plane x=0 and score the mean nearest-
neighbour distance to the unmirrored cloud; the best yaw puts the part's symmetry plane on x=0.
The front is the side of that plane's normal facing the drawing's camera (azimuth 30 deg in the
render frame, i.e. towards (-0.5, -0.87)). Output: parts-orient.json {name: yaw_degrees, score}.

  blender-python tools/part_pipeline/orient_parts.py --parts .tmp/parts --output .tmp/stage4/parts-orient.json
"""
from pathlib import Path
import argparse, json, math, sys
import bpy
import numpy as np
from scipy.spatial import cKDTree

p = argparse.ArgumentParser(); p.add_argument('--parts', required=True); p.add_argument('--output', required=True)
p.add_argument('--names', default='helmet,do-front,do-back,sode,kote-forearm,gauntlet,haidate,knee,suneate,boot')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
CAMERA = np.array([-.5, -.866])
result = {}
for name in a.names.split(','):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(Path(a.parts, name, 'seed-1615', f'{name}-closed.glb').resolve()))
    pts = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in bpy.context.scene.objects if o.type == 'MESH'])
    pts = pts[np.random.default_rng(0).choice(len(pts), min(len(pts), 12000), replace=False)]
    pts -= pts.mean(0); tree_pts = pts
    scores = []
    for deg in range(0, 180):
        t = math.radians(deg); R = np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]])
        q = pts @ R.T; q[:, 0] -= np.median(q[:, 0])
        m = q.copy(); m[:, 0] *= -1
        d, _ = cKDTree(q).query(m); scores.append(d.mean())
    best = int(np.argmin(scores)); t = math.radians(best)
    # After rotating by `best`, the symmetry plane is x=0 and the front is +Y or -Y. In the
    # original frame that front is R^-1 (0, +-1); pick the sign facing the drawing's camera.
    fwd = np.array([-math.sin(t), -math.cos(t)])       # original-frame direction that R(best) maps to -Y
    yaw = best if fwd @ CAMERA > 0 else best + 180
    result[name] = {'yaw_deg': yaw % 360, 'symmetry_score': round(float(scores[best]), 5), 'score_spread': round(float(np.median(scores) / scores[best]), 2)}
    print(name, result[name], flush=True)
Path(a.output).parent.mkdir(parents=True, exist_ok=True); Path(a.output).write_text(json.dumps(result, indent=2) + '\n')
