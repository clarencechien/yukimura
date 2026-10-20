"""Image-to-3D through the Tripo API (v3), for comparison with TRELLIS.2.

Uploads the image (or, with --view, a turnaround: multiview-to-model), creates one task per --variant, polls until it finishes and
downloads every model file the task returns, plus the task record (parameters, credits used).
The secret key (tsk_...) is read from the first of TRIPO_API_KEY, tripo_key, tripo_secret, tripo
that holds a tsk_ key; it is never printed or written to disk.

  python tools/tripo_generate.py --image docs/experiments/future-sanada/reference.png \
      --output .tmp/tripo --variant ultra --variant parts
  python tools/tripo_generate.py --view front=f.png --view left=l.png --view back=b.png \
      --output .tmp/tripo-mv --variant ultra
"""
from pathlib import Path
import argparse, json, os, sys, time, urllib.error, urllib.request, uuid

# International accounts (developers.tripo3d.ai, Stripe billing); China mainland is openapi.tripo3d.com.
API = os.environ.get('TRIPO_API_BASE', 'https://openapi.tripo3d.ai/v3')
VARIANTS = {
    # Best quality: newest geometry model, Ultra geometry, detailed PBR textures.
    'ultra': {'model': 'v3.1-20260211', 'geometry_quality': 'detailed', 'texture': True, 'pbr': True, 'texture_quality': 'detailed'},
    # Same geometry model with Tripo's part segmentation (geometry only: parts exclude textures).
    'parts': {'model': 'v3.1-20260211', 'generate_parts': True, 'texture': False, 'pbr': False},
    # Game budget: P2 low-poly triangles (quad output would force FBX), under the 90k commander limit.
    'game': {'model': 'P2-20260801', 'face_limit': 45000, 'texture': True, 'pbr': True, 'texture_quality': 'detailed'},
}
p = argparse.ArgumentParser()
p.add_argument('--image'); p.add_argument('--output', required=True)
p.add_argument('--task', action='append', default=[], metavar='VARIANT=TASK_ID', help='download an existing task again instead of creating one')
p.add_argument('--view', action='append', default=[], metavar='NAME=PATH',
               help='front/left/back/right images for multiview-to-model (front required, at least two)')
p.add_argument('--variant', action='append', choices=sorted(VARIANTS), required=True)
p.add_argument('--balance', action='store_true', help='only print the credit balance')
a = p.parse_args()
key = next((os.environ[k] for k in ('TRIPO_API_KEY', 'tripo_key', 'tripo_secret', 'tripo') if os.environ.get(k, '').startswith('tsk_')), None)
if not key: sys.exit('No Tripo secret key (tsk_...) in TRIPO_API_KEY / tripo_key / tripo_secret / tripo.')

def call(method, path, body=None, files=None):
    headers = {'Authorization': f'Bearer {key}'}
    data = None
    if files:
        boundary = uuid.uuid4().hex; name, blob = files
        data = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: image/png\r\n\r\n').encode() + blob + f'\r\n--{boundary}--\r\n'.encode()
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    elif body is not None:
        data = json.dumps(body).encode(); headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r: out = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {path}: HTTP {e.code} {e.read().decode()[:1500]}')
    if out.get('code') not in (0, None): sys.exit(f'{method} {path}: {json.dumps(out)[:1500]}')
    return out.get('data', out)

print('balance before:', json.dumps(call('GET', '/account/balance')), flush=True)
if a.balance: sys.exit()
out_dir = Path(a.output); out_dir.mkdir(parents=True, exist_ok=True)
def upload(path): return call('POST', '/files', files=(Path(path).name, Path(path).read_bytes()))['file_token']
views = {}
if a.task:
    source, endpoint = {}, None
elif a.view:
    views = dict(x.split('=', 1) for x in a.view)
    if 'front' not in views or len(views) < 2 or not set(views) <= {'front', 'left', 'back', 'right'}: sys.exit('--view needs front plus at least one of left/back/right')
    source = {'inputs': [{name: upload(path)} for name, path in views.items()]}; endpoint = '/generation/multiview-to-model'
elif a.image:
    source = {'input': upload(a.image)}; endpoint = '/generation/image-to-model'
else:
    sys.exit('give --image or --view')
tasks = dict(x.split('=', 1) for x in a.task)
for v in ([] if a.task else a.variant):
    body = {**source, **VARIANTS[v]}
    tasks[v] = call('POST', endpoint, body)['task_id']
    print('created', v, tasks[v], flush=True)
pending = dict(tasks); results = {}
while pending:
    time.sleep(10)
    for v, tid in list(pending.items()):
        t = call('GET', f'/tasks/{tid}')
        if t.get('status') in ('success', 'failed', 'cancelled', 'banned', 'expired', 'unknown'):
            results[v] = t; del pending[v]; print(v, t.get('status'), 'progress', t.get('progress'), flush=True)
for v, t in results.items():
    d = out_dir / v; d.mkdir(exist_ok=True)
    files = []
    for k, url in (t.get('output') or {}).items():
        if isinstance(url, str) and url.startswith('http'):
            ext = Path(url.split('?')[0]).suffix or '.bin'
            dest = d / f'{v}-{k}{ext}'
            for attempt in range(4):                     # signed CDN links; retry transient resets
                try:
                    with urllib.request.urlopen(url, timeout=600) as r: dest.write_bytes(r.read())
                    break
                except (urllib.error.URLError, ConnectionError) as e:
                    if attempt == 3: raise
                    print('retrying download:', e, flush=True); time.sleep(2 ** (attempt + 1))
            files.append({'key': k, 'file': dest.name, 'bytes': dest.stat().st_size})
    record = {'variant': v, 'endpoint': endpoint or t.get('type'), 'views': sorted(views) or None, 'parameters': VARIANTS[v], 'task': {k: t.get(k) for k in t if k != 'output'}, 'files': files}
    (d / 'task.json').write_text(json.dumps(record, indent=2) + '\n')
    print(v, json.dumps(files), flush=True)
print('balance after:', json.dumps(call('GET', '/account/balance')), flush=True)
