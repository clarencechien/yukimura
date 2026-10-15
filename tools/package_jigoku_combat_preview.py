"""Encode actual browser screenshots; no generated or interpolated motion frames."""
from pathlib import Path
import json,subprocess
from PIL import Image, ImageChops, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/combat-check/frames'
frames=sorted(TMP.glob('*.png'));assert len(frames)==78
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'%03d.png'),'-frames:v','78','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'combat-30fps.mp4')],check=True)
images=[Image.open(p).convert('RGB').resize((640,400),Image.Resampling.LANCZOS) for p in frames]
sheet=Image.new('RGB',(640*8,400*10))
for i,im in enumerate(images):sheet.paste(im,((i%8)*640,(i//8)*400))
palette=sheet.quantize(colors=256)
gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
gifs[0].save(OUT/'combat-preview.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*26,loop=0,disposal=1,optimize=True)
decoded=Image.open(OUT/'combat-preview.gif')
assert decoded.n_frames==len(gifs)
for i,expected in enumerate(gifs):
    decoded.seek(i)
    assert ImageChops.difference(decoded.convert('RGB'),expected.convert('RGB')).getbbox() is None, ('GIF ghosting',i)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(OUT/'combat-30fps.mp4')]))['streams'][0]
assert probe['avg_frame_rate']=='30/1' and int(probe['nb_read_frames'])==78 and abs(float(probe['duration'])-2.6)<.001
(OUT/'video-check.json').write_text(json.dumps({'passed':True,'source':'78 actual Phaser browser screenshots sampled with controlled clock at 33/33/34 ms','video':probe,'gif':'30/30/40 ms approximate 30 fps; use MP4 for uniform frame timing.','note':'This is deterministic capture, not measured real-device frame rate.'},indent=2)+'\n')
print('Encoded and verified 78 frames / 30 fps / 2.6 seconds.')

# Inspect authored enemy transitions using the exact captured browser frames.
rows=json.loads((OUT/'capture-timing.json').read_text())
inspection=Image.new('RGB',(1536,1440),'#1b2328')
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(phase,label) in enumerate([('guard','戒備'),('flinch','輕受擊'),('hurt','後仰'),('buckle','重心下沉'),('crouch','屈膝'),('kneel','跪下'),('brace','手掌承重'),('lower','屈肘落胯'),('settle','側身落地'),('fallen','伏地'),('dissolve','消散'),('gone','離場')]):
    row=next(r for r in rows if r['enemy']['phase']==phase)
    im=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').crop((760,160,1200,650)).resize((384,428),Image.Resampling.LANCZOS)
    inspection.paste(im,((i%4)*384,(i//4)*480))
    ImageDraw.Draw(inspection).text(((i%4)*384+18,(i//4)*480+440),label,font=font,fill='#e0c9a2')
inspection.save(OUT/'enemy-sequence.jpg',quality=93)

# Wrist contact inspection from actual renderer captures, including release and landing.
contacts=Image.new('RGB',(1152,1050),'#1b2328')
labels=[('guard','戒備'),('flinch','輕受擊'),('hurt','後仰'),('buckle','重心下沉'),('crouch','屈膝'),('kneel','跪下'),('brace','半開握姿'),('lower','已脫手'),('fallen','刀已落地')]
for i,(phase,label) in enumerate(labels):
    candidates=[r for r in rows if r['enemy']['phase']==phase]
    row=candidates[-1] if phase in ['fallen','brace'] else candidates[0]
    point=row['hand'] if row['weapon']['held'] else row['weapon']
    x,y=round(point['x']),round(point['y'])
    crop=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').crop((x-150,y-70,x+70,y+100)).resize((384,297),Image.Resampling.LANCZOS)
    contacts.paste(crop,((i%3)*384,(i//3)*350))
    ImageDraw.Draw(contacts).text(((i%3)*384+15,(i//3)*350+308),label,font=font,fill='#e0c9a2')
contacts.save(OUT/'weapon-contacts.jpg',quality=94)
