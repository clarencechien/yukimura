"""Encode actual unloading and sword-release-page screenshots; no generated animation frames."""
from pathlib import Path
import json,subprocess
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';TMP=ROOT/'.tmp/free-arm-settle-capture'
rows=json.loads((OUT/'capture.json').read_text());assert len(rows)==150
frames=[];size=Image.open(TMP/'000.png').size;assert size[0]>=1200
for i,r in enumerate(rows):
 assert r['sample']==i
 pose=r['pose'];assert np.hypot(pose['wrist']['x']-pose['target']['x'],pose['wrist']['y']-pose['target']['y'])<1e-6
 assert len(r['swords'])==4
 if pose['planted']: assert np.hypot(pose['heel']['x']-pose['contact']['x'],pose['heel']['y']-pose['contact']['y'])<1e-6
 im=Image.open(TMP/f'{i:03d}.png').convert('RGB');assert im.size==size;frames.append(im)
# One stable palette lets GIF encode only changed rectangles instead of
# re-quantizing the static background differently in every frame.
palette=frames[0].quantize(colors=256)
paletted=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
paletted[0].save(OUT/'settle-preview.gif',save_all=True,append_images=paletted[1:],duration=[30,30,40]*50,loop=0,optimize=True,disposal=1)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','150','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(OUT/'settle-30fps.mp4')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(OUT/'settle-30fps.mp4')]))['streams'][0]
assert probe['nb_frames']=='150' and probe['r_frame_rate']=='30/1' and float(probe['duration'])==5
assert (probe['width'],probe['height'])==tuple(n+n%2 for n in size)
with Image.open(OUT/'settle-preview.gif') as gif:
 assert gif.size==size
 decoded=[];end=0
 for i in range(gif.n_frames):
  gif.seek(i);end+=gif.info['duration'];decoded.append((end,np.array(gif.convert('RGB'))))
 assert end==5000
 sample_time=0
 for i,frame in enumerate(paletted):
  actual=next(pixels for end,pixels in decoded if end>sample_time)
  assert np.array_equal(actual,np.array(frame.convert('RGB'))), ('GIF frame mismatch',i)
  sample_time += [30,30,40][i%3]
 gif_frames=len(decoded)
(OUT/'video-check.json').write_text(json.dumps({'passed':True,'frames':150,'gifStoredFrames':gif_frames,'fps':30,'durationSeconds':5,'sourceSize':size,'videoSize':[probe['width'],probe['height']],'source':'Actual unloading and sword-release Canvas screenshots; controlled browser clock, quarter-speed reaction time, no interpolated image frames.','limits':'Previous five-pose study compared with a shared torso hinge, rigid shin/shoe and existing sword arm, released blade, unloading torso and released support hand. 30 fps is playback cadence, not thirty distinct body drawings; independent review, not installed combat. GIF uses one 256-color palette with changed rectangles, 30/30/40 ms timing and merged identical holds; MP4 is uniform 30 fps, padded to even dimensions without scaling or cropping.'},indent=2)+'\n')
print('Encoded 150 actual unloading and sword-release canvas frames, 30 fps / 5 seconds.')
