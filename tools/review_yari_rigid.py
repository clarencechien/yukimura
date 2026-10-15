"""Before/after timing-matched review and an annotated joint inspection plate."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/routes/jigoku-2d/yari-rigid';TMP=ROOT/'.tmp/yari-rigid'
old=Image.open(ROOT/'assets/source/jigoku-2d/yari-rigid/static-lower-baseline.webp').convert('RGBA')
fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font=lambda n:ImageFont.truetype(fontfile,n)
folder=TMP/'comparison';folder.mkdir(exist_ok=True)
frames=[]
for i in range(36):
    before=old.crop(((i%6)*512,(i//6)*320,(i%6+1)*512,(i//6+1)*320))
    after=Image.open(TMP/'neutral'/f'{i+1:03}.png').convert('RGBA')
    canvas=Image.new('RGBA',(1024,384),'#20262a');draw=ImageDraw.Draw(canvas)
    canvas.alpha_composite(before,(0,48));canvas.alpha_composite(after,(512,48))
    draw.text((22,10),'前版：下身固定',font=font(22),fill='#e8a59a')
    draw.text((534,10),'新版：骨盆前移・膝踝連動',font=font(22),fill='#9fdbca')
    im=canvas.convert('RGB');im.save(folder/f'{i:03}.png');frames.append(im)
palette=Image.new('RGB',(1024*6,384*6))
for i,im in enumerate(frames):palette.paste(im,((i%6)*1024,(i//6)*384))
palette=palette.quantize(colors=256)
gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
gifs[0].save(OUT/'before-after.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*12,loop=0,disposal=2,optimize=False)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(folder/'%03d.png'),'-frames:v','36','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'before-after-30fps.mp4')],check=True)
r=json.loads((OUT/'motion-report.json').read_text())
sheet=Image.new('RGB',(1536,720),'#20262a');d=ImageDraw.Draw(sheet)
d.text((24,18),'關節檢查：肩肘腕＋髖膝踝',font=font(27),fill='#e8dfd0')
for i,(frame,label) in enumerate([(1,'持槍'),(11,'蓄勢'),(15,'短刺')]):
    im=Image.open(OUT/f'neutral-{frame:02}.png').convert('RGBA')
    draw=ImageDraw.Draw(im)
    for chain in r['frames'][frame-1]['joints'].values():
        points=[(x+256,y+128) for x,y in chain]
        draw.line(points,fill='#73e0e0',width=5)
        for (x,y),color in zip(points,['#ef7c7c','#f1cf6e','#73e0e0']):draw.ellipse((x-10,y-10,x+10,y+10),fill=color)
    # Crop in on shoulders and hands for inspection, no pose manipulation.
    im=im.crop((370,260,1320,1170)).resize((512,490),Image.Resampling.LANCZOS)
    sheet.paste(im,(i*512,70),im);d.text((i*512+24,565),label,font=font(24),fill='#e8dfd0')
d.text((24,615),'骨盆先行、雙膝連動；前腳固定，後腳繞腳尖小幅抬跟。',font=font(23),fill='#9fdbca')
d.text((24,651),'固定肢段長度；沒有拉伸鎧甲。平面投影關節，並非動力學模擬。',font=font(20),fill='#aeb7b8')

sheet.save(OUT/'joint-check.jpg',quality=94)
print('Created before/after GIF, 30 fps video and joint inspection plate.')
