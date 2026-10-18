"""Single-image TRELLIS.2 experiment. Does not modify or deploy the game.
Run with the workspace tools Python; see docs/experiments/future-sanada/README.md.
"""
from pathlib import Path
import os
# Use the environment's existing system CA trust. Never disable TLS verification.
import modal
if modal.is_local():
    import truststore
    truststore.inject_into_ssl()
for upper, lower in (("MODAL_TOKEN_ID", "modal_token_id"), ("MODAL_TOKEN_SECRET", "modal_token_secret")):
    if not os.environ.get(upper) and os.environ.get(lower):
        os.environ[upper] = os.environ[lower]
os.environ.setdefault("MODAL_SERVER_URL", "https://api.modal.com")

TRELLIS_COMMIT = "75fbf0183001ed9876c8dbb35de6b68552ee08bd"
app = modal.App("yukimura-trellis2-study")
cache = modal.Volume.from_name("yukimura-trellis2-cache", create_if_missing=True)
hf_secrets = [] if os.environ.get('TRELLIS_ENVIRONMENT_CHECK_ONLY') == '1' else [
    modal.Secret.from_name(os.environ.get('TRELLIS_HF_SECRET', 'trellis-huggingface'),
                          required_keys=['HF_TOKEN'])
]
GPU_CHECK = """python - <<'CHECK'
import torch, xformers, cumesh, flex_gemm, o_voxel
import nvdiffrast.torch as dr
from trellis2.pipelines import Trellis2ImageTo3DPipeline
v = torch.tensor([[-1.,-1.,0.],[1.,-1.,0.],[0.,1.,0.]], device='cuda')
f = torch.tensor([[0,1,2]], dtype=torch.int32, device='cuda')
m = cumesh.CuMesh()
m.init(v,f)
assert m.num_vertices == 3 and m.num_faces == 1
clip = torch.cat([v,torch.ones((3,1),device='cuda')],dim=1)[None]
rast,_ = dr.rasterize(dr.RasterizeCudaContext(),clip,f,resolution=[16,16])
assert rast.shape == (1,16,16,4)
torch.cuda.synchronize()
print('TRELLIS.2 GPU imports, CuMesh and rasterization OK:', torch.cuda.get_device_name())
CHECK"""
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.11")
    .apt_install("git", "build-essential", "cmake", "ninja-build", "libgl1", "libglib2.0-0", "libjpeg-dev")
    .env({"TORCH_CUDA_ARCH_LIST": "9.0", "MAX_JOBS": "2", "ATTN_BACKEND": "xformers",
          "OPENCV_IO_ENABLE_OPENEXR": "1", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
          "HF_HOME": "/cache/huggingface", "PYTHONPATH": "/opt/TRELLIS.2"})
    .pip_install("torch==2.6.0", "torchvision==0.21.0", "xformers==0.0.29.post3",
                 index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("numpy<2", "pillow", "imageio", "imageio-ffmpeg", "tqdm", "easydict",
                 "opencv-python-headless<4.12", "ninja", "trimesh", "transformers==4.57.3",
                 "accelerate", "safetensors", "huggingface-hub<1", "scipy", "tensorboard", "pandas",
                 "lpips", "zstandard", "kornia", "timm", "fast-simplification")
    .pip_install("wheel==0.45.1", "setuptools==75.8.0")
    .run_commands(f"git clone https://github.com/microsoft/TRELLIS.2.git /opt/TRELLIS.2 && cd /opt/TRELLIS.2 && git checkout {TRELLIS_COMMIT} && git submodule update --init --recursive")
    .run_commands("pip install git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8")
    .apt_install("clang")
    .run_commands("git clone -b v0.4.0 https://github.com/NVlabs/nvdiffrast.git /opt/nvdiffrast && pip install /opt/nvdiffrast --no-build-isolation")
    .run_commands("git clone -b renderutils https://github.com/JeffreyXiang/nvdiffrec.git /opt/nvdiffrec && pip install /opt/nvdiffrec --no-build-isolation")
    .run_commands("git clone https://github.com/JeffreyXiang/CuMesh.git /opt/CuMesh && cd /opt/CuMesh && git checkout 12289e1062f0603f2f0d0771b02e1395d247f26f && git submodule update --init --recursive && pip install . --no-build-isolation")
    .run_commands("git clone https://github.com/JeffreyXiang/FlexGEMM.git /opt/FlexGEMM && cd /opt/FlexGEMM && git checkout 6dd94a859c26ee8246888502eada3dd8ad85532e && git submodule update --init --recursive && pip install . --no-build-isolation")
    .run_commands("pip install /opt/TRELLIS.2/o-voxel --no-build-isolation --no-deps")
    .run_commands(GPU_CHECK, gpu="H100")
)

@app.function(image=modal.Image.debian_slim(python_version='3.11').pip_install(
                  'huggingface-hub==0.36.0', 'pillow'),
              secrets=hf_secrets, timeout=120, max_containers=1, retries=0)
def check_access(input_png: bytes) -> dict:
    """Check gated access on CPU before allocating the inference GPU."""
    import io
    from PIL import Image
    from huggingface_hub import HfApi, get_hf_file_metadata, hf_hub_url
    from huggingface_hub.errors import HfHubHTTPError
    picture = Image.open(io.BytesIO(input_png))
    if picture.mode != 'RGBA':
        raise ValueError('This study requires a transparent RGBA reference.')
    low, high = picture.getchannel('A').getextrema()
    if low >= 255 or high <= 204:
        raise ValueError('Reference needs both transparent background and visible foreground.')
    repo = 'facebook/dinov3-vitl16-pretrain-lvd1689m'
    token = os.environ['HF_TOKEN']
    try:
        info = HfApi().model_info(repo, token=token)
        weight = next(f.rfilename for f in info.siblings if f.rfilename.endswith('.safetensors'))
        for filename in ['config.json', weight]:
            get_hf_file_metadata(hf_hub_url(repo, filename), token=token)
    except HfHubHTTPError as error:
        raise RuntimeError(
            f'Hugging Face access check failed for {repo} (HTTP {error.response.status_code}). '
            'Approve access with the token owner account and allow this model in token permissions. '
            'GPU inference was not started.'
        ) from None
    return {'dinov3_access': 'passed', 'input_alpha': 'passed', 'background_removal': 'provided alpha'}


@app.function(image=image, gpu="H100", cpu=4, memory=49152, timeout=1200,
              startup_timeout=1200, max_containers=1, scaledown_window=2,
              volumes={"/cache": cache}, secrets=hf_secrets, retries=0)
def generate(input_png: bytes, seed: int = 1615, resolution: str = "1024_cascade") -> dict:
    import io, json, time, hashlib
    import torch
    from PIL import Image
    from trellis2.pipelines import Trellis2ImageTo3DPipeline
    import o_voxel
    started = time.monotonic()
    report = {"trellis_commit": TRELLIS_COMMIT, "model": "microsoft/TRELLIS.2-4B", "seed": seed,
              "pipeline": resolution, "gpu": torch.cuda.get_device_name(), "torch": torch.__version__,
              "input_sha256": hashlib.sha256(input_png).hexdigest(), "status": "running"}
    print("GPU:", report["gpu"], "pipeline:", resolution, flush=True)
    # The input already has alpha. Configure a null remover instead of loading
    # the unused, separately gated RMBG-2.0 model. The pinned pipeline supports
    # rembg_model=None and uses the input's alpha in preprocess_image.
    import tempfile
    from huggingface_hub import hf_hub_download
    from trellis2.pipelines import rembg
    repo = 'microsoft/TRELLIS.2-4B'
    config = json.loads(Path(hf_hub_download(repo, 'pipeline.json')).read_text())
    for key, path in config['args']['models'].items():
        if path.startswith('ckpts/'):
            config['args']['models'][key] = f'{repo}/{path}'
    config['args']['rembg_model'] = {'name': 'ProvidedAlpha', 'args': {}}
    rembg.ProvidedAlpha = lambda: None
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, 'pipeline.json').write_text(json.dumps(config))
        pipeline = Trellis2ImageTo3DPipeline.from_pretrained(directory)
    report['background_removal'] = 'provided alpha; RMBG-2.0 not loaded'
    pipeline.cuda()
    report["load_seconds"] = time.monotonic() - started
    inference_started = time.monotonic()
    mesh = pipeline.run(Image.open(io.BytesIO(input_png)), seed=seed, pipeline_type=resolution)[0]
    torch.cuda.synchronize()
    report["inference_seconds"] = time.monotonic() - inference_started
    report["source_vertices"] = int(mesh.vertices.shape[0])
    report["source_triangles"] = int(mesh.faces.shape[0])
    print("Generated", report["source_triangles"], "triangles", flush=True)
    export_started = time.monotonic()
    mesh.simplify(16777216)
    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices, faces=mesh.faces, attr_volume=mesh.attrs, coords=mesh.coords,
        attr_layout=mesh.layout, voxel_size=mesh.voxel_size,
        aabb=[[-.5,-.5,-.5],[.5,.5,.5]], decimation_target=150000,
        texture_size=2048, remesh=True, remesh_band=1, remesh_project=0, verbose=True)
    # Standard embedded PNG textures for reliable Blender/browser import.
    output = glb.export(file_type="glb")
    report.update({"status": "completed", "export_seconds": time.monotonic()-export_started,
                   "elapsed_seconds": time.monotonic()-started, "export_bytes": len(output),
                   "export_sha256": hashlib.sha256(output).hexdigest(), "texture_size": 2048,
                   "decimation_target": 150000, "peak_gpu_gib": torch.cuda.max_memory_allocated()/2**30})
    directory = Path('/cache/results/future-sanada')
    directory.mkdir(parents=True, exist_ok=True)
    (directory/'future-sanada.glb').write_bytes(output)
    (directory/'generation.json').write_text(json.dumps(report, indent=2)+'\n')
    cache.commit()
    print(json.dumps(report), flush=True)
    return {"future-sanada.glb": output, "generation.json": (json.dumps(report,indent=2)+'\n').encode()}

@app.local_entrypoint()
def main(input: str = "docs/experiments/future-sanada/reference.png",
         output: str = "docs/experiments/future-sanada", seed: int = 1615,
         resolution: str = "1024_cascade", build_only: bool = False):
    if build_only:
        print("TRELLIS.2 image build completed; inference intentionally not started.")
        return
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    print('CPU access check:', check_access.remote(Path(input).read_bytes()))
    for name, data in generate.remote(Path(input).read_bytes(), seed, resolution).items():
        (target/name).write_bytes(data)
        print("Saved", target/name, len(data), "bytes")
