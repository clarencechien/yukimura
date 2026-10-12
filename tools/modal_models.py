"""Optional remote generation. pip install modal; modal run tools/modal_models.py.
Uses MODAL_TOKEN_ID and MODAL_TOKEN_SECRET from secure environment only.
"""
from pathlib import Path
import os
for upper, lower in [("MODAL_TOKEN_ID", "modal_token_id"), ("MODAL_TOKEN_SECRET", "modal_token_secret")]:
 if not os.environ.get(upper) and os.environ.get(lower):
  os.environ[upper] = os.environ[lower]
import modal
app=modal.App('yukimura-model-builder')
image=(modal.Image.debian_slim(python_version='3.11').apt_install('blender')
       .add_local_dir(Path(__file__).resolve().parent,'/opt/yukimura/tools',ignore=['__pycache__']))
@app.function(image=image,timeout=1800,cpu=2,memory=8192)
def build():
 import subprocess,os
 from pathlib import Path
 subprocess.run(['blender','--background','--threads','2','--python-exit-code','1','--python','/opt/yukimura/tools/build_models.py'],env={**os.environ,'MODEL_OUTPUT':'/tmp/models','MODEL_SOURCE':'/tmp/samurai-kit.blend'},check=True)
 return {str(p.relative_to('/tmp/models')):p.read_bytes() for p in Path('/tmp/models').rglob('*') if p.is_file() and p.suffix in ('.glb','.png','.json')}
@app.local_entrypoint()
def main():
 import subprocess
 target=Path(__file__).resolve().parent.parent/'public/models';target.mkdir(parents=True,exist_ok=True)
 for name,data in build.remote().items():
  path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  print('Saved',name,len(data),'bytes')
 # The lightweight palette bake runs locally with the project's Babylon dependency.
 subprocess.run(['node','tools/bake-crowd.mjs'],cwd=target.parent.parent,check=True)
