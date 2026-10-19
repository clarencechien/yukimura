"""Fit reference.png to the generated body's front silhouette (orthographic scale + offset).

u = u0 + s * x, v = v0 - s * z in reference pixels, body normalized to height 2 (front = -Y).
Coarse-to-fine IoU search starting from the bounding boxes; writes alignment.json.
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

p = argparse.ArgumentParser()
p.add_argument('--vertices', required=True, help='.npy of normalized generated-body vertices (with its own head)')
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/pass2/alignment.json')
a = p.parse_args()
co = np.load(a.vertices)
ref = np.array(Image.open(a.reference))[..., 3] > 128; H, W = ref.shape
def sil(s, u0, v0):
    u = np.round(u0 + s * co[:, 0]).astype(int); v = np.round(v0 - s * co[:, 2]).astype(int)
    ok = (u >= 0) & (u < W) & (v >= 0) & (v < H); m = np.zeros((H, W), bool); m[v[ok], u[ok]] = True
    return ndimage.binary_closing(ndimage.binary_dilation(m, iterations=2), iterations=3)
def iou(m): return float((m & ref).sum() / (m | ref).sum())
ys, xs = np.where(ref)
best = (0, (ys.max() - ys.min()) / 2.0, (xs.min() + xs.max()) / 2, ys.max())
for scales, step, reach in [(np.linspace(.96, 1.04, 9), 4, 12), (np.linspace(.99, 1.01, 5), 1, 3)]:
    _, s, u0, v0 = best
    for ds in scales:
        for du in range(-reach, reach + 1, step):
            for dv in range(-reach, reach + 1, step):
                score = iou(sil(s * ds, u0 + du, v0 + dv))
                if score > best[0]: best = (score, s * ds, u0 + du, v0 + dv)
score, s, u0, v0 = best
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
Path(a.output).write_text(json.dumps({'pixels_per_unit': float(s), 'u0': float(u0), 'v0': float(v0), 'iou': float(score), 'yaw_note': 'yaw search -8..8 deg peaked at +3 deg with IoU +0.0025; left at 0'}, indent=2) + '\n')
print(Path(a.output).read_text())
