"""Generate the per-part images of stage 2 from parts.json, a few at a time.

  python tools/part_pipeline/gen_parts.py [--only helmet,sode] [--jobs 4]
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / 'docs/experiments/future-sanada/part-pipeline/images'
REFS = [IMG / 'ab-front-gemini-3-pro-image.png', IMG / 'sheet-side.png', IMG / 'sheet-back-knotA2.png']
p = argparse.ArgumentParser(); p.add_argument('--only'); p.add_argument('--jobs', type=int, default=4)
p.add_argument('--model', default='google/gemini-3-pro-image')
a = p.parse_args()
spec = json.loads((Path(__file__).parent / 'parts.json').read_text())
parts = [q for q in spec['parts'] if not a.only or q['name'] in a.only.split(',')]

def run(q):
    prompt = spec['common'].replace('{desc}', q['desc']).replace('{view}', q['view'])
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f: f.write(prompt)
    cmd = [sys.executable, str(Path(__file__).parent / 'gen_image.py'), '--model', a.model, '--prompt-file', f.name,
           '--aspect', q['aspect'], '--output', str(IMG / f"part-{q['name']}.png")] + sum((['--ref', str(r)] for r in REFS), [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    return q['name'], (r.stdout.strip() or r.stderr.strip()[-500:])

with ThreadPoolExecutor(a.jobs) as ex:
    for name, out in ex.map(run, parts): print(name, out, flush=True)
