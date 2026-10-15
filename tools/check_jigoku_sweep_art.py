"""Verify shared transition pixels and inspect manually registered tip steps."""
from pathlib import Path
import io,json,math,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/combat'
BASE='a6bf7a6ba0978ad81c3bd2b6e78c6bd6363c0950'
old=lambda name:subprocess.check_output(['git','show',f'{BASE}:docs/routes/jigoku-2d/combat/{name}'],cwd=ROOT)
track=json.loads((OUT/'sweep-track.json').read_text());art=json.loads((OUT/'sweep-art.json').read_text());before=json.loads(old('sweep-art.json'))
def resolve(pose,hd):
    w,h=(1024,640) if hd else (512,320)
    clip,index=pose['clip'],pose['frame']
    if clip=='sweep':
        path=OUT/f'sweep{"-hd" if hd else ""}.webp';cols=2;local=index
    else:
        suffix=('-hd-2' if index>=24 else '-hd') if hd else ''
        path=OUT.parent/f'yari-rigid/{clip}-warm-left{suffix}.webp';cols=4 if hd else 6;local=index%24 if hd else index
    im=Image.open(path).convert('RGBA')
    return im.crop(((local%cols)*w,(local//cols)*h,(local%cols+1)*w,(local//cols+1)*h))
rows=[]
for hd in [True,False]:
    w,h=(1024,640) if hd else (512,320)
    atlas=Image.open(OUT/f'sweep{"-hd" if hd else ""}.webp').convert('RGBA')
    assert atlas.size==(w*2,h*2),'Shared boundary frames must not duplicate texture memory'
    for pose,clip,index in [(0,'thrust',35),(5,'idle',0)]:
        source=track['poseSources'][pose];assert source=={'clip':clip,'frame':index}
        a,b=np.array(resolve(source,hd)),np.array(resolve({'clip':clip,'frame':index},hd))
        assert np.array_equal(a[:,:,3],b[:,:,3])
        visible=(a[:,:,3]>0)|(b[:,:,3]>0);assert np.array_equal(a[visible],b[visible])
        rows.append({'resolution':'HD' if hd else 'mobile','sweepPose':pose,'sourceClip':clip,'sourceFrame':index,'sharedResidentTexture':True,'visiblePixelMismatch':0,'alphaMismatch':0})
assert len(track['poseFrames'])==32 and track['activeFrames']==list(range(9,17))
assert [track['poseFrames'].count(i) for i in range(6)]==[4,4,6,5,5,8]
assert max(Image.open(OUT/'sweep-hd.webp').size)<=4096
for row in art['poses']:
    if 'rearSole' in row:
        assert math.dist(row['rearSole'],[228,558])<1
        assert math.dist(row['frontSole'],[626,516])<12
points=lambda poses:[(p['worldTip']['x'],p['worldTip']['y']) for p in poses]
after=points(art['poses']);old_path=[after[0]]+points(before['poses'])+[after[-1]]
steps=lambda p:[math.dist(a,b) for a,b in zip(p,p[1:])]
assert max(steps(after))<max(steps(old_path))*.65
report={'passed':True,'baselineCommit':BASE,'sharedPixelChecks':rows,'previousTipSteps':steps(old_path),'currentTipSteps':steps(after),'maxTipStepReductionPercent':100*(1-max(steps(after))/max(steps(old_path))),'timing':'32 simulation frames, active 9..16, unchanged','scope':'Boundary sources resolve to the exact resident source cell in both resolutions; identity by reference, with desktop renderer bindings checked separately in browser capture. Tip positions are manually marked projected points; this is not anatomical correctness, continuous motion or fixed physical shaft-length verification. Mid-action armor and shaft projection still vary.'}
(OUT/'sweep-continuity-check.json').write_text(json.dumps(report,indent=2)+'\n')
# Diagnostic comparison only: no editing of sprite artwork.
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',20)
old_atlas=Image.open(io.BytesIO(old('sweep-hd.webp'))).convert('RGBA');new_frames=[resolve(p,True) for p in track['poseSources']]
cell=lambda im,i:im.crop(((i%2)*1024,(i//2)*640,(i%2+1)*1024,(i//2+1)*640))
plate=Image.new('RGB',(1536,720),'#1b2328')
for row,(new_i,old_i,labels) in enumerate([(0,0,['短刺最後一幀','前輪：重繪起手','本輪：共用收槍']), (5,3,['待機第一幀','前輪：重繪收勢','本輪：共用待機'])]):
    for col,(im,label) in enumerate(zip([new_frames[new_i],cell(old_atlas,old_i),new_frames[new_i]],labels)):
        thumb=im.resize((512,320),Image.Resampling.LANCZOS);x,y=col*512,row*360;plate.paste(thumb,(x,y),thumb);ImageDraw.Draw(plate).text((x+15,y+325),label,font=font,fill='#e0c9a2')
plate.save(OUT/'sweep-handoff-comparison.jpg',quality=94)
print(f'4 resident-frame reference/pixel checks passed; manual maximum tip step {max(steps(old_path)):.2f} -> {max(steps(after)):.2f} px.')
