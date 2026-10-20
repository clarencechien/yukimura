"""Contact sheet: one row per part, input cut-out | colour 30 | colour 210 | clay 30 | clay 210."""
from pathlib import Path
import argparse
from PIL import Image, ImageDraw
p = argparse.ArgumentParser(); p.add_argument('--renders', required=True); p.add_argument('--inputs', required=True)
p.add_argument('--names', required=True); p.add_argument('--suffix', default='', help='e.g. -closed'); p.add_argument('--output', required=True); p.add_argument('--tile', type=int, default=300)
a = p.parse_args(); T = a.tile; names = a.names.split(',')
W = Image.new('RGB', (T * 5, T * len(names)), (26, 31, 38)); d = ImageDraw.Draw(W)
for r, n in enumerate(names):
    cells = [Path(a.inputs) / f'{n}.png'] + [Path(a.renders) / f'{n}{a.suffix}-{k}.png' for k in ('color-30', 'color-210', 'clay-30', 'clay-210')]
    for c, f in enumerate(cells):
        if not f.exists(): continue
        im = Image.open(f); im.thumbnail((T, T))
        if im.mode == 'RGBA': bg = Image.new('RGB', im.size, (26, 31, 38)); bg.paste(im, (0, 0), im); im = bg
        W.paste(im.convert('RGB'), (c * T + (T - im.width) // 2, r * T + (T - im.height) // 2))
    d.text((6, r * T + 6), n, fill='white')
W.save(a.output, quality=88)
