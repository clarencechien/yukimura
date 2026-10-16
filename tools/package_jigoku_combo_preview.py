"""Package real Phaser screenshots; no generated interpolation."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/combat-check/combo-frames'
frames=sorted(TMP.glob('*.png'));assert len(frames)==90
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','90','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'combo-30fps.mp4')],check=True)
images=[Image.open(p).convert('RGB').resize((640,400),Image.Resampling.LANCZOS) for p in frames]
sheet=Image.new('RGB',(640*9,400*10))
for i,im in enumerate(images):sheet.paste(im,((i%9)*640,(i//9)*400))
palette=sheet.quantize(colors=256);gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
gifs[0].save(OUT/'combo-preview.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*30,loop=0,disposal=1,optimize=True)
decoded=Image.open(OUT/'combo-preview.gif');assert decoded.n_frames==90
for i,expected in enumerate(gifs):
 decoded.seek(i);assert ImageChops.difference(decoded.convert('RGB'),expected.convert('RGB')).getbbox() is None,('ghosting',i)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(OUT/'combo-30fps.mp4')]))['streams'][0]
assert probe['avg_frame_rate']=='30/1' and int(probe['nb_read_frames'])==90 and abs(float(probe['duration'])-3)<.001
rows=json.loads((OUT/'combo-capture.json').read_text())
for pose,texture,frame in [(0,'sweepBoundary',0),(5,'sweepBoundary',1)]:
 samples=[r for r in rows if r['sweepPose']==pose];assert samples
 assert all(r['texture']==texture and r['heroFrame']==frame for r in samples),'Rendered boundary must use resident source cell'
plate=Image.new('RGB',(1200,1125))
for i in range(6):
 row=next(r for r in rows if r['sweepPose']==i)
 im=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB');plate.paste(im.resize((600,375),Image.Resampling.LANCZOS),((i%2)*600,(i//2)*375))
plate.save(OUT/'combo-sequence.jpg',quality=94)
(OUT/'combo-video-check.json').write_text(json.dumps({'passed':True,'video':probe,'source':'90 actual Phaser screenshots with controlled 33/33/34 ms clock; not a device FPS benchmark','sweep':'Six silhouettes held over 32 simulation frames: two shared boundary frames, two preserved low poses, two new transitions; no interpolated body frames','gif':'30/30/40 ms timings, decoded pixels checked against palette frames','residentTextureChecks':'Every captured start/end sweep sample binds extracted sweepBoundary cells 0 / 1; old full idle/thrust atlases are no longer loaded'},indent=2)+'\n')
print('Verified combo capture: 90 frames, 30 fps, 3 seconds.')
