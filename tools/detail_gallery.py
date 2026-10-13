"""Offline before/after proof: embedded, unretouched Babylon captures."""
from pathlib import Path
import base64,json,sys
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'renders/detail-v16'
rows=[('yukimura','idle','arms','幸村 · 雙倍腕部與束帶'),
      ('yukimura','idle','armor','幸村 · 胸甲、肩甲繫繩與包邊'),
      ('yukimura','idle','full','幸村 · 全身'),
      ('ieyasu','idle','arms','家康 · 雙倍腕部與束帶'),
      ('ieyasu','idle','armor','家康 · 黑金甲冑共用細節'),
      ('ieyasu','idle','full','家康 · 全身'),
      ('ashigaru','idle','armor','赤備足輕 · 共用零件的簡化版'),
      ('tokugawa','idle','armor','德川足輕 · 同套零件與材質'),
      ('yukimura','thrust','arms','幸村 · 突刺握持'),
      ('ieyasu','thrust','arms','家康 · 突刺握持')]
sections=[]
for kind,clip,view,title in rows:
    commander=kind in ('yukimura','ieyasu');figures=[]
    for version,label in [('physique' if commander else 'detail-base','之前 · v15' if commander else '之前 · 基礎小兵'),('detail','現在 · v16')]:
        data=base64.b64encode((OUT/f'{kind}-{version}-{clip}-{view}.png').read_bytes()).decode()
        figures.append(f'<figure><figcaption>{label}</figcaption><img alt="{title} · {label}" src="data:image/png;base64,{data}"></figure>')
    sections.append(f'<section><h2>{title}</h2><div class="pair">'+''.join(figures)+'</div></section>')
html='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>共用甲冑套件 · v16</title><style>
*{box-sizing:border-box}body{margin:0;padding:24px;background:#141c20;color:#e8e2d4;font:16px/1.7 system-ui,sans-serif}main{max-width:1200px;margin:auto}h1{font-size:28px}h2{font-size:20px;margin:28px 0 8px}p{max-width:980px;color:#c4cccb}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0;min-width:0}figcaption{padding:8px 12px;background:#273336}img{width:100%;height:auto;display:block}table{border-collapse:collapse}td,th{text-align:left;padding:8px 16px;border-bottom:1px solid #465255}@media(max-width:600px){body{padding:12px}.pair{gap:6px}figcaption{font-size:13px;padding:6px}h1{font-size:22px}td,th{padding:6px}}
</style><main><h1>共用甲冑套件 · 雙倍腕部與構造細節</h1>
<p>實際 GLB／Babylon.js 遊戲畫面，未使用 AI 修圖。前後採相同相機、光線與動作時間；20 張 PNG 內嵌，離線可看。</p>
<p>兩位主將的腕部指定截面，相對 v15 沿骨軸的橫截面尺寸為 2 倍；前臂與掌根逐漸銜接。新增貼合束帶、交叉繫繩、金屬孔圈、甲片細包邊，以及共用的細微法線／粗糙度貼圖。</p>
<p>四種角色共用同一套零件生成器。小兵使用較少幾何的版本，沿用既有圖集、單一材質與 18 骨；主將共用新增的配件貼圖。四種角色在同一場景共用兩張材質細節紋理。</p>
<table><tr><th>角色</th><th>三角形</th><th>材質</th><th>骨骼</th></tr>
<tr><td>幸村</td><td>76,625</td><td>4</td><td>92</td></tr><tr><td>家康</td><td>73,775</td><td>4</td><td>92</td></tr>
<tr><td>赤備足輕</td><td>3,650</td><td>1</td><td>18</td></tr><tr><td>德川足輕</td><td>3,506</td><td>1</td><td>18</td></tr></table>
<p>本輪建模與匯出使用 CPU，沒有 Modal 或付費 GPU 工作。遊戲使用裝置 GPU；這裡的 Chromium 檢查使用軟體 GPU，未量測手機效能。</p>
<p>這版增加可見構造，仍未達到插畫精細度。面甲、肩甲懸掛、掌根的誇張比例，以及布革摺痕與磨損分布仍需精修。此頁為 v16 模型比較；遊戲可從網站根目錄開啟。</p>
'''+''.join(sections)+'</main></html>'
(OUT/'index.html').write_text(html)
if '--publish' in sys.argv:
    public=ROOT/'public/review';public.mkdir(parents=True,exist_ok=True)
    (public/'index.html').write_text(html)
print('20 embedded screenshots:',OUT/'index.html')
