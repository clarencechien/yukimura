"""Encode actual browser screenshots; no generated or interpolated motion frames."""
from pathlib import Path
import json,subprocess,sys
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

# Preserve historical comparison plates when only updating current playback.
if '--video-only' in sys.argv: sys.exit(0)

# Inspect authored enemy transitions using the exact captured browser frames.
rows=json.loads((OUT/'capture-timing.json').read_text())
inspection=Image.new('RGB',(1536,1920),'#1b2328')
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22)
for i,(phase,label) in enumerate([('guard','戒備'),('flinch','輕受擊'),('hurt','後仰'),('buckle','重心下沉'),('crouch','屈膝'),('kneel','跪下'),('brace','手掌承重'),('yield','屈肘承重'),('sink','落胯過渡'),('lower','屈肘落胯'),('settle','側身落地'),('fallen','伏地'),('dissolve','消散'),('gone','離場')]):
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

# Shoulder positions come from the actual captured runtime, not a separate mockup.
phases=['brace','yield','sink','lower']
selected=[next(r for r in rows if r['enemy']['phase']==phase) for phase in phases]
distance=lambda a,b: ((a['x']-b['x'])**2+(a['y']-b['y'])**2)**.5
shoulders=[r['renderedArm']['shoulder'] for r in selected]
steps=[distance(a,b) for a,b in zip(shoulders,shoulders[1:])]
baseline=distance(shoulders[0],shoulders[-1])
assert max(steps)<baseline*.55
report={'scope':'Only brace → yield → sink → lower; manually authored shoulder anchors. Not a measurement of mesh continuity, foot sliding, or every body transition.',
        'previousDirectWorldStep':baseline,'currentWorldSteps':steps,'maxStepReductionPercent':100*(1-max(steps)/baseline),
        'samples':[{'phase':r['enemy']['phase'],'sample':r['sample'],'body':r['body'],'shoulder':r['renderedArm']['shoulder']} for r in selected]}
(OUT/'shoulder-check.json').write_text(json.dumps(report,indent=2)+'\n')
plate=Image.new('RGB',(1440,340),'#1b2328')
for i,(r,label) in enumerate(zip(selected,['手掌承重','屈肘承重','落胯過渡','屈肘落胯'])):
    crop=Image.open(TMP/f"{r['sample']:03}.png").convert('RGB').crop((720,290,1200,690)).resize((360,300),Image.Resampling.LANCZOS)
    plate.paste(crop,(i*360,0))
    point=r['renderedArm']['shoulder'];x=i*360+(point['x']-720)*.75;y=(point['y']-290)*.75
    draw=ImageDraw.Draw(plate);draw.ellipse((x-4,y-4,x+4,y+4),outline='#72e4ef',width=2)
    draw.text((i*360+12,304),label,font=font,fill='#e0c9a2')
plate.save(OUT/'shoulder-transitions.jpg',quality=94)
print(f'Shoulder steps: {baseline:.2f} px direct → {max(steps):.2f} px maximum with authored transitions.')

# The top strip is an archived browser capture from 6100c07, not a reconstruction.
comparison=Image.new('RGB',(1440,740),'#1b2328')
for y,name,label in [(0,'proportion-before.jpg','前輪 6100c07 · 頭盔與肩甲偏大'),(370,'shoulder-transitions.jpg','本輪 · 比例重繪、接點重標與掌下接觸陰影')]:
    ImageDraw.Draw(comparison).text((16,y+3),label,font=font,fill='#e0c9a2')
    comparison.paste(Image.open(OUT/name).convert('RGB'),(0,y+30))
comparison.save(OUT/'proportion-comparison.jpg',quality=94)

# Recoil study: three actual browser frames. Foot measurements use manually authored sole
# centers projected through the same body transform, not tracked physical contacts.
rig=json.loads((OUT/'enemy-rig.json').read_text())
recoil=Image.new('RGB',(1152,480),'#1b2328')
recoil_rows=[]
for i,(phase,label) in enumerate([('hurt','後仰'),('buckle','重心下沉'),('crouch','屈膝')]):
    row=next(r for r in rows if r['enemy']['phase']==phase)
    crop=Image.open(TMP/f"{row['sample']:03}.png").convert('RGB').crop((760,160,1200,650)).resize((384,428),Image.Resampling.LANCZOS)
    recoil.paste(crop,(i*384,0))
    ImageDraw.Draw(recoil).text((i*384+18,440),label,font=font,fill='#e0c9a2')
    binding=rig['bindings'][row['enemy']['pose']]
    recoil_rows.append({'phase':phase,'sample':row['sample'],'shoulder':row['renderedArm']['shoulder'],'soleCentersHD':binding['footContacts']})
recoil.save(OUT/'recoil-after.jpg',quality=94)
comparison=Image.new('RGB',(1152,1020),'#1b2328')
for y,name,label in [(0,'recoil-before.jpg','前輪 80c217c · 中間幀站距突然加寬'),(510,'recoil-after.jpg','本輪 · 收窄站距、屈膝回正與雙腳接觸陰影')]:
    ImageDraw.Draw(comparison).text((16,y+3),label,font=font,fill='#e0c9a2')
    comparison.paste(Image.open(OUT/name).convert('RGB'),(0,y+30))
comparison.save(OUT/'recoil-comparison.jpg',quality=94)
old_feet=[[[461,688],[681,665]],[[350,678],[765,677]],[[448,684],[729,686]]]
new_feet=[r['soleCentersHD'] for r in recoil_rows]
foot_steps=lambda poses: [[sum((a-b)**2 for a,b in zip(poses[j][i],poses[j+1][i]))**.5*rig['worldScale'] for i in range(2)] for j in range(2)]
report={'scope':'Manually inspected projected sole centers, not optical flow or a physical foot-lock measurement. Shoulder coordinates are actual runtime layer origins.',
        'previousCommit':'80c217c6c57c7aecd039604428f99afca13bb4f4','previousSoleCentersHD':old_feet,
        'previousFootStepsWorld':foot_steps(old_feet),'currentFootStepsWorld':foot_steps(new_feet),'samples':recoil_rows}
(OUT/'recoil-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared three-pose recoil comparison and explicitly marked manual foot measurements.')
