"""Generate or edit one image through OpenRouter and log it.

Every call appends {file, model, prompt, references, cost} to prompts.json next to the output, so
each image in the part pipeline can be traced and re-made. The key is read from the environment
variable named by --key-env (default `or_key`); it is never written anywhere.

  python tools/part_pipeline/gen_image.py --model openai/gpt-image-2.5-flare \
      --ref docs/experiments/future-sanada/reference.png --prompt-file prompt.txt \
      --output docs/experiments/future-sanada/part-pipeline/images/front-gpt.png
"""
from pathlib import Path
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

p = argparse.ArgumentParser()
p.add_argument('--model', required=True)
p.add_argument('--prompt'); p.add_argument('--prompt-file')
p.add_argument('--ref', action='append', default=[], help='Reference image(s), in order')
p.add_argument('--output', required=True)
p.add_argument('--aspect', default='2:3', help='Aspect ratio hint (models that support image_config)')
p.add_argument('--size', default='2K', help='Image size hint (1K, 2K, 4K) for models that support it')
p.add_argument('--quality', default='high', help='Images-endpoint models: auto, low, medium, high')
p.add_argument('--key-env', default='or_key')
a = p.parse_args()
prompt = a.prompt if a.prompt else Path(a.prompt_file).read_text().strip()
key = os.environ[a.key_env]

refs = []
for r in a.ref:
    mime = mimetypes.guess_type(r)[0] or 'image/png'
    refs.append({'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,' + base64.b64encode(Path(r).read_bytes()).decode()}})

def post(path, body):
    req = urllib.request.Request(f'https://openrouter.ai/api/v1/{path}', data=json.dumps(body).encode(),
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp: return json.load(resp), None
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code}: {e.read().decode()[:2000]}'

t0 = time.time()
# Chat models (Gemini) take references in the message; pure image models (gpt-image, FLUX) only
# accept the dedicated images endpoint, with references in input_references.
out, err = post('chat/completions', {'model': a.model, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}] + refs}],
                                     'modalities': ['image', 'text'], 'image_config': {'aspect_ratio': a.aspect, 'image_size': a.size},
                                     'usage': {'include': True}})
if out is not None:
    msg = out['choices'][0]['message']; reply = msg.get('content') or ''
    images = msg.get('images') or []
    if not images: sys.exit('no image returned: ' + json.dumps(msg)[:2000])
    data = base64.b64decode(images[0]['image_url']['url'].split(',', 1)[1])
elif '/api/v1/images' in err:
    body = {'model': a.model, 'prompt': prompt, 'n': 1, 'quality': a.quality, 'aspect_ratio': a.aspect, 'output_format': 'png'}
    if refs: body['input_references'] = refs
    out, err = post('images', body)
    if out is None: sys.exit(err)
    reply = ''; data = base64.b64decode(out['data'][0]['b64_json'])
else:
    sys.exit(err)
dest = Path(a.output); dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(data)
cost = (out.get('usage') or {}).get('cost')
log_path = dest.parent / 'prompts.json'
log = json.loads(log_path.read_text()) if log_path.exists() else []
log = [e for e in log if e['file'] != dest.name] + [{'file': dest.name, 'model': a.model, 'prompt': prompt, 'references': [Path(r).name for r in a.ref],
                                                     'aspect': a.aspect, 'size': a.size, 'cost_usd': cost, 'seconds': round(time.time() - t0, 1),
                                                     'text_reply': reply[:500]}]
log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'file': str(dest), 'cost_usd': cost, 'seconds': round(time.time() - t0, 1)}))
