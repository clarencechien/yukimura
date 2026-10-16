"""Mechanical cutouts of the existing guard painting; no repainted anatomy."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
source=OUT/'ghost-warrior-hd.webp'
im=Image.open(source).convert('RGBA').crop((0,0,1152,768))
# Follow the belt beneath the painted support hand. A narrow overlap hides the
# rigid waist seam; the lower piece is behind the torso, never a second body.
seam=[(0,405),(490,405),(525,400),(552,390),(592,382),(626,375),(660,365),(1152,365)]
layers={
 'torso':{'box':[425,115,710,420],'polygon':[(0,0),(1152,0)]+[(x,y+12) for x,y in reversed(seam)]},
 'lower':{'box':[320,350,810,700],'polygon':[(x,y-10) for x,y in seam]+[(1152,768),(0,768)]},
}
for name,layer in layers.items():
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(layer['polygon'],fill=255)
 rgba=np.array(im);rgba[:,:,3]=(rgba[:,:,3].astype(float)*np.array(mask)/255).round().astype('uint8')
 part=Image.fromarray(rgba).crop(layer['box']);part.save(OUT/f'enemy-body-{name}-hd.webp',lossless=True)
 part.resize((round(part.width*2/3),round(part.height*2/3)),Image.Resampling.LANCZOS).save(OUT/f'enemy-body-{name}.webp',lossless=True)
(OUT/'enemy-body-art.json').write_text(json.dumps({'source':'ghost-warrior-hd.webp','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceCell':[0,0,1152,768],'pivot':[577,382],'layers':layers,'method':'Only alpha masks and rectangular crops of the existing guard cell. Mobile is a uniform 2/3 resample rounded to whole pixels. No generated or repainted pixels.'},indent=2)+'\n')
print('Packed two shared enemy body pieces at desktop/mobile resolutions.')
