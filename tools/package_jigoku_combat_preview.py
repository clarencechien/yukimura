"""Encode actual browser screenshots; no generated or interpolated motion frames."""
from pathlib import Path
import json,subprocess
from PIL import Image, ImageChops, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/combat-check/frames'
frames=sorted(TMP.glob('*.png'));assert len(frames)==72
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','72','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'combat-30fps.mp4')],check=True)
images=[Image.open(p).convert('RGB').resize((640,400),Image.Resampling.LANCZOS) for p in frames]
sheet=Image.new('RGB',(640*8,400*9))
for i,im in enumerate(images):sheet.paste(im,((i%8)*640,(i//8)*400))
palette=sheet.quantize(colors=256)
gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
gifs[0].save(OUT/'combat-preview.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*24,loop=0,disposal=1,optimize=True)
decoded=Image.open(OUT/'combat-preview.gif')
assert decoded.n_frames==len(gifs)
for i,expected in enumerate(gifs):
    decoded.seek(i)
    assert ImageChops.difference(decoded.convert('RGB'),expected.convert('RGB')).getbbox() is None, ('GIF ghosting',i)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(OUT/'combat-30fps.mp4')]))['streams'][0]
assert probe['avg_frame_rate']=='30/1' and int(probe['nb_read_frames'])==72 and abs(float(probe['duration'])-2.4)<.001
(OUT/'video-check.json').write_text(json.dumps({'passed':True,'source':'72 actual Phaser browser screenshots sampled with controlled clock at 33/33/34 ms','video':probe,'gif':'30/30/40 ms approximate 30 fps; use MP4 for uniform frame timing.','note':'This is deterministic capture, not measured real-device frame rate.'},indent=2)+'\n')
print('Encoded and verified 72 frames / 30 fps / 2.4 seconds.')

# Inspect authored enemy transitions using the exact captured browser frames.
rows=json.loads((OUT/'capture-timing.json').read_text())
inspection=Image.new('RGB',(1152,960),'#1b2328')
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(phase,label) in enumerate([('guard','戒備'),('hurt','受擊'),('kneel','跪倒'),('fallen','伏地'),('dissolve','消散'),('gone','離場')]):
    row=next(r for r in rows if r['enemy']['phase']==phase)
    im=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').crop((760,160,1200,650)).resize((384,428),Image.Resampling.LANCZOS)
    inspection.paste(im,((i%3)*384,(i//3)*480))
    ImageDraw.Draw(inspection).text(((i%3)*384+18,(i//3)*480+440),label,font=font,fill='#e0c9a2')
inspection.save(OUT/'enemy-sequence.jpg',quality=93)
