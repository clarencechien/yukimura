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
# Split the original lower mask along armor overlaps. The central skirt and
# hanging cords remain on the pelvis; legs keep their painted proportions.
base_lower=layers['lower']['polygon']
layers['lower']={'box':[420,350,810,590],'polygon':[(0,0),(1152,0),(1152,515),(760,515),(720,488),(664,473),(642,470),(644,505),(642,580),(600,590),(545,590),(532,500),(515,468),(422,472),(0,472)]}
layers.update({
 'leftThigh':{'box':[375,440,555,580],'polygon':[(420,448),(515,448),(550,495),(545,540),(515,575),(380,560),(382,490)]},
 'leftShin':{'box':[345,510,495,660],'polygon':[(392,516),(490,540),(435,650),(350,655)]},
 'leftFoot':{'box':[315,610,445,700],'polygon':[(353,615),(430,625),(439,699),(315,699),(320,660)]},
 'rightThigh':{'box':[610,435,755,585],'polygon':[(622,440),(700,455),(750,515),(738,568),(645,578),(613,498)]},
 'rightShin':{'box':[650,525,785,675],'polygon':[(654,531),(755,531),(778,660),(696,668)]},
 'rightFoot':{'box':[685,615,815,700],'polygon':[(705,619),(760,619),(807,669),(810,700),(690,700)]},
})
for name,layer in layers.items():
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(layer['polygon'],fill=255)
 if name!='torso':
  base=Image.new('L',im.size);ImageDraw.Draw(base).polygon(base_lower,fill=255);mask=Image.fromarray(np.minimum(np.array(mask),np.array(base)))
 rgba=np.array(im);rgba[:,:,3]=(rgba[:,:,3].astype(float)*np.array(mask)/255).round().astype('uint8')
 part=Image.fromarray(rgba).crop(layer['box']);part.save(OUT/f'enemy-body-{name}-hd.webp',lossless=True)
 part.resize((round(part.width*2/3),round(part.height*2/3)),Image.Resampling.LANCZOS).save(OUT/f'enemy-body-{name}.webp',lossless=True)
(OUT/'enemy-body-art.json').write_text(json.dumps({'source':'ghost-warrior-hd.webp','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceCell':[0,0,1152,768],'pivot':[577,382],'layers':layers,'lowerSourceMask':base_lower,'method':'Only alpha masks and rectangular crops of the existing guard cell. Mobile is a uniform 2/3 resample rounded to whole pixels. No generated or repainted pixels.'},indent=2)+'\n')
print('Packed eight shared enemy body pieces at desktop/mobile resolutions.')
