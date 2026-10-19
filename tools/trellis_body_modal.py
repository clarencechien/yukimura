"""Full-body v2 at 1536 cascade. Reuses the verified CUDA image; caches source before any export."""
from pathlib import Path
import os
import modal

app=modal.App('yukimura-trellis2-body-v2')
cache=modal.Volume.from_name('yukimura-trellis2-cache')
image=modal.Image.from_id('im-CWPfod9BzDeCjqD07JU8Ui')
secrets=[] if os.environ.get('TRELLIS_ENVIRONMENT_CHECK_ONLY')=='1' else [modal.Secret.from_name(os.environ.get('TRELLIS_HF_SECRET','trellis-huggingface'),required_keys=['HF_TOKEN'])]
ROOT='results/future-sanada-body-v2'
COMMIT='75fbf0183001ed9876c8dbb35de6b68552ee08bd'

@app.function(image=image,cpu=1,timeout=120,retries=0,secrets=secrets)
def preflight(data:bytes):
    import io
    from PIL import Image
    from huggingface_hub import HfApi,get_hf_file_metadata,hf_hub_url
    im=Image.open(io.BytesIO(data))
    lo,hi=im.getchannel('A').getextrema();assert im.mode=='RGBA' and lo==0 and hi>=250
    repo='facebook/dinov3-vitl16-pretrain-lvd1689m';token=os.environ['HF_TOKEN']
    info=HfApi().model_info(repo,token=token)
    weight=next(f.rfilename for f in info.siblings if f.rfilename.endswith('.safetensors'))
    for name in ['config.json',weight]:get_hf_file_metadata(hf_hub_url(repo,name),token=token)
    return {'access':'passed','alpha':'passed','image_size':list(im.size)}

@app.function(image=image,gpu='H100',cpu=4,memory=49152,timeout=1200,startup_timeout=1200,max_containers=2,scaledown_window=2,retries=0,volumes={'/cache':cache},secrets=secrets)
def generate(data:bytes,seed:int=1615,export_only:bool=False,remesh:bool=False):
    REMOTE=f'{ROOT}/seed-{seed}'
    import io,json,time,hashlib,tempfile
    import numpy as np
    import torch
    import o_voxel
    from PIL import Image
    from huggingface_hub import hf_hub_download
    from trellis2.pipelines import Trellis2ImageTo3DPipeline,rembg
    started=time.monotonic();directory=Path('/cache')/REMOTE;directory.mkdir(parents=True,exist_ok=True)
    def describe(p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            while chunk:=f.read(1024*1024):h.update(chunk)
        return {'name':p.name,'bytes':p.stat().st_size,'sha256':h.hexdigest()}
    if not export_only:
        report={'model':'microsoft/TRELLIS.2-4B','trellis_commit':COMMIT,'study':'full body v2','input_sha256':hashlib.sha256(data).hexdigest(),'pipeline':'1536_cascade','seed':seed,'max_num_tokens':65536,'gpu':torch.cuda.get_device_name(),'torch':str(torch.__version__),'status':'running'}
        repo=report['model'];config=json.loads(Path(hf_hub_download(repo,'pipeline.json')).read_text())
        for key,path in config['args']['models'].items():
            if path.startswith('ckpts/'):config['args']['models'][key]=f'{repo}/{path}'
        config['args']['rembg_model']={'name':'ProvidedAlpha','args':{}};rembg.ProvidedAlpha=lambda:None
        with tempfile.TemporaryDirectory() as temp:
            Path(temp,'pipeline.json').write_text(json.dumps(config));pipeline=Trellis2ImageTo3DPipeline.from_pretrained(temp)
        pipeline.cuda();report['load_seconds']=time.monotonic()-started;t=time.monotonic()
        outputs,latent=pipeline.run(Image.open(io.BytesIO(data)),seed=seed,pipeline_type='1536_cascade',return_latent=True,max_num_tokens=65536)
        actual_resolution=int(latent[2]);del latent;mesh=outputs[0];del outputs
        torch.cuda.synchronize();report.update(inference_seconds=time.monotonic()-t,actual_resolution=actual_resolution,source_vertices=int(mesh.vertices.shape[0]),source_triangles=int(mesh.faces.shape[0]))
        print('Generated body:',json.dumps(report),flush=True)
        vertices=mesh.vertices;faces=mesh.faces;attrs=mesh.attrs;coords=mesh.coords;layout=mesh.layout;voxel_size=float(mesh.voxel_size)
        del pipeline;torch.cuda.empty_cache()
        t=time.monotonic()
        np.savez_compressed(directory/'source-geometry.npz',vertices=vertices.cpu().numpy(),faces=faces.cpu().numpy())
        np.savez_compressed(directory/'source-attributes.npz',attrs=attrs.cpu().numpy(),coords=coords.cpu().numpy())
        metadata={'layout':{k:[v.start,v.stop,v.step] for k,v in layout.items()},'voxel_size':voxel_size}
        (directory/'source-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        report['source_files']=[describe(directory/n) for n in ['source-geometry.npz','source-attributes.npz','source-metadata.json']]
        report['source_save_seconds']=time.monotonic()-t;report['status']='source_cached';report['exports']=[]
        (directory/'generation.json').write_text(json.dumps(report,indent=2)+'\n');cache.commit()
        print('Source mesh and voxel materials committed before export.',flush=True)
    else:
        report=json.loads((directory/'generation.json').read_text())
        if hashlib.sha256(data).hexdigest()!=report['input_sha256']:raise ValueError('Cached source belongs to a different reference')
        source=np.load(directory/'source-geometry.npz',allow_pickle=False);material=np.load(directory/'source-attributes.npz',allow_pickle=False)
        vertices=torch.from_numpy(source['vertices']).cuda();faces=torch.from_numpy(source['faces']).cuda();attrs=torch.from_numpy(material['attrs']).cuda();coords=torch.from_numpy(material['coords']).cuda()
        metadata=json.loads((directory/'source-metadata.json').read_text());layout={k:slice(*v) for k,v in metadata['layout'].items()};voxel_size=metadata['voxel_size']
    plan=[('body-remesh.glb',600000,4096,True)] if remesh else [('body-high.glb',600000,4096,False),('body-light.glb',200000,2048,False)]
    for name,target,size,closed in plan:
        if any(e['name']==name for e in report['exports']) and (directory/name).exists():continue
        t=time.monotonic()
        glb=o_voxel.postprocess.to_glb(vertices=vertices,faces=faces,attr_volume=attrs,coords=coords,attr_layout=layout,voxel_size=voxel_size,aabb=[[-.5,-.5,-.5],[.5,.5,.5]],decimation_target=target,texture_size=size,remesh=closed,remesh_band=1,remesh_project=0,verbose=True)
        glb.export(str(directory/name));del glb;torch.cuda.empty_cache()
        report['exports'].append({**describe(directory/name),'target_triangles':target,'texture_size':size,'remesh':closed,'export_seconds':time.monotonic()-t})
        (directory/'generation.json').write_text(json.dumps(report,indent=2)+'\n');cache.commit();print('Exported:',name,flush=True)
    report.update(status='completed',invocation_seconds=time.monotonic()-started,peak_pytorch_allocated_gib=torch.cuda.max_memory_allocated()/2**30)
    (directory/'generation.json').write_text(json.dumps(report,indent=2)+'\n');cache.commit();return report

@app.local_entrypoint()
def main(input:str='docs/experiments/future-sanada/reference.png',output:str='.tmp/body-v2',seeds:str='1615,7',download_only:bool=False,export_only:bool=False,remesh:bool=False,include_source:bool=False):
    import json,hashlib
    seeds=[int(s) for s in seeds.split(',')]
    if not download_only:
        data=Path(input).read_bytes();print('CPU preflight:',preflight.remote(data))
        calls=[generate.spawn(data,seed,export_only,remesh) for seed in seeds]
        for call in calls:print('Completed:',call.get())
    def download(remote,name,destination,expected=None):
        destination.parent.mkdir(parents=True,exist_ok=True);part=destination.with_suffix(destination.suffix+'.part');h=hashlib.sha256()
        try:
            with part.open('wb') as f:
                for chunk in cache.read_file(remote+'/'+name):f.write(chunk);h.update(chunk)
            if expected and h.hexdigest()!=expected:raise ValueError('SHA256 mismatch: '+name)
            part.replace(destination)
        finally:part.unlink(missing_ok=True)
        print('Saved',destination,destination.stat().st_size,flush=True)
    for seed in seeds:
        remote=f'{ROOT}/seed-{seed}';target=Path(output)/f'seed-{seed}'
        download(remote,'generation.json',target/'generation.json');report=json.loads((target/'generation.json').read_text())
        for artifact in report['exports']:download(remote,artifact['name'],target/artifact['name'],artifact['sha256'])
        if include_source:
            for artifact in report['source_files']:download(remote,artifact['name'],target/'source'/artifact['name'],artifact['sha256'])
