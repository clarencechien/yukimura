"""Stage 3 of the part pipeline: TRELLIS.2 1536 cascade, one armour part per call.

Same verified CUDA image and caching as the body-v2 study: the source mesh and voxel materials
are committed to the volume before any export, so an export can be redone without inference.
Inputs are the RGBA cut-outs from cutout.py (alpha provided; no matting network is loaded).

  python tools/run_trellis.py --parts-study --names helmet,sode --seeds 1615
"""
from pathlib import Path
import os
import modal

app = modal.App('yukimura-trellis2-parts')
cache = modal.Volume.from_name('yukimura-trellis2-cache')
image = modal.Image.from_id('im-CWPfod9BzDeCjqD07JU8Ui')
secrets = [] if os.environ.get('TRELLIS_ENVIRONMENT_CHECK_ONLY') == '1' else [modal.Secret.from_name(os.environ.get('TRELLIS_HF_SECRET', 'trellis-huggingface'), required_keys=['HF_TOKEN'])]
ROOT = 'results/future-sanada-parts'
COMMIT = '75fbf0183001ed9876c8dbb35de6b68552ee08bd'
# high: open surface straight from the voxels; closed: remeshed watertight (fills the pin holes the
# open export leaves in thin plates).
EXPORTS = [('high.glb', 300000, 2048, False), ('closed.glb', 300000, 2048, True)]


@app.function(image=image, gpu='H100', cpu=4, memory=49152, timeout=1500, startup_timeout=1200, max_containers=4, scaledown_window=2, retries=0, volumes={'/cache': cache}, secrets=secrets)
def generate(name: str, data: bytes, seed: int = 1615, export_only: bool = False):
    import io, json, time, hashlib, tempfile
    import numpy as np
    import torch
    import o_voxel
    from PIL import Image
    from huggingface_hub import hf_hub_download
    from trellis2.pipelines import Trellis2ImageTo3DPipeline, rembg
    started = time.monotonic(); directory = Path('/cache') / ROOT / name / f'seed-{seed}'; directory.mkdir(parents=True, exist_ok=True)

    def describe(p):
        h = hashlib.sha256()
        with p.open('rb') as f:
            while chunk := f.read(1024 * 1024): h.update(chunk)
        return {'name': p.name, 'bytes': p.stat().st_size, 'sha256': h.hexdigest()}

    im = Image.open(io.BytesIO(data)); assert im.mode == 'RGBA', 'cut-out must carry alpha'
    if not export_only:
        report = {'model': 'microsoft/TRELLIS.2-4B', 'trellis_commit': COMMIT, 'part': name, 'input_sha256': hashlib.sha256(data).hexdigest(),
                  'pipeline': '1536_cascade', 'seed': seed, 'max_num_tokens': 65536, 'gpu': torch.cuda.get_device_name(), 'status': 'running'}
        repo = report['model']; config = json.loads(Path(hf_hub_download(repo, 'pipeline.json')).read_text())
        for key, path in config['args']['models'].items():
            if path.startswith('ckpts/'): config['args']['models'][key] = f'{repo}/{path}'
        config['args']['rembg_model'] = {'name': 'ProvidedAlpha', 'args': {}}; rembg.ProvidedAlpha = lambda: None
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, 'pipeline.json').write_text(json.dumps(config)); pipeline = Trellis2ImageTo3DPipeline.from_pretrained(temp)
        pipeline.cuda(); report['load_seconds'] = time.monotonic() - started; t = time.monotonic()
        outputs, latent = pipeline.run(im, seed=seed, pipeline_type='1536_cascade', return_latent=True, max_num_tokens=65536)
        report['actual_resolution'] = int(latent[2]); del latent; mesh = outputs[0]; del outputs
        torch.cuda.synchronize(); report.update(inference_seconds=time.monotonic() - t, source_vertices=int(mesh.vertices.shape[0]), source_triangles=int(mesh.faces.shape[0]))
        vertices, faces, attrs, coords, layout, voxel_size = mesh.vertices, mesh.faces, mesh.attrs, mesh.coords, mesh.layout, float(mesh.voxel_size)
        del pipeline; torch.cuda.empty_cache()
        np.savez_compressed(directory / 'source-geometry.npz', vertices=vertices.cpu().numpy(), faces=faces.cpu().numpy())
        np.savez_compressed(directory / 'source-attributes.npz', attrs=attrs.cpu().numpy(), coords=coords.cpu().numpy())
        (directory / 'source-metadata.json').write_text(json.dumps({'layout': {k: [v.start, v.stop, v.step] for k, v in layout.items()}, 'voxel_size': voxel_size}, indent=2) + '\n')
        report['source_files'] = [describe(directory / n) for n in ['source-geometry.npz', 'source-attributes.npz', 'source-metadata.json']]
        report['status'] = 'source_cached'; report['exports'] = []
        (directory / 'generation.json').write_text(json.dumps(report, indent=2) + '\n'); cache.commit()
    else:
        report = json.loads((directory / 'generation.json').read_text())
        if hashlib.sha256(data).hexdigest() != report['input_sha256']: raise ValueError('Cached source belongs to a different input')
        source = np.load(directory / 'source-geometry.npz'); material = np.load(directory / 'source-attributes.npz')
        vertices = torch.from_numpy(source['vertices']).cuda(); faces = torch.from_numpy(source['faces']).cuda()
        attrs = torch.from_numpy(material['attrs']).cuda(); coords = torch.from_numpy(material['coords']).cuda()
        metadata = json.loads((directory / 'source-metadata.json').read_text())
        layout = {k: slice(*v) for k, v in metadata['layout'].items()}; voxel_size = metadata['voxel_size']
    for suffix, target, size, closed in EXPORTS:
        out = f'{name}-{suffix}'
        if any(e['name'] == out for e in report['exports']) and (directory / out).exists(): continue
        t = time.monotonic()
        glb = o_voxel.postprocess.to_glb(vertices=vertices, faces=faces, attr_volume=attrs, coords=coords, attr_layout=layout, voxel_size=voxel_size,
                                         aabb=[[-.5, -.5, -.5], [.5, .5, .5]], decimation_target=target, texture_size=size, remesh=closed,
                                         remesh_band=1, remesh_project=0, verbose=False)
        glb.export(str(directory / out)); del glb; torch.cuda.empty_cache()
        report['exports'].append({**describe(directory / out), 'target_triangles': target, 'texture_size': size, 'remesh': closed, 'export_seconds': time.monotonic() - t})
    report.update(status='completed', invocation_seconds=time.monotonic() - started, peak_pytorch_allocated_gib=torch.cuda.max_memory_allocated() / 2 ** 30)
    (directory / 'generation.json').write_text(json.dumps(report, indent=2) + '\n'); cache.commit()
    return {k: report[k] for k in ('part', 'seed', 'status', 'source_triangles', 'invocation_seconds')}


@app.local_entrypoint()
def main(names: str, seeds: str = '1615', inputs: str = 'docs/experiments/future-sanada/part-pipeline/stage3/inputs',
         output: str = '.tmp/parts', download_only: bool = False, export_only: bool = False):
    import json, hashlib
    names = names.split(','); seeds = [int(s) for s in seeds.split(',')]
    if not download_only:
        calls = [(n, s, generate.spawn(n, Path(inputs, f'{n}.png').read_bytes(), s, export_only)) for n in names for s in seeds]
        for n, s, call in calls:
            try: print('Completed:', call.get(), flush=True)
            except Exception as e: print('FAILED:', n, s, repr(e)[:500], flush=True)
    for n in names:
        for s in seeds:
            remote = f'{ROOT}/{n}/seed-{s}'; target = Path(output) / n / f'seed-{s}'; target.mkdir(parents=True, exist_ok=True)
            try:
                report = json.loads(b''.join(cache.read_file(remote + '/generation.json')))
            except Exception as e:
                print('missing', remote, repr(e)[:200]); continue
            (target / 'generation.json').write_text(json.dumps(report, indent=2) + '\n')
            for artifact in report.get('exports', []):
                data = b''.join(cache.read_file(remote + '/' + artifact['name']))
                if hashlib.sha256(data).hexdigest() != artifact['sha256']: raise ValueError('SHA256 mismatch: ' + artifact['name'])
                (target / artifact['name']).write_bytes(data); print('Saved', target / artifact['name'], len(data), flush=True)
