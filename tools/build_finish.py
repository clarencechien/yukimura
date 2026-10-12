"""Reuse baked surface data to mask lacquer, leaving cloth and bare metal matte.
No new bake or paid API: Blender NumPy, deterministic box downsample.
"""
import bpy,json,struct,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'public/look';OUT.mkdir(exist_ok=True)
report={}
for kind,size in [('yukimura',512),('ieyasu',256)]:
    raw=(ROOT/'public/models'/f'{kind}.glb').read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    index=g['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']['index']
    uri=g['images'][g['textures'][index]['source']]['uri'];source=ROOT/'public/models'/uri
    image=bpy.data.images.load(str(source));image.colorspace_settings.name='Non-Color';w,h=image.size
    pixels=np.empty(w*h*4,np.float32);image.pixels.foreach_get(pixels);p=pixels.reshape(h,w,4)
    mask=np.clip((.72-p[:,:,1])/.16,0,1)*np.clip((.38-p[:,:,2])/.16,0,1)*(p[:,:,0]>.01)
    small=mask.reshape(size,h//size,size,w//size).mean(axis=(1,3))
    rgba=np.ones((size,size,4),np.float32);rgba[:,:,0]=small;rgba[:,:,1]=.30;rgba[:,:,2]=0
    out=bpy.data.images.new(kind+' lacquer mask',size,size,alpha=False);out.colorspace_settings.name='Non-Color';out.pixels.foreach_set(rgba.ravel());out.filepath_raw=str(OUT/f'{kind}-coat.png');out.file_format='PNG';out.save()
    data=Path(out.filepath_raw).read_bytes();report[kind]={'uri':f'{kind}-coat.png','size':size,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source':uri,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    bpy.data.images.remove(image);bpy.data.images.remove(out)
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
