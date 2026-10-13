"""Portable, script-free review page: embed proof and real Babylon screenshots."""
from pathlib import Path
import base64,html,json
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'renders/fullbody-v14'
def pic(path,caption):
    assert path.is_file(),path
    return '<figure><img loading="lazy" src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'" alt="'+html.escape(caption)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'
content=[]
for kind,label in [('yukimura','幸村'),('ieyasu','家康')]:
    content.append(f'<h2>{label}・實際遊戲模型</h2><div class="grid">')
    content.append(pic(ROOT/'renders/commanders-v13'/f'after-{kind}-idle-hands.png','調整前：固定手型接在簡化前臂'))
    content.append(pic(OUT/f'{kind}-idle-hands.png','調整後：連續蒙皮、分段轉腕與貼合護腕'))
    content.append(pic(OUT/f'{kind}-thrust-hands.png','突刺：保留握持位置，調整手掌與手肘方向'))
    content.append(pic(OUT/f'{kind}-idle-full.png','完整角色：共用人體骨架，保留各自盔甲與體型設定'))
    if kind=='yukimura':
        content.append(pic(OUT/'yukimura-slash-hands.png','橫掃：前臂旋轉連續，避免半途反向跳轉'))
        content.append(pic(OUT/'yukimura-dash-full.png','衝刺：朝前持槍，減少腕部反折'))
    content.append('</div>')
content.append('<h2>163 骨開源人體・Blender Cycles 變形驗證</h2><p>這是未做角色體型雕塑的 MPFB 原始人體底模，用來檢查連續網格與骨架。</p><div class="grid">')
for name,label in [('neutral','原始姿勢'),('elbow','屈肘'),('roll','前臂分段旋轉'),('wrist','手腕活動')]:content.append(pic(OUT/f'body-{name}.png',label))
content.append('</div>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>幸村與家康・全身骨架與腕部修正</title><style>body{margin:0;background:#141a1e;color:#eee9de;font:17px/1.7 system-ui}main{max-width:1200px;margin:auto;padding:24px}h1{font-size:30px}h2{margin-top:36px;font-size:23px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:0;background:#222c31}img{display:block;width:100%;height:auto}figcaption{padding:12px;font-size:15px}p{color:#c0c9cb}@media(max-width:650px){.grid{grid-template-columns:1fr}main{padding:16px}}</style><main><h1>幸村與家康・全身骨架與腕部修正</h1><p>MPFB／MakeHuman CC0・完整 163 骨作者版，遊戲版各 92 骨。連續肩臂與腕部蒙皮、30 根手指骨、分段前臂旋轉、獨立護腕甲片。角色圖為 Babylon.js 實際 GLB 畫面。</p><p>圖片全部內嵌，離線開啟也能查看。此頁為模型檢查，並非最終美術品質驗收。</p>'''+''.join(content)+'</main></html>'
(OUT/'index.html').write_text(page)
print('Embedded',page.count('<img '),'images;',len(page.encode()),'bytes')
