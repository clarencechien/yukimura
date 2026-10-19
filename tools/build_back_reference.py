"""Compose a 'back view' texture source from the front reference for the dō and skirt.

The single reference has no back view. A real dō's back mirrors the front lames, so this
reuses clean front areas: five chest lames clear of the tassels are mirrored about the centre
line across the back plate, and the rope knot / hanging tassels over the centre skirt panel are replaced
by the panel's own lames shifted upward. Front-only parts (neck rope, tassels) disappear.
Pixel boxes are in reference.png coordinates (1024 x 1536).
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('--reference', default='docs/experiments/future-sanada/reference.png')
p.add_argument('--output', default='docs/experiments/future-sanada/body-v2/pass2/back-reference.png')
a = p.parse_args()
ref = np.array(Image.open(a.reference).convert('RGBA')).copy()
out = ref.copy()
LAMES = (395, 535, 440, 636)        # x0, x1, y0, y1: five clean chest lames (no tassels / side buckles)
PITCH = 37                           # lame pitch in pixels, measured between the chest gaps
CENTRE = 507                         # model centre line in reference pixels (silhouette fit)
TOP = 372                            # back plate continues up to the shoulder yoke
x0, x1, y0, y1 = LAMES
strip = ref[y0:y1, x0:x1]
half = np.concatenate([strip[:, ::-1], strip], 1)  # mirrored about the centre: symmetric back
w = half.shape[1]
for y in range(TOP, y1):
    sy = y if y >= y0 else y + 2 * PITCH          # repeat the upper lames, pitch-aligned
    row = half[sy - y0]
    out[y, CENTRE - w // 2:CENTRE - w // 2 + w] = row
PLATE = (CENTRE - w // 2, CENTRE - w // 2 + w, TOP, y1)
period = PITCH
KNOT = (378, 532, 660, 762)          # rope knot + tassels over the centre skirt panel
SHIFT = 100                          # copy panel lames from this far below
kx0, kx1, ky0, ky1 = KNOT
out[ky0:ky1, kx0:kx1] = ref[ky0 + SHIFT:ky1 + SHIFT, kx0:kx1]
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(out).save(a.output)
Path(a.output).with_suffix('.json').write_text(json.dumps({'source': a.reference, 'lames_box': LAMES, 'plate_box': PLATE, 'lame_pitch_px': period, 'centre_px': CENTRE, 'knot_box': KNOT, 'knot_shift_px': SHIFT}, indent=2) + '\n')
