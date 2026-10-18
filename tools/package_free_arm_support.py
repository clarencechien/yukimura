"""Encode actual kneeling-support-page screenshots; no generated animation frames."""
from pathlib import Path
import json,subprocess
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-support';TMP=ROOT/'.tmp/free-arm-support-capture'
rows=json.loads((OUT/'capture.json').read_text());assert len(rows)==30
frames=[];size=Image.open(TMP/'000.png').size;assert size[0]>=1200
for i,r in enumerate(rows):
 assert r['sample']==i
 pose=r['pose'];assert np.hypot(pose['wrist']['x']-pose['target']['x'],pose['wrist']['y']-pose['target']['y'])<1e-6
 if pose['planted']: assert np.hypot(pose['heel']['x']-pose['contact']['x'],pose['heel']['y']-pose['contact']['y'])<1e-6
 im=Image.open(TMP/f'{i:03d}.png').convert('RGB');assert im.size==size;frames.append(im)
paletted=[im.convert('P',palette=Image.Palette.ADAPTIVE,colors=256) for im in frames]
paletted[0].save(OUT/'support-preview.gif',save_all=True,append_images=paletted[1:],duration=[30,30,40]*10,loop=0,optimize=False,disposal=2)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','30','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(OUT/'support-30fps.mp4')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(OUT/'support-30fps.mp4')]))['streams'][0]
assert probe['nb_frames']=='30' and probe['r_frame_rate']=='30/1' and float(probe['duration'])==1
assert (probe['width'],probe['height'])==tuple(n+n%2 for n in size)
with Image.open(OUT/'support-preview.gif') as gif:
 assert gif.size==size
 decoded=[];end=0
 for i in range(gif.n_frames):
  gif.seek(i);end+=gif.info['duration'];decoded.append((end,np.array(gif.convert('RGB'))))
 assert end==1000
 sample_time=0
 for i,frame in enumerate(paletted):
  actual=next(pixels for end,pixels in decoded if end>sample_time)
  assert np.array_equal(actual,np.array(frame.convert('RGB'))), ('GIF frame mismatch',i)
  sample_time += [30,30,40][i%3]
 gif_frames=len(decoded)
(OUT/'video-check.json').write_text(json.dumps({'passed':True,'frames':30,'gifStoredFrames':gif_frames,'fps':30,'durationSeconds':1,'sourceSize':size,'videoSize':[probe['width'],probe['height']],'source':'Actual kneeling-support Canvas screenshots; controlled browser clock, quarter-speed reaction time, no interpolated image frames.','limits':'Standalone kneeling support segment, not a full crouch transition or installed combat animation. GIF uses 30/30/40 ms timing and merges identical holds; MP4 is uniform 30 fps, padded to even dimensions without scaling or cropping.'},indent=2)+'\n')
print('Encoded 30 actual kneeling-support canvas frames, 30 fps / 1 second.')
