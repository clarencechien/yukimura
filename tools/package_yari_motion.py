"""Validate Blender outputs and package transparent, fixed-pivot sprite atlases.

Pillow only downsizes/composites/packages actual rendered frames. No image AI.
"""
from pathlib import Path
import json, hashlib, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
RIGID='--rigid' in sys.argv
STUDY='yari-rigid' if RIGID else 'yari-motion'
OUT=ROOT/'docs/routes/jigoku-2d'/STUDY
TMP=ROOT/'.tmp'/STUDY
POSES=[1,11,15,27] if RIGID else [1,8,10,18]
PRESETS=['neutral','warm-left','cool-right']
FPS, COUNT = 30, 36
CLIPS={'thrust':(1,36),'idle':(37,72)}
W,H=512,320
report=json.loads((OUT/'motion-report.json').read_text())
assert report['fps']==FPS and report['frames_per_clip']==COUNT and len(report['frames'])==72
assert report['source_sha256']==hashlib.sha256((ROOT/report['source']).read_bytes()).hexdigest()
assert report['scene_sha256']==hashlib.sha256((ROOT/report['scene']).read_bytes()).hexdigest()
if RIGID:assert report['preview_only'] is False
source=np.array(Image.open(ROOT/report['source']))
light_checks=[]
for preset in PRESETS:
    plate=np.array(Image.open(OUT/('body-lights' if RIGID else 'lights')/f'{preset}.png'))
    assert np.array_equal(source[:,:,3],plate[:,:,3])
    difference=np.abs(source[:,:,:3].astype(int)-plate[:,:,:3].astype(int))[source[:,:,3]>240]
    if preset=='neutral':assert difference.max()<=1
    else:assert difference.mean()>1
    light_checks.append({'preset':preset,'source_alpha_exact':True,'mean_RGB_difference_from_source':float(difference.mean()),'max_RGB_difference':int(difference.max())})

manifest={'version':2,'frameSize':[W,H],'fps':FPS,'framesPerClip':COUNT,'direction':'single source view, facing screen-right',
          'pivot':{'x':.5,'y':.85},'pivotNote':'Stable canvas anchor. No root motion. Weapon-tip markers are reference data, not a collision system.',
          'gpuBytesPerAtlasRGBA8':3072*1920*4,'gpuBytesWithMipmapsApprox':round(3072*1920*4*4/3),
          'atlases':[],'clips':{'idle':{'loop':True},'thrust':{'loop':False,'contactFramesZeroBased':[14,15],'durationMs':1200}}}
frames={};checks=[]
for preset in PRESETS:
    frames[preset]=[Image.open(TMP/preset/f'{i:03}.png').convert('RGBA') for i in range(1,73)]
    for i,im in enumerate(frames[preset]):
        assert im.size==(W,H)
        a=np.array(im)[:,:,3]
        assert a.max()>240 and np.count_nonzero(a)>10000
        assert not a[:4].any() and not a[-4:].any() and not a[:,:4].any() and not a[:,-4:].any(), (preset,i,'cropped')
        if preset!='neutral':assert np.array_equal(a,np.array(frames['neutral'][i])[:,:,3])
    for clip,(start,end) in CLIPS.items():
        images=frames[preset][start-1:end]
        assert np.array_equal(np.array(images[0]),np.array(images[-1])),(preset,clip,'loop seam')
        assert np.mean(np.abs(np.array(images[0]).astype(float)-np.array(images[9]).astype(float)))>.05
        distinct=len({hashlib.sha256(im.tobytes()).hexdigest() for im in images})
        if clip=='thrust':assert distinct>24, 'Must render new in-between poses, not duplicate 24 old frames'
        atlas=Image.new('RGBA',(W*6,H*6))
        name=f'{clip}-{preset}'
        entries={}
        for i,im in enumerate(images):
            x,y=i%6*W,i//6*H;atlas.paste(im,(x,y))
            entries[f'{clip}-{i:02}']={'frame':{'x':x,'y':y,'w':W,'h':H},'rotated':False,'trimmed':False,
                'spriteSourceSize':{'x':0,'y':0,'w':W,'h':H},'sourceSize':{'w':W,'h':H},'pivot':manifest['pivot']}
        file=OUT/(name+'.webp');atlas.save(file,lossless=True,method=6)
        # Lossless RGBA foreground round-trip; encoders may discard hidden RGB.
        decoded=np.array(Image.open(file).convert('RGBA'));original=np.array(atlas)
        assert np.array_equal(decoded[:,:,3],original[:,:,3])
        mask=original[:,:,3]>0;assert np.array_equal(decoded[:,:,:3][mask],original[:,:,:3][mask])
        metadata={'frames':entries,'meta':{'app':'Yukimura illustration study','image':name+'.webp','format':'RGBA8888','size':{'w':W*6,'h':H*6},'scale':'1'}}
        (OUT/(name+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
        manifest['atlases'].append({'clip':clip,'light':preset,'image':name+'.webp','data':name+'.json','bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        checks.append({'clip':clip,'light':preset,'frameCount':COUNT,'distinctFrames':distinct,'closed_loop':True,'visible_motion':True,'webp_lossless_foreground':True})
(OUT/'atlas-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Larger optional atlases for desktop review. Do not load these on mobile by default.
manifest['desktopAtlases']=[]
manifest['desktopFrameSize']=[1024,640]
manifest['desktopGPUBytesPerClipRGBA8']=4096*(3840+1920)*4
manifest['desktopMaxPageSize']=[4096,3840]
for preset in PRESETS:
    hd=[Image.open(TMP/(preset+'-hd')/f'{i:03}.png').convert('RGBA') for i in range(1,73)]
    for im in hd:
        assert im.size==(1024,640)
        a=np.array(im)[:,:,3]
        assert a.max()>240 and not a[:4].any() and not a[-4:].any() and not a[:,:4].any() and not a[:,-4:].any()
    for clip,(start,end) in CLIPS.items():
        images=hd[start-1:end]
        assert np.array_equal(np.array(images[0]),np.array(images[-1]))
        pages=[]
        for first in [0,24]:
            chunk=images[first:first+24]
            name=f'{clip}-{preset}-hd'+('-2' if first else '')
            height=((len(chunk)+3)//4)*640
            atlas=Image.new('RGBA',(4096,height));entries={}
            for i,im in enumerate(chunk):
                x,y=(i%4)*1024,(i//4)*640;atlas.paste(im,(x,y))
                entries[f'{clip}-{first+i:02}']={'frame':{'x':x,'y':y,'w':1024,'h':640},'rotated':False,'trimmed':False,
                    'spriteSourceSize':{'x':0,'y':0,'w':1024,'h':640},'sourceSize':{'w':1024,'h':640},'pivot':manifest['pivot']}
            file=OUT/(name+'.webp');atlas.save(file,lossless=True,method=4)
            decoded=np.array(Image.open(file).convert('RGBA'));original=np.array(atlas);mask=original[:,:,3]>0
            assert np.array_equal(decoded[:,:,3],original[:,:,3]) and np.array_equal(decoded[:,:,:3][mask],original[:,:,:3][mask])
            (OUT/(name+'.json')).write_text(json.dumps({'frames':entries,'meta':{'image':name+'.webp','format':'RGBA8888','size':{'w':4096,'h':height},'scale':'1'}},indent=2)+'\n')
            pages.append({'firstFrame':first,'frameCount':len(chunk),'image':name+'.webp','data':name+'.json','bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        manifest['desktopAtlases'].append({'clip':clip,'light':preset,'pages':pages})
(OUT/'atlas-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# GitHub supports this GIF inline. It is a small review proxy, not game art.
preview=[]
for im in frames['warm-left'][:COUNT]:
    bg=Image.new('RGBA',(W,H),'#161b20');bg.alpha_composite(im);preview.append(bg.convert('RGB'))
palette=Image.new('RGB',(W*6,H*6))
for i,im in enumerate(preview):palette.paste(im,((i%6)*W,(i//6)*H))
palette=palette.quantize(colors=256)
gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in preview]
gifs[0].save(OUT/'thrust-preview.gif',save_all=True,append_images=gifs[1:],duration=[30,30,40]*12,loop=0,disposal=2,optimize=False)

# GIF timing is centisecond-quantized; MP4 is the exact constant-30-fps preview.
video_frames=TMP/'video-30';video_frames.mkdir(exist_ok=True)
for i,im in enumerate(preview):im.save(video_frames/f'{i:03}.png')
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(video_frames/'%03d.png'),'-frames:v',str(COUNT),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'thrust-preview-30fps.mp4')],check=True)
video=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,nb_frames,duration','-of','json',str(OUT/'thrust-preview-30fps.mp4')]))['streams'][0]
assert video['avg_frame_rate']=='30/1' and int(video['nb_frames'])==COUNT and abs(float(video['duration'])-1.2)<.001
with Image.open(OUT/'thrust-preview.gif') as gif:
    durations=[]
    for i in range(gif.n_frames):gif.seek(i);durations.append(gif.info['duration'])
    assert sum(durations)==1200

fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def font(n):return ImageFont.truetype(fontfile,n)
sheet=Image.new('RGBA',(1536,910),'#161b20');d=ImageDraw.Draw(sheet)
d.text((30,20),'六文劫 · 十文字槍動作與補光',font=font(32),fill='#eddbc5')
d.text((30,70),('固定長度手臂 → 肩肘腕求解 → 剛性貼圖旋轉' if RIGID else '同一插畫 → Blender 補光 → 固定視角連續變形'),font=font(21),fill='#a5afb2')
for i,(preset,label) in enumerate(zip(PRESETS,['中性','左暖火光','右冷鬼火'])):
    im=Image.open(OUT/f'{preset}-{POSES[2]:02}.png');im.thumbnail((512,320),Image.Resampling.LANCZOS)
    sheet.alpha_composite(im,(i*512,120));d.text((i*512+26,445),label,font=font(23),fill='#eddbc5')
for i,(f,label) in enumerate(zip(POSES,['持槍','蓄勢','短刺','收槍'])):
    im=Image.open(OUT/f'warm-left-{f:02}.png');im.thumbnail((384,240),Image.Resampling.LANCZOS)
    sheet.alpha_composite(im,(i*384,510));d.text((i*384+26,770),label,font=font(22),fill='#eddbc5')
d.text((30,846),'單方向試作 / 腳底固定 / 小幅動作 / 尚未接入正式遊戲',font=font(20),fill='#a5afb2')
sheet.convert('RGB').save(OUT/'comparison.jpg',quality=94)
validation={'passed':True,'framesChecked':432,'fps':FPS,'framesPerClip':COUNT,'video':video,'allFramesUncropped':True,'matchingAlphaAcrossLightsAt512':True,
    'lighting':light_checks,'clips':checks,'minTriangleAreaRatio':None if RIGID else min(f['min_triangle_area_ratio'] for f in report['frames']),
    'maxGripTranslationErrorSourcePixels':max(f['max_grip_error_source_px'] if RIGID else f['weapon_hand_translation_error_source_px'] for f in report['frames']),
    'maxFootAnchorDriftSourcePixels':max(f['foot_anchor_drift_source_px'] for f in report['frames']),
    'desktopAtlasesLosslessForeground':True,'scope':'Image-cage consistency checks, not human anatomy, sword/spear technique or game-performance validation.'}
if RIGID:
    validation['maxJointGapSourcePixels']=max(f['max_joint_gap_source_px'] for f in report['frames'])
    validation['maxLegLengthErrorSourcePixels']=max(f['max_leg_length_error_source_px'] for f in report['frames'])
    validation['maxRearHeelLiftSourcePixels']=max(f['rear_heel_lift_source_px'] for f in report['frames'])
    validation['maxRigidMatrixError']=max(f['max_rigid_matrix_error'] for f in report['frames'])
    validation['maxUpperArmLengthError']=max(a['upper_length_error'] for f in report['frames'] for a in f['arms'])
    validation['maxForearmLengthError']=max(a['forearm_length_error'] for f in report['frames'] for a in f['arms'])
    validation['maxWristAngleChangeDegrees']=max(abs(a['wrist_angle_change_degrees']) for f in report['frames'] for a in f['arms'])
    validation['scope']='Rigid image pieces and projected two-link IK consistency; not full anatomical/dynamics validation.'
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({'validation':validation,'totalAtlasBytes':sum(a['bytes'] for a in manifest['atlases'])},indent=2))
