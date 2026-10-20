"""Cut the flat studio-grey background out of the Nano Banana Pro turnaround sheets (front, left side,
back) so TRELLIS.2 gets RGBA inputs with a clean alpha, like reference.png.

Background = pixels close to the border colour that are connected to the border; a 1-pixel feather.

  python tools/multiview/key_views.py
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'docs/experiments/future-sanada/part-pipeline/images'
OUT = ROOT / 'docs/experiments/future-sanada/multiview/inputs'
VIEWS = {'front': 'ab-front-gemini-3-pro-image.png', 'left': 'sheet-side.png', 'back': 'sheet-back-knotA2.png'}

def key(path, tol=14):
    rgb = np.asarray(Image.open(path).convert('RGB')).astype(np.int16)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, 0)
    near = np.abs(rgb - bg).max(2) <= tol
    lab, _ = ndimage.label(near)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    background = np.isin(lab, edge[edge > 0])
    fg = ndimage.binary_fill_holes(ndimage.binary_opening(~background, iterations=2))
    keep, n = ndimage.label(fg)                       # drop specks: keep the largest piece
    if n > 1: fg = keep == (np.argmax(ndimage.sum(fg, keep, range(1, n + 1))) + 1)
    alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
    out = Image.fromarray(rgb.astype(np.uint8)); out.putalpha(alpha)
    return out, bg

OUT.mkdir(parents=True, exist_ok=True)
for view, name in VIEWS.items():
    im, bg = key(SRC / name); im.save(OUT / f'{view}.png')
    a = np.asarray(im)[:, :, 3]; ys, xs = np.nonzero(a > 128)
    print(view, name, 'bg', bg.tolist(), 'figure bbox', xs.min(), ys.min(), xs.max(), ys.max())
