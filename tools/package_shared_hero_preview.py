"""Encode actual shared-hero browser frames and verify playback; no generated motion."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/shared-hero-check/frames'
rows=json.loads((OUT/'shared-hero-capture.json').read_text());frames=sorted(TMP.glob('*.png'));assert len(frames)==len(rows)==60
assert rows[-1]['hits']==1 and rows[-1]['phase']=='idle'
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','60','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'shared-hero-30fps.mp4')],check=True)
images=[Image.open(f).convert('RGB').resize((640,400),Image.Resampling.LANCZOS) for f in frames];sheet=Image.new('RGB',(640*6,400*10))
for i,im in enumerate(images):sheet.paste(im,(i%6*640,i//6*400))
palette=sheet.quantize(colors=256);gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
gifs[0].save(OUT/'shared-hero-preview.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*20,loop=0,disposal=1,optimize=True)
# Static ready poses can be merged by GIF encoding. Compare each time interval,
# including merged durations, rather than claiming 60 distinct GIF frames.
decoded=Image.open(OUT/'shared-hero-preview.gif');cursor=0
for i in range(decoded.n_frames):
 decoded.seek(i);duration=decoded.info['duration'];used=0
 while used<duration:
  assert ImageChops.difference(decoded.convert('RGB'),gifs[cursor].convert('RGB')).getbbox() is None
  used+=[30,30,40][cursor%3];cursor+=1
 assert used==duration
assert cursor==60
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(OUT/'shared-hero-30fps.mp4')]))['streams'][0]
assert probe['avg_frame_rate']=='30/1' and int(probe['nb_read_frames'])==60 and abs(float(probe['duration'])-2)<.001
(OUT/'shared-hero-video-check.json').write_text(json.dumps({'passed':True,'video':probe,'source':'60 actual controlled browser frames, not per-frame generated art or a hardware frame-rate benchmark','gif':{'frames':decoded.n_frames,'decodedTimelineMatches':True,'durationMS':2000}},indent=2)+'\n')
print('Verified shared-hero 60-frame / 30 fps / 2 second capture and decoded GIF timeline.')
