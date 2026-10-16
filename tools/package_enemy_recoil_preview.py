"""Real Phaser footage and matched before/after frames; no generated animation."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat';TMP=ROOT/'.tmp/enemy-recoil';BASE='a0ddb54c47f808650a3a706e6cc0732593acf806'
rows=json.loads((OUT/'enemy-recoil-capture.json').read_text());frames=sorted((TMP/'frames').glob('*.png'));assert len(rows)==len(frames)==60
assert rows[-1]['hp']==2 and all(r['duel']['playerHP']==3 for r in rows)
assert any(r['enemy'].get('bodyReaction',{}).get('from',{}).get('intent')=='windup' for r in rows if r['enemy'].get('bodyReaction'))
assert any(r['hp']==2 and r['enemy']['phase']=='guard' and r['duel']['stage']=='recovery' and r['enemyBodyPose']['angle']==0 for r in rows)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(TMP/'frames/%03d.png'),'-frames:v','60','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'enemy-recoil-30fps.mp4')],check=True)
images=[Image.open(p).convert('RGB').resize((640,400),Image.Resampling.LANCZOS) for p in frames]
sheet=Image.new('RGB',(640*6,400*10))
for i,im in enumerate(images):sheet.paste(im,((i%6)*640,(i//6)*400))
palette=sheet.quantize(colors=256);gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
gifs[0].save(OUT/'enemy-recoil-preview.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*20,loop=0,disposal=1,optimize=True)
decoded=Image.open(OUT/'enemy-recoil-preview.gif');assert decoded.n_frames==60
for i,expected in enumerate(gifs):
 decoded.seek(i);assert ImageChops.difference(decoded.convert('RGB'),expected.convert('RGB')).getbbox() is None
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(OUT/'enemy-recoil-30fps.mp4')]))['streams'][0]
assert probe['avg_frame_rate']=='30/1' and int(probe['nb_read_frames'])==60 and abs(float(probe['duration'])-2)<.001
# Previous committed duel has a nonfatal counterattack: use the same counterattack
# in this run for comparison, separately from the new windup-interrupt clip above.
old=lambda n:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{n}'],cwd=ROOT)
(TMP/'before.mp4').write_bytes(old('duel-30fps.mp4'))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(TMP/'before.mp4'),'-start_number','0',str(TMP/'before-%03d.png')],check=True)
previous=json.loads(old('duel-capture.json'));current=json.loads((OUT/'duel-capture.json').read_text())
plate=Image.new('RGB',(1200,1305),'#1b2328');font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22);draw=ImageDraw.Draw(plate)
draw.text((18,12),'前輪 · 命中後切換整身反應圖',font=font,fill='#e0c9a2');draw.text((618,12),'本輪 · 保持同一軀幹，受擊再回防',font=font,fill='#e0c9a2')
selected=[]
for i,(age,label) in enumerate([(0,'命中與停頓：保持當下姿勢'),(95,'受力：胸甲後仰、持刀手收回'),(300,'回防：同一副身體逐步回正')]):
 row=min((r for r in current if r['enemy'].get('bodyReaction')),key=lambda r:abs(r['enemy']['bodyReaction']['age']-age))
 candidates=[r for r in previous if r['hp']==row['hp'] and r['duel']['playerHP']==row['duel']['playerHP'] and r['duel']['recoveryFrom']=='hit' and r['phase']==row['phase'] and r['frame']==row['frame']]
 before=min(candidates,key=lambda r:abs(r['duel']['age']-row['duel']['age']));offset=row['duel']['age']-before['duel']['age'];assert abs(offset)<=17
 for x,p in [(0,TMP/f"before-{before['sample']:03d}.png"),(600,ROOT/f".tmp/duel-check/frames/{row['sample']:03d}.png")]:
  im=Image.open(p).convert('RGB');assert im.size==(1200,750);plate.paste(im.resize((600,375),Image.Resampling.LANCZOS),(x,50+i*415))
 draw.text((18,428+i*415),label,font=font,fill='#e0c9a2')
 selected.append({'beforeSample':before['sample'],'afterSample':row['sample'],'attackFrame':row['frame'],'beforeRecoveryAgeMS':before['duel']['age'],'afterRecoveryAgeMS':row['duel']['age'],'stageOffsetMS':offset,'reactionAgeMS':row['enemy']['bodyReaction']['age']})
plate.save(OUT/'enemy-recoil-comparison.jpg',quality=94)
(OUT/'enemy-recoil-video-check.json').write_text(json.dumps({'passed':True,'video':probe,'source':'60 actual Phaser screenshots at controlled 33/33/34 ms, no effects; windup interrupted by thrust, one hit, no player damage. Not a hardware FPS benchmark.','gif':'60 frames, 30/30/40 ms, decoded pixel equality passed','comparison':{'baselineCommit':BASE,'selected':selected,'source':'Separate existing counterattack sequence: baseline MP4 vs current native PNG, matched attack frame, HP and hit-recovery stage; <=17 ms timing offset explicitly recorded.'},'limits':'Nonfatal upper thrust only. Low hits, fatal transition and death retain authored silhouettes. Planar rigid parts, not anatomical force simulation.'},indent=2)+'\n')
print('Verified interruption capture: 60 frames, 30 fps, 2 seconds; matched counterattack comparison:',selected)
