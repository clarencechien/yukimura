"""Validate Blender outputs and package transparent, fixed-pivot sprite atlases.

Pillow only downsizes/composites/packages actual rendered frames. No image AI.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/routes/jigoku-2d/yari-motion'
TMP=ROOT/'.tmp/yari-motion'
PRESETS=['neutral','warm-left','cool-right']
CLIPS={'thrust':(1,24),'idle':(25,48)}
W,H=512,320
report=json.loads((OUT/'motion-report.json').read_text())
assert report['source_sha256']==hashlib.sha256((ROOT/report['source']).read_bytes()).hexdigest()
assert report['scene_sha256']==hashlib.sha256((ROOT/report['scene']).read_bytes()).hexdigest()
source=np.array(Image.open(ROOT/report['source']))
light_checks=[]
for preset in PRESETS:
    plate=np.array(Image.open(OUT/'lights'/f'{preset}.png'))
    assert np.array_equal(source[:,:,3],plate[:,:,3])
    difference=np.abs(source[:,:,:3].astype(int)-plate[:,:,:3].astype(int))[source[:,:,3]>240]
    if preset=='neutral':assert difference.max()<=1
    else:assert difference.mean()>1
    light_checks.append({'preset':preset,'source_alpha_exact':True,'mean_RGB_difference_from_source':float(difference.mean()),'max_RGB_difference':int(difference.max())})

manifest={'version':1,'frameSize':[W,H],'fps':20,'framesPerClip':24,'direction':'single source view, facing screen-right',
          'pivot':{'x':.5,'y':.85},'pivotNote':'Stable canvas anchor. No root motion. Weapon-tip markers are reference data, not a collision system.',
          'gpuBytesPerAtlasRGBA8':3072*1280*4,'gpuBytesWithMipmapsApprox':round(3072*1280*4*4/3),
          'atlases':[],'clips':{'idle':{'loop':True},'thrust':{'loop':False,'contactFramesZeroBased':[9,10],'durationMs':1200}}}
frames={};checks=[]
for preset in PRESETS:
    frames[preset]=[Image.open(TMP/preset/f'{i:03}.png').convert('RGBA') for i in range(1,49)]
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
        atlas=Image.new('RGBA',(W*6,H*4))
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
        metadata={'frames':entries,'meta':{'app':'Yukimura illustration study','image':name+'.webp','format':'RGBA8888','size':{'w':W*6,'h':H*4},'scale':'1'}}
        (OUT/(name+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
        manifest['atlases'].append({'clip':clip,'light':preset,'image':name+'.webp','data':name+'.json','bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        checks.append({'clip':clip,'light':preset,'frameCount':24,'closed_loop':True,'visible_motion':True,'webp_lossless_foreground':True})
(OUT/'atlas-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Larger optional atlases for desktop review. Do not load these on mobile by default.
manifest['desktopAtlases']=[]
manifest['desktopFrameSize']=[1024,640]
manifest['desktopGPUBytesPerAtlasRGBA8']=4096*3840*4
for preset in PRESETS:
    hd=[Image.open(TMP/(preset+'-hd')/f'{i:03}.png').convert('RGBA') for i in range(1,49)]
    for im in hd:
        assert im.size==(1024,640)
        a=np.array(im)[:,:,3]
        assert a.max()>240 and not a[:4].any() and not a[-4:].any() and not a[:,:4].any() and not a[:,-4:].any()
    for clip,(start,end) in CLIPS.items():
        images=hd[start-1:end]
        assert np.array_equal(np.array(images[0]),np.array(images[-1]))
        name=f'{clip}-{preset}-hd';atlas=Image.new('RGBA',(4096,3840));entries={}
        for i,im in enumerate(images):
            x,y=(i%4)*1024,(i//4)*640;atlas.paste(im,(x,y))
            entries[f'{clip}-{i:02}']={'frame':{'x':x,'y':y,'w':1024,'h':640},'rotated':False,'trimmed':False,
                'spriteSourceSize':{'x':0,'y':0,'w':1024,'h':640},'sourceSize':{'w':1024,'h':640},'pivot':manifest['pivot']}
        file=OUT/(name+'.webp');atlas.save(file,lossless=True,method=4)
        decoded=np.array(Image.open(file).convert('RGBA'));original=np.array(atlas);mask=original[:,:,3]>0
        assert np.array_equal(decoded[:,:,3],original[:,:,3]) and np.array_equal(decoded[:,:,:3][mask],original[:,:,:3][mask])
        (OUT/(name+'.json')).write_text(json.dumps({'frames':entries,'meta':{'image':name+'.webp','format':'RGBA8888','size':{'w':4096,'h':3840},'scale':'1'}},indent=2)+'\n')
        manifest['desktopAtlases'].append({'clip':clip,'light':preset,'image':name+'.webp','data':name+'.json','bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(OUT/'atlas-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# GitHub supports this GIF inline. It is a small review proxy, not game art.
preview=[]
for im in frames['warm-left'][:24]:
    bg=Image.new('RGBA',(W,H),'#161b20');bg.alpha_composite(im);preview.append(bg.convert('RGB'))
palette=Image.new('RGB',(W*6,H*4))
for i,im in enumerate(preview):palette.paste(im,((i%6)*W,(i//6)*H))
palette=palette.quantize(colors=256)
gifs=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in preview]
gifs[0].save(OUT/'thrust-preview.gif',save_all=True,append_images=gifs[1:],duration=50,loop=0,disposal=2,optimize=False)

fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def font(n):return ImageFont.truetype(fontfile,n)
sheet=Image.new('RGBA',(1536,910),'#161b20');d=ImageDraw.Draw(sheet)
d.text((30,20),'六文劫 · 十文字槍動作與補光',font=font(32),fill='#eddbc5')
d.text((30,70),'同一插畫 → Blender 補光 → 固定視角連續變形',font=font(21),fill='#a5afb2')
for i,(preset,label) in enumerate(zip(PRESETS,['中性','左暖火光','右冷鬼火'])):
    im=Image.open(OUT/f'{preset}-10.png');im.thumbnail((512,320),Image.Resampling.LANCZOS)
    sheet.alpha_composite(im,(i*512,120));d.text((i*512+26,445),label,font=font(23),fill='#eddbc5')
for i,(f,label) in enumerate([(1,'持槍'),(8,'蓄勢'),(10,'短刺'),(18,'收槍')]):
    im=Image.open(OUT/f'warm-left-{f:02}.png');im.thumbnail((384,240),Image.Resampling.LANCZOS)
    sheet.alpha_composite(im,(i*384,510));d.text((i*384+26,770),label,font=font(22),fill='#eddbc5')
d.text((30,846),'單方向試作 / 腳底固定 / 小幅動作 / 尚未接入正式遊戲',font=font(20),fill='#a5afb2')
sheet.convert('RGB').save(OUT/'comparison.jpg',quality=94)
validation={'passed':True,'framesChecked':288,'allFramesUncropped':True,'matchingAlphaAcrossLightsAt512':True,
    'lighting':light_checks,'clips':checks,'minTriangleAreaRatio':min(f['min_triangle_area_ratio'] for f in report['frames']),
    'maxGripTranslationErrorSourcePixels':max(f['weapon_hand_translation_error_source_px'] for f in report['frames']),
    'maxFootAnchorDriftSourcePixels':max(f['foot_anchor_drift_source_px'] for f in report['frames']),
    'desktopAtlasesLosslessForeground':True,'scope':'Image-cage consistency checks, not human anatomy, sword/spear technique or game-performance validation.'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({'validation':validation,'totalAtlasBytes':sum(a['bytes'] for a in manifest['atlases'])},indent=2))
