"""Cut each stage-2 part image out of its flat grey background into an RGBA input for TRELLIS.2.

The images were drawn on a flat #BFBFBF-ish background, so a colour key is exact enough and
avoids a matting network (the TRELLIS default, BiRefNet, is excluded by the project's rules).
Background = pixels close to the border colour that are connected to the border, plus large
enclosed pockets of the same colour (gaps between antlers, inside straps). Optional crop boxes
pick one piece out of an image that shows several.

  python tools/part_pipeline/cutout.py            # all parts.json entries -> stage3/inputs/*.png
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / 'docs/experiments/future-sanada/part-pipeline/images'
OUT = ROOT / 'docs/experiments/future-sanada/part-pipeline/stage3/inputs'
# One piece out of a multi-piece image: polygon in image fractions; everything outside is background.
# kusazuri: the front panel only (the side panels behind it and the hanging rack are dropped).
POLY = {'kusazuri': [(.362, .255), (.708, .255), (.762, .835), (.352, .835)]}
# Extra inputs cut from one drawn image: name -> (source part, polygon). The whole arm read as a
# torso to TRELLIS (the shoulder opening looks like a neck), so the arm is split at the elbow.
DERIVED = {'kote-forearm': ('kote', [(.2, .455), (.72, .455), (.72, .93), (.2, .93)]),
           'kote-upper': ('kote', [(.25, .265), (.72, .265), (.72, .462), (.25, .462)])}
POLY.update({k: v[1] for k, v in DERIVED.items()})
spec = json.loads((Path(__file__).parent / 'parts.json').read_text())
OUT.mkdir(parents=True, exist_ok=True)
report = {}
for name in [q['name'] for q in spec['parts']] + list(DERIVED):
    im = Image.open(IMG / f"part-{DERIVED.get(name, (name,))[0]}.png").convert('RGB')
    rgb = np.asarray(im).astype(np.float32)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, 0)
    dist = np.linalg.norm(rgb - bg, axis=2)
    near = dist < 9                                                   # flat background; object never this grey-neutral at that value
    lab, n = ndimage.label(near)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    back = np.isin(lab, edge[edge > 0])
    sizes = ndimage.sum(near, lab, range(1, n + 1))
    pockets = np.isin(lab, 1 + np.flatnonzero(sizes > 4000)) & ~back
    back |= pockets
    if name in POLY:
        from PIL import ImageDraw
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).polygon([(x * im.width, y * im.height) for x, y in POLY[name]], fill=255)
        back |= np.asarray(m) == 0
    obj = ndimage.binary_opening(~back, iterations=1)
    keep, k = ndimage.label(obj)                                      # drop specks: keep components > 0.2% of the object
    areas = ndimage.sum(obj, keep, range(1, k + 1))
    obj = np.isin(keep, 1 + np.flatnonzero(areas > obj.sum() * .002))
    alpha = ndimage.gaussian_filter(obj.astype(np.float32), .8)       # soft 1-2 px edge
    ys, xs = np.nonzero(obj); pad = int(.04 * max(rgb.shape[:2]))
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, rgb.shape[1]), min(ys.max() + pad, rgb.shape[0]))
    rgba = np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8)[box[1]:box[3], box[0]:box[2]]
    Image.fromarray(rgba, 'RGBA').save(OUT / f'{name}.png')
    report[name] = {'size': [int(box[2] - box[0]), int(box[3] - box[1])], 'object_fraction': round(float(obj.mean()), 3),
                    'pocket_pixels': int(pockets.sum()), 'components': int(k), 'polygon': POLY.get(name)}
(OUT / 'cutout-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
