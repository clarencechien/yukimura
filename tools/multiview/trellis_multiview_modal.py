"""TRELLIS.2 1536 cascade from a turnaround (front / back / left, right = mirrored left), on Modal H100.

TRELLIS.2 only takes one image. Following the multi-view sampler of the ComfyUI-Trellis2 wrapper
(visualbruno, MIT), every flow model is wrapped so that, for the positive conditioning, it runs once per
view (each conditioned on that view's DINOv3 features alone) and blends the predicted velocities by voxel
position: the front of the volume follows the front image, the back the back image, the sides the side
images, with soft (softmax) transitions. The negative (empty) conditioning runs once as usual, so CFG is
unchanged. Nothing sees the views jointly; it is region-wise guidance, not reconstruction.

Voxel axes (measured on body-v2: exported GLB = (x, z, -y) of the voxel space): z up, front = -y,
the figure's left = +x. Sparse coords are [batch, x, y, z]; the dense structure latent is (B, C, x, y, z).

  python tools/run_trellis.py --multiview --modes single,multi --seeds 7
"""
from pathlib import Path
import os
import modal

app = modal.App('yukimura-trellis2-multiview')
cache = modal.Volume.from_name('yukimura-trellis2-cache')
image = modal.Image.from_id('im-CWPfod9BzDeCjqD07JU8Ui')      # the verified TRELLIS.2 CUDA image (body v2)
secrets = [] if os.environ.get('TRELLIS_ENVIRONMENT_CHECK_ONLY') == '1' else [
    modal.Secret.from_name(os.environ.get('TRELLIS_HF_SECRET', 'trellis-huggingface'), required_keys=['HF_TOKEN'])]
ROOT = 'results/future-sanada-multiview'
INPUTS = 'docs/experiments/future-sanada/multiview/inputs'
DIRECTIONS = {'front': (0, -1), 'back': (0, 1), 'left': (1, 0), 'right': (-1, 0)}   # (x, y) in voxel space


@app.function(image=image, gpu='H100', cpu=4, memory=49152, timeout=3600, startup_timeout=1200, max_containers=4,
              scaledown_window=2, retries=0, volumes={'/cache': cache}, secrets=secrets)
def generate(views: dict, mode: str, seed: int = 7, temperature: float = 2.0, mirror_right: bool = True):
    import io, json, time, hashlib, tempfile
    import torch, o_voxel
    from PIL import Image, ImageOps
    from huggingface_hub import hf_hub_download
    from trellis2.pipelines import Trellis2ImageTo3DPipeline, rembg
    started = time.monotonic(); out = Path('/cache') / ROOT / f'{mode}-seed-{seed}'; out.mkdir(parents=True, exist_ok=True)
    repo = 'microsoft/TRELLIS.2-4B'; config = json.loads(Path(hf_hub_download(repo, 'pipeline.json')).read_text())
    for key, path in config['args']['models'].items():
        if path.startswith('ckpts/'): config['args']['models'][key] = f'{repo}/{path}'
    config['args']['rembg_model'] = {'name': 'ProvidedAlpha', 'args': {}}; rembg.ProvidedAlpha = lambda: None
    with tempfile.TemporaryDirectory() as temp:
        Path(temp, 'pipeline.json').write_text(json.dumps(config)); pipeline = Trellis2ImageTo3DPipeline.from_pretrained(temp)
    pipeline.cuda()
    used = ['front'] if mode == 'single' else list(views)
    pre = {v: pipeline.preprocess_image(Image.open(io.BytesIO(views[v]))) for v in used}
    if mode != 'single' and mirror_right and 'left' in pre and 'right' not in pre: pre['right'] = ImageOps.mirror(pre['left'])
    report = {'model': repo, 'pipeline': '1536_cascade', 'mode': mode, 'seed': seed, 'views': list(pre),
              'temperature': temperature if mode != 'single' else None, 'mirror_right': mirror_right and mode != 'single',
              'inputs_sha256': {v: hashlib.sha256(views[v]).hexdigest() for v in used}, 'gpu': torch.cuda.get_device_name()}
    if mode != 'single':
        conds = {r: {v: pipeline.get_cond([im], r) for v, im in pre.items()} for r in (512, 1024)}
        front = {r: conds[r]['front'] for r in conds}
        by_id = {id(front[r]['cond']): {v: conds[r][v]['cond'] for v in pre} for r in conds}
        axis_log = []

        def weights(x, names):
            if hasattr(x, 'coords'):
                c = x.coords[:, 1:4].float(); lo, hi = c.min(0).values, c.max(0).values
                n = (c - (lo + hi) / 2) / ((hi - lo) / 2).clamp(min=1)
                if len(axis_log) < 3: axis_log.append([int(v) for v in (hi - lo)])
                s = torch.stack([n[:, 0] * DIRECTIONS[v][0] + n[:, 1] * DIRECTIONS[v][1] for v in names], 1)
                return torch.softmax(s * temperature, 1)                      # (N, views)
            X, Y = x.shape[2], x.shape[3]
            gx = torch.linspace(-1, 1, X, device=x.device)[:, None, None]; gy = torch.linspace(-1, 1, Y, device=x.device)[None, :, None]
            s = torch.stack([(gx * DIRECTIONS[v][0] + gy * DIRECTIONS[v][1]).expand(X, Y, x.shape[4]) for v in names], 0)
            return torch.softmax(s * temperature, 0)                          # (views, x, y, z)

        class MultiView(torch.nn.Module):
            def __init__(self, inner): super().__init__(); self.inner = inner
            def __getattr__(self, name):
                try: return super().__getattr__(name)
                except AttributeError: return getattr(self._modules['inner'], name)
            def forward(self, x, t, cond, **kw):
                per_view = by_id.get(id(cond))
                if per_view is None: return self.inner(x, t, cond, **kw)          # negative conditioning
                names = list(per_view); w = weights(x, names); acc = None
                for i, v in enumerate(names):
                    p = self.inner(x, t, per_view[v], **kw); f = p.feats if hasattr(p, 'feats') else p
                    wi = w[:, i:i + 1] if hasattr(x, 'coords') else w[i][None, None]
                    acc = f * wi if acc is None else acc + f * wi
                return p.replace(acc) if hasattr(p, 'feats') else acc

        for k in [k for k in pipeline.models.keys() if 'flow_model' in k]: pipeline.models[k] = MultiView(pipeline.models[k])
        pipeline.get_cond = lambda image, resolution, include_neg_cond=True: front[resolution]
    t = time.monotonic()
    outputs, latent = pipeline.run(pre['front'], seed=seed, pipeline_type='1536_cascade', return_latent=True,
                                   max_num_tokens=65536, preprocess_image=False)
    report.update(actual_resolution=int(latent[2]), inference_seconds=round(time.monotonic() - t, 1))
    if mode != 'single': report['sparse_extent_xyz'] = axis_log      # sanity: z should be the tallest
    mesh = outputs[0]; del outputs, latent
    for v, im in pre.items(): im.save(out / f'input-{v}.png')
    t = time.monotonic()
    glb = o_voxel.postprocess.to_glb(vertices=mesh.vertices, faces=mesh.faces, attr_volume=mesh.attrs, coords=mesh.coords,
                                     attr_layout=mesh.layout, voxel_size=float(mesh.voxel_size), aabb=[[-.5, -.5, -.5], [.5, .5, .5]],
                                     decimation_target=600000, texture_size=4096, remesh=True, remesh_band=1, remesh_project=0, verbose=False)
    glb.export(str(out / 'body-remesh.glb'))
    report.update(export_seconds=round(time.monotonic() - t, 1), source_triangles=int(mesh.faces.shape[0]),
                  invocation_seconds=round(time.monotonic() - started, 1), status='completed')
    (out / 'generation.json').write_text(json.dumps(report, indent=2) + '\n'); cache.commit()
    return report


@app.local_entrypoint()
def main(modes: str = 'single,multi', seeds: str = '7', output: str = '.tmp/multiview', temperature: float = 2.0, download_only: bool = False):
    views = {v: Path(INPUTS, f'{v}.png').read_bytes() for v in ('front', 'back', 'left')}
    jobs = [(m, int(s)) for m in modes.split(',') for s in seeds.split(',')]
    if not download_only:
        calls = [generate.spawn(views, m, s, temperature) for m, s in jobs]
        for c in calls: print('Completed:', c.get(), flush=True)
    for m, s in jobs:
        d = Path(output, f'{m}-seed-{s}'); d.mkdir(parents=True, exist_ok=True)
        for e in cache.listdir(f'{ROOT}/{m}-seed-{s}'):
            (d / Path(e.path).name).write_bytes(b''.join(cache.read_file(e.path)))
        print('downloaded', d, sorted(p.name for p in d.iterdir()), flush=True)
