"""Cut rigid image layers from the original art and the prepared clean body.

No generative per-frame edits. Polygon cutouts, alpha masks and cropping only.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/source/jigoku-2d/yari-rigid'
OUT=SOURCE/'layers';OUT.mkdir(exist_ok=True)
CONFIG=json.loads((SOURCE/'rig.json').read_text())
W,H=CONFIG['canvas']
def polygon(points):
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon([tuple(p) for p in points],fill=255)
    return np.array(mask)

weapon=polygon(CONFIG['parts']['weapon'])
weapon[:,1100:]=255  # Beyond the figure: source alpha isolates blade/shaft exactly.
manifest={'canvas':[W,H],'layers':{},'method':'Rigid alpha cutouts; clean body prepared once by image_gen, original limbs/weapon retained.'}
for light in ['neutral','warm-left','cool-right']:
    original=Image.open(ROOT/f'docs/routes/jigoku-2d/yari-motion/lights/{light}.png').convert('RGBA')
    body=Image.open(ROOT/f'docs/routes/jigoku-2d/yari-rigid/body-lights/{light}.png').convert('RGBA')
    masks={name:polygon(poly) for name,poly in CONFIG['parts'].items()}
    masks['weapon']=weapon
    masks['torso']=np.zeros((H,W),dtype=np.uint8);masks['torso'][:CONFIG['torso_cut_y']]=255
    masks['lower']=np.zeros((H,W),dtype=np.uint8);masks['lower'][CONFIG['lower_start_y']:]=255
    for name,mask in masks.items():
        if name in ['front_forearm','rear_forearm','front_upper','rear_upper']:
            # Spear pixels must not rotate with the forearm.
            mask=np.minimum(mask,255-weapon)
        rgba=np.array(body if name in ['torso','lower'] else original).copy()
        # Half-pixel antialiasing at manually cut boundaries; no warp or inpaint.
        soft=np.array(Image.fromarray(mask).filter(ImageFilter.GaussianBlur(.45)))
        rgba[:,:,3]=(rgba[:,:,3].astype(float)*soft/255).round().astype('uint8')
        labels,count=ndimage.label(rgba[:,:,3]>0)
        sizes=np.bincount(labels.ravel());keep=sizes>=24;keep[0]=False
        rgba[:,:,3][~keep[labels]]=0  # Disconnected alpha flecks, not garment detail.
        im=Image.fromarray(rgba);box=im.getbbox();assert box
        im.crop(box).save(OUT/f'{name}-{light}.png')
        if name not in manifest['layers']:manifest['layers'][name]={'box':list(box),'files':{}}
        assert manifest['layers'][name]['box']==list(box)
        manifest['layers'][name]['files'][light]=f'{name}-{light}.png'
(SOURCE/'layers.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared',len(manifest['layers']),'rigid layers × 3 lights.')
