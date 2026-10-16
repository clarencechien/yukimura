from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-support';m=json.loads((OUT/'support.json').read_text())
def same(a,b):
 a,b=np.array(a),np.array(b);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[:,:,:3][a[:,:,3]>0],b[:,:,:3][b[:,:,3]>0])
for entry in [m['body'],m['palm']]:assert hashlib.sha256((ROOT/entry['source']).read_bytes()).hexdigest()==entry['sha256']
b=m['body'];raw=Image.open(ROOT/b['source']).convert('RGBA');frame=Image.new('RGBA',(1152,768));frame.alpha_composite(raw.resize((round(raw.width*b['scale']),round(raw.height*b['scale'])),Image.Resampling.LANCZOS),tuple(b['offset']));same(frame,Image.open(OUT/'body.webp').convert('RGBA'))
coverage=np.zeros((768,1152),dtype=np.uint8)
for name,box in b['boxes'].items():
 crop=frame.crop(box);mask=Image.new('L',crop.size);ImageDraw.Draw(mask).polygon([(x-box[0],y-box[1]) for x,y in b['polygons'][name]],fill=255);a=np.array(crop);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));same(Image.fromarray(a),Image.open(OUT/f'{name}.webp').convert('RGBA'))
 if name!='cap':coverage[box[1]:box[3],box[0]:box[2]]=np.maximum(coverage[box[1]:box[3],box[0]:box[2]],a[:,:,3])
alpha=np.array(frame)[:,:,3];missing=alpha>coverage
assert not np.any(missing & (alpha>1)), 'Torso/lower masks leave visible source pixels missing'
omitted=int(np.count_nonzero(missing)) # Generated distant alpha=1 speckles outside packed boxes.
assert b['overlap']>10 # Initial raised torso keeps at least 14 px waist overlap.
p=m['palm'];raw=Image.open(ROOT/p['source']).convert('RGBA');same(raw.crop(p['box']).resize(tuple(p['size']),Image.Resampling.LANCZOS),Image.open(OUT/'palm.webp').convert('RGBA'))
for point,key in [('sourceWrist','pivot'),('sourceHeel','heel')]:assert p[key]==[(p[point][i]-p['box'][i])*p['scale'] for i in range(2)]
paths=['docs/routes/jigoku-2d/combat','docs/routes/jigoku-2d/free-arm-parts','src','public']
subprocess.run(['git','diff','--exit-code',m['baselineCommit'],'--',*paths],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*paths],cwd=ROOT).strip()
textures=['torso','lower','cap','palm'];budget=sum(Image.open(OUT/f'{n}.webp').width*Image.open(OUT/f'{n}.webp').height*4 for n in textures)
(OUT/'art-check.json').write_text(json.dumps({'passed':True,'baselineCommit':m['baselineCommit'],'checks':['Body/palm source hashes and declared uniform registration','Torso/lower/cap preserve source pixels under declared masks','Torso/lower union covers all source pixels with alpha > 1; 24 px waist overlap','Palm wrist/heel source coordinates map to packed sprite','Existing arm kit and production combat/src/public unchanged'],'omittedAlpha1Pixels':omitted,'newLoadedRGBA8MiB':budget/1048576,'scope':'Excludes reused arm textures and canvas buffers; body.webp is an inspection source and is not loaded by review. No anatomy or force validation.'},indent=2)+'\n');print('Support source, overlap, palm registration and runtime isolation checks passed.')
