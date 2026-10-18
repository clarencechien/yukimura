"""Validate rendered files and assemble honest size comparisons (Pillow only).

No generative retouch, sharpening, or replacement of the Blender render.
Run after render_jigoku_study.py: python3 tools/review_jigoku_study.py
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont,ImageChops
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/routes/jigoku-2d';OUT=BASE/'renders'
report=json.loads((OUT/'render-report.json').read_text())
assert not report['draft']
assert report['source_sha256']==hashlib.sha256((ROOT/report['source']).read_bytes()).hexdigest()
assert report['editable_scene_sha256']==hashlib.sha256((ROOT/report['editable_scene']).read_bytes()).hexdigest()
poses=['ready','windup','strike'];labels=['持槍 / READY','蓄勢 / WINDUP','刺出 / STRIKE']
assert {(r['pose'],r['mode'],r['width']) for r in report['files']}=={(p,m,size) for p in poses for m,size in [('sprite',512),('sprite',1024),('stage',1024)]}
checks=[]
for row in report['files']:
    p=OUT/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],p
    im=Image.open(p);assert im.mode=='RGBA' and im.size==(row['width'],row['height'])
    bounds=im.getchannel('A').getbbox();assert bounds and im.getchannel('A').getextrema()==(0,255)
    if row['mode']=='sprite':
        assert min(bounds[0],bounds[1],im.width-bounds[2],im.height-bounds[3])>im.width*.04,('clipped sprite',p,bounds)
        assert row['camera_scale']==report['camera']['scale'] and row['camera_location']==report['camera']['location']
    checks.append({'file':p.name,'alpha_bounds':bounds,'bytes':p.stat().st_size})
# A single pixel pivot represents the same fixed world origin in all source frames.
assert 0<report['pivot_normalized_top_left'][0]<1 and 0<report['pivot_normalized_top_left'][1]<1
for p in poses[1:]:
    assert ImageChops.difference(Image.open(OUT/f'ready-sprite-1024.png'),Image.open(OUT/f'{p}-sprite-1024.png')).getbbox() is not None
font_path=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if not font_path.exists():raise RuntimeError('Install Noto Sans CJK fonts to generate the labeled comparison sheet')
def font(size):return ImageFont.truetype(str(font_path),size)
def label(draw,pos,text,size=24,color='#d4d0c4'):draw.text(pos,text,font=font(size),fill=color)
def composite(canvas,path,rect):
    im=Image.open(path).convert('RGBA');im.thumbnail((rect[2],rect[3]),Image.Resampling.LANCZOS)
    canvas.alpha_composite(im,(rect[0]+(rect[2]-im.width)//2,rect[1]+(rect[3]-im.height)//2))
# 3 poses, unchanged camera, no per-pose crop: transparent PNGs laid onto neutral.
board=Image.new('RGBA',(1536,820),'#1b2023');draw=ImageDraw.Draw(board)
label(draw,(34,20),'真田・六文劫  /  Blender 三幀試渲',32)
label(draw,(34,72),'Cycles CPU · v22 幾何／握姿 · 固定正交相機 · 非 image gen',20,'#a8aaa6')
for i,(p,title) in enumerate(zip(poses,labels)):
    x=i*512
    composite(board,OUT/f'{p}-sprite-1024.png',(x,115,512,512))
    label(draw,(x+28,637),title,25)
    label(draw,(x+28,681),'1024 原始渲染 → 此處顯示 512',18,'#a8aaa6')
label(draw,(34,748),'造型驗證：既有模型仍偏簡化；尚未達成概念圖的甲冑與布料精細度。',21)
board.convert('RGB').save(OUT/'three-poses.jpg',quality=94,subsampling=0)
# Equal DISPLAY size, independently rendered SOURCE resolutions, no sharpening.
board=Image.new('RGBA',(1200,720),'#1b2023');draw=ImageDraw.Draw(board)
label(draw,(26,18),'相同顯示尺寸：512 與 1024 原生渲染比較',28)
label(draw,(26,65),'每格畫布 160 × 160 px；不是角色全身高度 160 px。無額外銳化。',18,'#a8aaa6')
for col,(p,title) in enumerate(zip(poses,labels)):
    x=col*400;label(draw,(x+24,118),title,23)
    for j,size in enumerate([512,1024]):
        y=170+j*240
        composite(board,OUT/f'{p}-sprite-{size}.png',(x+120,y,160,160))
        label(draw,(x+50,y+174),f'來源 {size} px → 顯示 160 px',18)
board.convert('RGB').save(OUT/'size-comparison.jpg',quality=95,subsampling=0)
checks={'passed':True,'source_unchanged':True,'render_files_checked':len(checks),'image_checks':checks,'total_render_seconds':sum(r['seconds'] for r in report['files']),'note':'Pixel bounds, hashes, fixed projection and distinct poses; not anatomical or performance certification.'}
(OUT/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>六文劫 · Blender 三幀試渲</title>
<style>:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#111719;color:#e7e2d7}*{box-sizing:border-box}body{max-width:1440px;margin:auto;padding:28px}h1{font-family:serif;font-size:clamp(28px,4vw,48px);margin-bottom:12px}p{max-width:900px;line-height:1.8;color:#bbbfb9}a{color:#dda36a}header small{letter-spacing:.2em;color:#c66459}.toolbar{display:flex;gap:16px;flex-wrap:wrap;align-items:center;padding:18px 0}label{display:flex;gap:8px;align-items:center}select{padding:8px;background:#222d31;border:1px solid #4b5558;color:inherit}main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.card{background:#1b2327;padding:14px;min-width:0}.viewport{width:100%;overflow:auto;min-height:240px;display:grid;place-items:center;background:repeating-conic-gradient(#1b2327 0% 25%,#222a2e 0% 50%) 50%/24px 24px}.viewport img{display:block;max-width:100%;height:auto}h2{font-size:19px}.caption{font-size:14px;color:#aaa}section{margin-top:32px}.sheet{display:block;width:100%;height:auto}footer{padding:30px 0;line-height:1.8;color:#999}@media(max-width:720px){body{padding:16px}main{grid-template-columns:1fr}.viewport{min-height:160px}}</style>
<header><small>ROKUMON · OFFLINE RENDER STUDY 01</small><h1>六文劫・持槍、蓄勢、刺出</h1><p>真正的 Blender Cycles CPU 渲染。重用 v22 模型與握姿，測試赤漆、布料、濕石與固定俯視相機；此頁是三個關鍵幀的檢視器，不是完成的動畫或可玩遊戲。模型仍未達到生成參考圖的精細度。</p></header>
<div class="toolbar"><label>內容<select id="mode"><option value="sprite">透明角色</option><option value="stage">場景與光影</option></select></label><label>原始解析度<select id="resolution"><option value="1024">1024 px</option><option value="512">512 px</option></select></label><label>顯示畫布<select id="display"><option value="fit">符合欄寬</option><option value="160">160 px</option><option value="256">256 px</option><option value="native">原始像素（可捲動）</option></select></label></div>
<main>'''
for p,title in zip(poses,labels):
 html+=f'<article class="card"><h2>{title}</h2><div class="viewport"><img data-pose="{p}" src="renders/{p}-sprite-1024.png" alt="幸村{title}的 Blender 渲染"></div><p class="caption">同一相機／地面原點 · <a data-download="{p}" href="renders/{p}-sprite-1024.png">開啟原圖</a></p></article>'
html+='''</main><section><h2>在相同遊戲尺寸比較</h2><p>下圖將獨立渲染的 512／1024 素材都縮到 160 px 畫布。若差異很小，優先省下貼圖記憶體；實體手機效能尚未量測。</p><img class="sheet" src="renders/size-comparison.jpg" alt="三個姿勢在相同 160 像素畫布比較兩種來源解析度"></section><footer>角色沿用 87,087 三角形／92 骨架；未新增高模雕刻。角色與場景使用不同構圖倍率，各自的三幀倍率一致。透明角色未包含獨立投影圖層。<br><a href="BLENDER_STUDY.md">製作與限制</a> · <a href="renders/render-report.json">渲染記錄</a> · <a href="renders/validation.json">檢查結果</a> · <a href="README.md">美術路線與概念圖</a></footer>
<script>const mode=document.querySelector('#mode'),resolution=document.querySelector('#resolution'),display=document.querySelector('#display');function update(){const stage=mode.value==='stage';resolution.disabled=stage;const size=stage?'1024':resolution.value;for(const img of document.querySelectorAll('[data-pose]')){const url=`renders/${img.dataset.pose}-${mode.value}-${size}.png`;img.src=url;document.querySelector(`[data-download="${img.dataset.pose}"]`).href=url;img.style.width=display.value==='fit'?'100%':(display.value==='native'?size:display.value)+'px';img.style.maxWidth=display.value==='native'?'none':'100%';}}for(const el of [mode,resolution,display])el.addEventListener('change',update);update();</script></html>'''
(BASE/'review.html').write_text(html)
print(json.dumps(checks,ensure_ascii=False,indent=2))
