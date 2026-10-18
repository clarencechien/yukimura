"""Official TRELLIS (first generation) fallback; no DINOv3 or HF token required.
Run via tools/run_trellis1.py. Outputs remain separate from TRELLIS.2.
"""
from pathlib import Path
import modal

COMMIT = '442aa1e1afb9014e80681d3bf604e8d728a86ee7'
DINO_COMMIT = '7764ea0f912e53c92e82eb78a2a1631e92725fc8'
app = modal.App('yukimura-trellis1-study')
cache = modal.Volume.from_name('yukimura-trellis2-cache')
# Reuse the validated CUDA/PyTorch build; its reproducible definition is in
# trellis_modal.py (tools/run_trellis.py --build-only). No gated model is in it.
image = (modal.Image.from_id('im-CWPfod9BzDeCjqD07JU8Ui')
    .env({'PYTHONPATH': '/opt/TRELLIS1', 'ATTN_BACKEND': 'xformers',
          'SPCONV_ALGO': 'native', 'SPARSE_BACKEND': 'spconv', 'TORCH_HOME': '/cache/torch'})
    .pip_install('spconv-cu120==2.3.6', 'rembg==2.0.67', 'onnxruntime',
                 'xatlas==0.0.11', 'pyvista==0.46.3', 'pymeshfix==0.17.2', 'igraph==0.11.9')
    .run_commands('pip install kaolin==0.18.0 -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.6.0_cu124.html')
    .run_commands(f'git clone https://github.com/microsoft/TRELLIS.git /opt/TRELLIS1 && cd /opt/TRELLIS1 && git checkout {COMMIT} && git submodule update --init --recursive')
    .run_commands(f"""python - <<'PIN'
from pathlib import Path
p = Path('/opt/TRELLIS1/trellis/pipelines/trellis_image_to_3d.py')
s = p.read_text()
assert s.count("'facebookresearch/dinov2'") == 1
p.write_text(s.replace("'facebookresearch/dinov2'", "'facebookresearch/dinov2:{DINO_COMMIT}'"))
PIN""")
    .run_commands('git clone https://github.com/autonomousvision/mip-splatting.git /opt/mip-splatting && cd /opt/mip-splatting && git checkout dda02ab5ecf45d6edb8c540d9bb65c7e451345a9 && pip install submodules/diff-gaussian-rasterization --no-build-isolation')
    .pip_install('open3d==0.19.0')
)

@app.function(image=image, cpu=2, timeout=180, retries=0,
              volumes={'/cache': cache})
def preflight():
    import json, urllib.request
    from huggingface_hub import hf_hub_download, get_hf_file_metadata, hf_hub_url
    repo = 'microsoft/TRELLIS-image-large'
    config = json.loads(Path(hf_hub_download(repo, 'pipeline.json', token=False)).read_text())
    assert config['args']['image_cond_model'] == 'dinov2_vitl14_reg'
    for stem in config['args']['models'].values():
        for suffix in ['.json', '.safetensors']:
            get_hf_file_metadata(hf_hub_url(repo, stem + suffix), token=False)
    url = 'https://dl.fbaipublicfiles.com/dinov2/dinov2_vitl14/dinov2_vitl14_reg4_pretrain.pth'
    with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as r:
        assert r.status == 200
    print('Official TRELLIS and DINOv2 weights accessible without token.', flush=True)
    # Validate imports on CPU before starting the inference GPU.
    from trellis.pipelines import TrellisImageTo3DPipeline
    from trellis.utils import postprocessing_utils
    return {'checkpoint_access': 'passed without HF token', 'dinov2_access': 'passed', 'imports': 'passed'}

@app.function(image=image, gpu='H100', cpu=4, memory=49152,
              timeout=1200, startup_timeout=1200, max_containers=1,
              scaledown_window=2, retries=0, volumes={'/cache': cache})
def generate(input_png: bytes, seed: int = 1615):
    import io, json, time, hashlib
    import numpy as np
    import torch
    from PIL import Image
    from trellis.pipelines import TrellisImageTo3DPipeline
    from trellis.utils import postprocessing_utils
    started = time.monotonic()
    report = {'engine': 'TRELLIS first generation', 'model': 'microsoft/TRELLIS-image-large',
              'trellis_commit': COMMIT, 'dinov2_commit': DINO_COMMIT,
              'seed': seed, 'gpu': torch.cuda.get_device_name(),
              'input_sha256': hashlib.sha256(input_png).hexdigest(),
              'material': 'baked base color; not TRELLIS.2 metallic/roughness prediction'}
    print('GPU:', report['gpu'], 'loading official TRELLIS + DINOv2', flush=True)
    pipeline = TrellisImageTo3DPipeline.from_pretrained(report['model'])
    pipeline.cuda()
    report['load_seconds'] = time.monotonic()-started
    t = time.monotonic()
    outputs = pipeline.run(Image.open(io.BytesIO(input_png)), seed=seed, formats=['mesh', 'gaussian'])
    torch.cuda.synchronize()
    report['inference_seconds'] = time.monotonic()-t
    mesh, gaussians = outputs['mesh'][0], outputs['gaussian'][0]
    report['source_triangles'] = int(mesh.faces.shape[0])
    report['source_vertices'] = int(mesh.vertices.shape[0])
    directory = Path('/cache/results/future-sanada-trellis1')
    directory.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(directory/'mesh.npz', vertices=mesh.vertices.cpu().numpy(), faces=mesh.faces.cpu().numpy())
    gaussians.save_ply(str(directory/'gaussians.ply'))
    (directory/'generation-partial.json').write_text(json.dumps(report, indent=2))
    cache.commit()  # Preserve generation if UV/texture export later fails.
    print('Geometry saved:', report['source_triangles'], 'triangles', flush=True)
    t = time.monotonic()
    ratio = max(0, 1-150000/report['source_triangles'])
    glb = postprocessing_utils.to_glb(gaussians, mesh, simplify=ratio, fill_holes=False, texture_size=2048)
    data = glb.export(file_type='glb')
    report.update(status='completed', export_seconds=time.monotonic()-t,
                  elapsed_seconds=time.monotonic()-started, texture_size=2048,
                  simplification_ratio=ratio, fill_holes=False, export_bytes=len(data),
                  export_sha256=hashlib.sha256(data).hexdigest(),
                  peak_gpu_gib=torch.cuda.max_memory_allocated()/2**30)
    (directory/'future-sanada.glb').write_bytes(data)
    (directory/'generation.json').write_text(json.dumps(report,indent=2)+'\n')
    cache.commit()
    print(json.dumps(report),flush=True)
    # Return small metadata; artifacts are already committed to the Volume.
    # Download through the supported Volume API instead of duplicating a large
    # GLB in Modal's transient function-result blob store.
    return report

@app.local_entrypoint()
def main(build_only: bool = False, download_only: bool = False):
    if build_only:
        print('TRELLIS1 image built; inference skipped.')
        return
    target = Path('docs/experiments/future-sanada/trellis1'); target.mkdir(parents=True,exist_ok=True)
    if not download_only:
        print('CPU preflight:', preflight.remote())
        reference = Path('docs/experiments/future-sanada/reference.png').read_bytes()
        print('Generation completed:', generate.remote(reference))
    import hashlib, json
    for name in ['generation.json', 'future-sanada.glb']:
        temporary = target/(name+'.part')
        try:
            with temporary.open('wb') as output:
                for chunk in cache.read_file('results/future-sanada-trellis1/'+name):
                    output.write(chunk)
            if name.endswith('.glb'):
                report=json.loads((target/'generation.json').read_text())
                assert hashlib.sha256(temporary.read_bytes()).hexdigest()==report['export_sha256']
            temporary.replace(target/name)
        finally:
            temporary.unlink(missing_ok=True)
        print('Saved',target/name,(target/name).stat().st_size,'bytes')
