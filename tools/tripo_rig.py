"""Rig a Tripo generation and retarget preset animations onto it (Tripo API v3).

rig-check -> rig (biped, v3.0, Mixamo bone names) -> one retarget task with several presets.
Every task record (parameters, status, credits) is written next to the downloaded files. The key is
read the same way as tripo_generate.py and never printed or written.

  python tools/tripo_rig.py --input <generation task id> --output .tmp/tripo-rig \
      --animations preset:idle,preset:run,preset:slash,preset:hurt
"""
from pathlib import Path
import argparse, json, os, sys, time, urllib.error, urllib.request

API = os.environ.get('TRIPO_API_BASE', 'https://openapi.tripo3d.ai/v3')
p = argparse.ArgumentParser()
p.add_argument('--input', required=True, help='task_id of the generation to rig')
p.add_argument('--output', required=True)
p.add_argument('--rig-model', default='v3.0-20260909'); p.add_argument('--spec', default='mixamo')
p.add_argument('--animations', default='preset:idle,preset:run,preset:slash,preset:hurt')
a = p.parse_args()
key = next((os.environ[k] for k in ('TRIPO_API_KEY', 'tripo_key', 'tripo_secret', 'tripo') if os.environ.get(k, '').startswith('tsk_')), None)
if not key: sys.exit('No Tripo secret key (tsk_...) in TRIPO_API_KEY / tripo_key / tripo_secret / tripo.')

def call(method, path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r: out = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {path}: HTTP {e.code} {e.read().decode()[:1500]}')
    if out.get('code') not in (0, None): sys.exit(f'{method} {path}: {json.dumps(out)[:1500]}')
    return out.get('data', out)

def wait(task_id):
    while True:
        t = call('GET', f'/tasks/{task_id}')
        if t.get('status') in ('success', 'failed', 'cancelled', 'banned', 'expired', 'unknown'): return t
        time.sleep(8)

out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
records = {}
def run(step, path, body):
    tid = call('POST', path, body)['task_id']; print(step, 'task', tid, flush=True)
    t = wait(tid); print(step, t.get('status'), 'credits', t.get('credits_consumed'), flush=True)
    files = []
    for k, url in (t.get('output') or {}).items():
        if isinstance(url, str) and url.startswith('http'):
            dest = out / f'{step}-{k}{Path(url.split("?")[0]).suffix or ".bin"}'
            with urllib.request.urlopen(url, timeout=600) as r: dest.write_bytes(r.read())
            files.append({'key': k, 'file': dest.name, 'bytes': dest.stat().st_size})
    records[step] = {'parameters': body, 'task': {k: v for k, v in t.items() if k != 'output'}, 'output': {k: v for k, v in (t.get('output') or {}).items() if not (isinstance(v, str) and v.startswith('http'))}, 'files': files}
    (out / 'tasks.json').write_text(json.dumps(records, indent=2) + '\n')
    if t.get('status') != 'success': sys.exit(f'{step} did not succeed')
    return tid, t

print('balance before:', json.dumps(call('GET', '/account/balance')), flush=True)
check_id, check = run('rig-check', '/animations/rig-check', {'input': a.input})
print('rig-check output:', json.dumps(check.get('output')), flush=True)
rig_id, _ = run('rig', '/animations/rig', {'input': a.input, 'model': a.rig_model, 'rig_type': 'biped', 'spec': a.spec, 'out_format': 'glb'})
run('retarget', '/animations/retarget', {'input': rig_id, 'animations': a.animations.split(','), 'out_format': 'glb', 'animate_in_place': True})
print('balance after:', json.dumps(call('GET', '/account/balance')), flush=True)
