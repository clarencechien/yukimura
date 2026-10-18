"""Encode actual side-by-side browser frames; no image interpolation."""
from pathlib import Path
from PIL import Image
import json,subprocess,numpy as np
OUT=Path('docs/routes/jigoku-2d/free-arm-settle');TMP=Path('.tmp/hip-motion');rows=json.loads((OUT/'hip-capture.json').read_text());assert len(rows)==90
frames=[]
for i,r in enumerate(rows):
 assert r['sample']==i and r['sourceAges']==[r['age'],r['age']];assert r['poseEqual'] and r['headEqual'] and r['weaponEqual'];frames.append(Image.open(TMP/f'{i:03d}.png').convert('RGB'))
size=frames[0].size;assert all(im.size==size for im in frames);palette=frames[0].quantize(colors=256);quantized=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
quantized[0].save(OUT/'hip-preview.gif',save_all=True,append_images=quantized[1:],duration=[30,30,40]*30,loop=0,optimize=True,disposal=1)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','90','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(OUT/'hip-30fps.mp4')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(OUT/'hip-30fps.mp4')]))['streams'][0];assert probe['nb_frames']=='90' and probe['r_frame_rate']=='30/1' and float(probe['duration'])==3
assert (probe['width'],probe['height'])==tuple(n+n%2 for n in size)
with Image.open(OUT/'hip-preview.gif') as gif:
 decoded=[];end=0
 for i in range(gif.n_frames):
  gif.seek(i);end+=gif.info['duration'];decoded.append((end,np.array(gif.convert('RGB'))))
 assert end==3000;time=0
 for i,q in enumerate(quantized):
  assert np.array_equal(next(p for end,p in decoded if end>time),np.array(q.convert('RGB')));time+=[30,30,40][i%3]
(OUT/'hip-video-check.json').write_text(json.dumps(dict(passed=True,frames=90,fps=30,durationSeconds=3,sourceSize=size,videoSize=[probe['width'],probe['height']],gifStoredFrames=len(decoded),source='Actual synchronized Canvas comparison captured with controlled browser clock; quarter-speed reaction time and final hold.',limits='Only waist artwork is generated. Video is not imagegen output or interpolated frame synthesis. 30 fps playback does not create thirty new drawings. Comparison candidate is not the default game or review artwork.'),indent=2)+'\n')
print('Encoded 90 actual comparison frames, 30 fps / 3 seconds; GIF samples verified.')
