"""Locate the reference's glowing energy slits as centre lines (reference pixels).

Seeds were picked by eye from zoomed crops; around each seed the brightest red-orange pixels
are thresholded relative to the local maximum and reduced to a centre line by PCA.
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

SEEDS = {  # name: (x, y) in reference.png; char right = image left
    'forearm right outer': (255, 690), 'forearm left inner': (752, 686), 'forearm left outer': (809, 690),
    'chest left side': (570, 545), 'knee left lens': (582, 1088), 'knee right lens': (400, 1090),
    'shin right': (345, 1250), 'shin left': (690, 1266),
}
p = argparse.ArgumentParser()
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/pass3/energy-seams.json')
a = p.parse_args()
im = np.asarray(Image.open(a.reference).convert('RGB')).astype(np.float32)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
glow = np.clip((r - b) / 255, 0, 1) * np.clip(r / 255, 0, 1) * (r - g > 30)
seams = []
for name, (sx, sy) in SEEDS.items():
    R = 40
    win = glow[sy - R:sy + R, sx - R:sx + R]
    mask = win > .55 * win.max()
    lab, n = ndimage.label(ndimage.binary_closing(mask, structure=np.ones((3, 3))))
    sizes = ndimage.sum(mask, lab, range(1, n + 1)); comp = lab == (np.argmax(sizes) + 1)
    yy, xx = np.nonzero(comp); pts = np.stack([xx + sx - R, yy + sy - R], 1).astype(np.float64)
    c = pts.mean(0); u, s_, vt = np.linalg.svd(pts - c); axis = vt[0]
    t = (pts - c) @ axis; width = np.ptp((pts - c) @ vt[1]) + 1
    seams.append({'name': name, 'p0': (c + axis * t.min()).round(1).tolist(), 'p1': (c + axis * t.max()).round(1).tolist(),
                  'width_px': float(width), 'pixels': int(len(pts)), 'peak': float(win.max())})
Path(a.output).write_text(json.dumps({'source': a.reference, 'seams': seams}, indent=2) + '\n')
for s_ in seams: print(s_)
