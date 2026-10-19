"""Fit the finished head study onto a regenerated body: scale + translation by trimmed ICP.

Both meshes come from the same character design, so the generated body's own helmet is the
target. Writes head-fit.json consumed by refine_trellis_body_v2.py.
"""
from pathlib import Path
import argparse, json
import bpy
import numpy as np
from mathutils import Matrix
from scipy.spatial import cKDTree

p = argparse.ArgumentParser()
p.add_argument('--body', required=True)
p.add_argument('--head', default='docs/experiments/future-sanada/head-study/refined/head-preview.glb')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/head-fit.json')
p.add_argument('--scale', type=float, help='Fix the head scale and refit translation only')
p.add_argument('--neck-z', type=float, default=1.45, help='Only body points above this (normalized height 2) are matched')
a = p.parse_args()

def points(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(Path(path).resolve()))
    chunks = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        co = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get('co', co)
        m = np.array(o.matrix_world); co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]; chunks.append(co)
    return np.concatenate(chunks)

body = points(a.body); low, high = body.min(0), body.max(0)
body = (body - [(low[0] + high[0]) / 2, (low[1] + high[1]) / 2, low[2]]) * (2 / (high[2] - low[2]))
head = points(a.head)  # head study is already normalized to height 2 at its origin
rng = np.random.default_rng(1615)
target = body[body[:, 2] > a.neck_z]; target = target[rng.choice(len(target), min(len(target), 60000), replace=False)]
source = head[rng.choice(len(head), min(len(head), 60000), replace=False)]
tree = cKDTree(target)
scale, t = .26, np.array([0, -.005, 1.44])  # previous static fit as initial guess
history = []
for it in range(80):
    moved = source * scale + t
    d1, i1 = tree.query(moved); d2, i2 = cKDTree(moved).query(target)
    k1 = d1 < np.quantile(d1, .85); k2 = d2 < np.quantile(d2, .85)
    # Symmetric correspondences: head->body alone lets the scale collapse inward.
    s_pts = np.concatenate([source[k1], source[i2[k2]]]); t_pts = np.concatenate([target[i1[k1]], target[k2]])
    sc, tc = s_pts.mean(0), t_pts.mean(0)
    scale = float(((s_pts - sc) * (t_pts - tc)).sum() / ((s_pts - sc) ** 2).sum())
    t = tc - scale * sc
    history.append(float(np.sqrt(((s_pts * scale + t - t_pts) ** 2).sum(1).mean())))
    if it > 5 and abs(history[-2] - history[-1]) < 1e-7: break
# Optionally lock scale (e.g. from a sharper export of the same generation), then refit
# translation only; the free ICP scale drifts with how smooth the body helmet is.
icp_scale = scale
if a.scale: scale = a.scale
for it in range(40 if a.scale else 0):
    moved = source * scale + t
    d1, i1 = tree.query(moved); d2, i2 = cKDTree(moved).query(target)
    k1 = d1 < np.quantile(d1, .85); k2 = d2 < np.quantile(d2, .85)
    s_pts = np.concatenate([source[k1], source[i2[k2]]]); t_pts = np.concatenate([target[i1[k1]], target[k2]])
    t = (t_pts - s_pts * scale).mean(0)
history.append(float(np.sqrt(((s_pts * scale + t - t_pts) ** 2).sum(1).mean())))
moved = source * scale + t
d_head, _ = tree.query(moved); d_body, _ = cKDTree(moved).query(target)
head_low, head_high = moved.min(0), moved.max(0)
# Remove the generated helmet, face and antlers above the head study's neck guard bottom.
# Removal rules for the generated head (normalized body units); see refine_trellis_body_v2.py.
remove = {'antler_band_z_min': 1.74, 'core_z_min': 1.56, 'core_abs_x_max': 0.20, 'near_head_z_min': 1.44, 'near_head_distance': 0.012}
antler = {'note': 'span measured on the z > 1.85 slice of each placed mesh', 'body_top_z': float(body[:, 2].max()), 'head_top_z': float(head_high[2]), 'body_antler_span_x': float(np.ptp(body[body[:, 2] > 1.85, 0])), 'head_antler_span_x': float(np.ptp(moved[moved[:, 2] > 1.85, 0])) if (moved[:, 2] > 1.85).any() else None}
report = {'free_icp_scale': icp_scale, 'antler_check': antler, 'body': a.body, 'head': a.head, 'method': 'symmetric trimmed ICP (85% inliers each way); optional fixed scale, translation refit', 'iterations': len(history),
          'scale': scale, 'translation': t.tolist(), 'rms_inlier': history[-1],
          'head_to_body_p50': float(np.median(d_head)), 'head_to_body_p90': float(np.quantile(d_head, .9)),
          'body_to_head_p50': float(np.median(d_body)), 'body_to_head_p90': float(np.quantile(d_body, .9)),
          'head_bounds': [head_low.tolist(), head_high.tolist()], 'remove_rules': remove}
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
Path(a.output).write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report, indent=2))
