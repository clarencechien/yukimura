"""Portable, script-free before/after gallery of actual Babylon screenshots."""
from pathlib import Path
import base64
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/physique-v15'
rows=[('yukimura','idle','full','幸村 · 全身'),
      ('yukimura','idle','arms','幸村 · 前臂與腕部'),
      ('yukimura','thrust','full','幸村 · 突刺'),
      ('yukimura','dash','full','幸村 · 衝刺'),
      ('ieyasu','idle','full','家康 · 全身'),
      ('ieyasu','idle','arms','家康 · 前臂與腕部'),
      ('ieyasu','thrust','full','家康 · 突刺'),
      ('ieyasu','fall','full','家康 · 倒地')]
sections=[]
for kind,clip,view,title in rows:
    images=[]
    for version,label in [('fullbody','之前 · v14'),('physique','現在 · v15')]:
        data=base64.b64encode((OUT/f'{kind}-{version}-{clip}-{view}.png').read_bytes()).decode()
        images.append(f'<figure><figcaption>{label}</figcaption><img alt="{title} · {label}" src="data:image/png;base64,{data}"></figure>')
    sections.append(f'<section><h2>{title}</h2><div class="pair">'+''.join(images)+'</div></section>')
html='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>武將體格 · v14 / v15</title><style>
*{box-sizing:border-box}body{margin:0;padding:24px;background:#141c20;color:#e8e2d4;font:16px/1.7 system-ui,sans-serif}main{max-width:1200px;margin:auto}h1{font-size:28px}h2{font-size:20px;margin:28px 0 8px}p{max-width:920px;color:#c4cccb}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0;min-width:0}figcaption{padding:8px 12px;background:#273336}img{width:100%;height:auto;display:block}a{color:#d9b677}@media(max-width:600px){body{padding:12px}.pair{gap:6px}figcaption{font-size:13px;padding:6px}h1{font-size:22px}}
</style><main><h1>武將體格 · 同角度前後比較</h1>
<p>實際遊戲 GLB，Babylon.js 即時渲染。每組相機、光線、動作與時間一致；16 張圖片全部內嵌，離線開啟亦可顯示。</p>
<p>上臂與近肘前臂增加厚度，往手腕收窄；胸背與腿部一起調整。家康比幸村更厚實。保留原骨架、指骨與武器握持，沒有增加面數或新貼圖。深色布料略提亮，讓輪廓可讀。</p>
<p>這是體格修正，尚非寫實雕刻成品。肩甲抬臂時外翻、手指握持表面與皮革皺褶仍待精修。此頁比較本機 v14 / v15；本次未部署 GitHub Pages。</p>
'''+''.join(sections)+'</main></html>'
(OUT/'index.html').write_text(html)
print('Embedded 16 screenshots:',OUT/'index.html')
