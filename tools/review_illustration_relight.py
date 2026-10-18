"""Checks original-vs-relight pixel layout; produces a labeled contact sheet.

Pillow only resizes/composites for the review sheet. Original Blender PNGs are
not retouched. Run after tools/render_illustration_relight.py.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/routes/jigoku-2d';OUT=BASE/'relight'
r=json.loads((OUT/'render-report.json').read_text())
source=ROOT/r['source'];src=np.array(Image.open(source));assert list(src.shape[1::-1])==r['source_dimensions']
assert hashlib.sha256(source.read_bytes()).hexdigest()==r['source_sha256']
assert hashlib.sha256((ROOT/r['scene']).read_bytes()).hexdigest()==r['scene_sha256']
assert hashlib.sha256((ROOT/r['surface_config']).read_bytes()).hexdigest()==r['surface_config_sha256']
assert {x['name'] for x in r['files']}=={'neutral','warm-left','cool-right'}
foreground=src[:,:,3]>240;assert foreground.sum()>100000
checks=[];rgb={}
for row in r['files']:
    p=OUT/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];im=np.array(Image.open(p));assert im.shape==src.shape
    alpha_changes=int(np.count_nonzero(im[:,:,3]!=src[:,:,3]));assert alpha_changes==0
    delta=np.abs(im[:,:,:3].astype(int)-src[:,:,:3].astype(int))[foreground]
    checks.append({'name':row['name'],'source_alpha_identical':True,'foreground_rgb_mean_absolute_difference_8bit':float(delta.mean()),'foreground_rgb_max_difference_8bit':int(delta.max()),'changed_foreground_pixels':int(np.any(delta>0,axis=1).sum())})
    rgb[row['name']]=im[:,:,:3]
assert checks[0]['name']=='neutral' and checks[0]['foreground_rgb_max_difference_8bit']<=1
for name in ['warm-left','cool-right']:
    assert np.mean(np.abs(rgb[name].astype(int)-rgb['neutral'].astype(int))[foreground])>1
# Compare the color response, not a falsely claimed geometric reconstruction.
validation={'passed':True,'source_pixel_dimensions':r['source_dimensions'],'alpha_identical_for_all_variants':True,'checks':checks,'method_verification':'Locked UV and camera; only a linear RGB gain changes. Exact source alpha retained. Neutral RGB differs by no more than one 8-bit quantization level.','scope':'Checks refer to the prepared single-character cutout, not pixel identity with the earlier multiview concept sheet.','blender_output_render_seconds':sum(x['seconds'] for x in r['files'])}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def font(size):return ImageFont.truetype(fontfile,size)
canvas=Image.new('RGBA',(1536,930),'#1b2326');draw=ImageDraw.Draw(canvas)
draw.text((28,18),'真田・六文劫 / 插畫 2.5D 補光試作',font=font(30),fill='#eee3d2')
draw.text((28,64),'同一透明人物・Blender 計算補光・造型與 Alpha 不變',font=font(20),fill='#aeb9ba')
for i,(name,label) in enumerate([('neutral','中性 / 原畫基準'),('warm-left','左側暖火光'),('cool-right','右側冷鬼火')]):
    im=Image.open(OUT/(name+'.png')).convert('RGBA');im.thumbnail((490,735),Image.Resampling.LANCZOS)
    canvas.alpha_composite(im,(i*512+(512-im.width)//2,105))
    draw.text((i*512+28,850),label,font=font(25),fill='#eee3d2')
canvas.convert('RGB').save(OUT/'comparison.jpg',quality=95,subsampling=0)
html='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>六文劫・插畫補光比較</title>
<style>:root{color-scheme:dark;background:#11191b;color:#e5dfd4;font-family:system-ui,sans-serif}*{box-sizing:border-box}body{max-width:1500px;margin:auto;padding:26px}h1{font-size:clamp(28px,4vw,46px);font-family:serif;margin-bottom:10px}p{line-height:1.8;color:#aeb9b8;max-width:980px}a{color:#e5b379}main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{background:#1b2326;padding:16px;min-width:0}article img{display:block;width:100%;height:auto}h2{font-size:21px}button{color:inherit;background:#303b3d;border:1px solid #637173;padding:11px 15px;border-radius:6px;margin:12px 0 24px;cursor:pointer}button[aria-pressed="true"]{border-color:#e5b379;color:#e5b379}.small{font-size:14px}.viewer{background:repeating-conic-gradient(#1b2326 0% 25%,#202a2d 0% 50%) 0/26px 26px}footer{padding:24px 0;line-height:1.8;color:#aeb9b8}.proxy{width:min(100%,260px);background:#1b2326}@media(max-width:680px){body{padding:16px}main{grid-template-columns:1fr}}</style>
<h1>保留插畫，改變補光</h1><p>三張圖共用同一人物與像素位置。原圖先經 image gen 整理為單人透明素材；其後由 Blender 以手工淺浮雕計算光照差異，不逐張重新生成角色。原畫陰影仍保留，這是補光合成，不是完整物理材質重建。</p>
<button id="original" aria-pressed="false">切換：三欄都顯示原始素材</button><p id="state" class="small" aria-live="polite">目前顯示 Blender 的三種光照結果。</p><main>'''
for name,label in [('neutral','中性・原畫基準'),('warm-left','左側暖火光'),('cool-right','右側冷鬼火')]:
 html+=f'<article><h2>{label}</h2><div class="viewer"><img data-variant="{name}" src="relight/{name}.png" alt="幸村插畫：{label}"></div><p class="small"><a href="relight/{name}.png">開啟 1024 × 1536 原圖</a></p></article>'
html+='''</main><footer><a href="RELIGHT_STUDY.md">製作與限制</a> · <a href="relight/validation.json">像素／透明邊界檢查</a> · <a href="relight/render-report.json">渲染記錄</a> · <a href="../../../assets/source/jigoku-2d/yukimura-illustration-cutout.png">原始透明素材</a><details><summary>查看實際補光表面（粗略方向，不是完整人物）</summary><p>白色表面由人工指定頭盔、胸甲等起伏構成。此圖不是美術成果，也沒有使用 Marigold／Depth Anything 推論。</p><img class="proxy" src="relight/surface-proxy.png" alt="手工淺浮雕光照代理"></details></footer>
<script>const button=document.querySelector('#original');let showOriginal=false;button.onclick=()=>{showOriginal=!showOriginal;button.setAttribute('aria-pressed',String(showOriginal));button.textContent=showOriginal?'返回：Blender 三種光照':'切換：三欄都顯示原始素材';document.querySelector('#state').textContent=showOriginal?'目前三欄皆為同一原始素材，可來回比對造型。':'目前顯示 Blender 的三種光照結果。';for(const img of document.querySelectorAll('[data-variant]'))img.src=showOriginal?'../../../assets/source/jigoku-2d/yukimura-illustration-cutout.png':`relight/${img.dataset.variant}.png`;};</script></html>'''
(BASE/'relight-review.html').write_text(html)
print(json.dumps(validation,indent=2))
