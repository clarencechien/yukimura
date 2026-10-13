"""Portable before/after gallery; all actual Babylon screenshots are embedded."""
from pathlib import Path
import base64,json,html
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/commanders-v13'
def image(file):
 data=(OUT/file).read_bytes();assert data.startswith(b'\x89PNG')
 return 'data:image/png;base64,'+base64.b64encode(data).decode()
manifest=json.loads((ROOT/'public/models/manifest.json').read_text())
sections=[]
for kind,name in [('yukimura','真田幸村・赤備'),('ieyasu','家康・黑金')]:
 stats=manifest['variants'][kind]
 cards=[]
 for clip,label in [('idle','持械待機'),('thrust','突刺')]+([('slash','橫掃')] if kind=='yukimura' else []):
  for view,viewname in [('full','全身'),('hands','手部近照')]:
   pair=''.join(f'<figure><img src="{image(f"{stage}-{kind}-{clip}-{view}.png")}" alt="{name} {label} {viewname} {title}"><figcaption>{title}</figcaption></figure>' for stage,title in [('before','修正前'),('after','修正後')])
   cards.append(f'<h3>{label}・{viewname}</h3><div class="pair">{pair}</div>')
 sections.append(f'<section><h2>{name}</h2><p>{stats["triangles"]:,} 三角面 · 18 骨骼 · 一個材質</p>'+''.join(cards)+'</section>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>幸村與家康・模型修正比較</title><style>*{box-sizing:border-box}body{margin:0;background:#151a1d;color:#e9e3d5;font:16px/1.7 system-ui}main{max-width:1400px;margin:auto;padding:28px 16px}h1{font-size:28px}h2{margin-top:48px;color:#d3ac77}h3{font-size:18px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0;background:#202a2e}img{display:block;width:100%;height:auto}figcaption{padding:10px 16px}p{color:#bbc1bc}@media(max-width:650px){.pair{grid-template-columns:1fr}}</style><main><h1>幸村與家康・連續手部與握持修正</h1><p>下列均為 Babylon.js 載入實際遊戲 GLB 的畫面；圖片已內嵌，不需相鄰檔案。相同動畫時間與視角；近照以右腕取景，因此修正姿勢後取景中心會跟著移動。</p><p>兩位武將換上 MPFB／MakeHuman CC0 人體基底衍生的連續手套與貼合手背甲，手掌方向跟隨武器，家康改為居中持刀。保留原有赤備／黑金甲冑與十八骨骼動畫。仍是固定握姿，未新增手指開合動畫。</p>'''+''.join(sections)+'''<p>單一角色的美術檢查不代表實機手機效能；遊戲測試與素材預算另記錄於專案文件。原始手部授權及雜湊保留於 assets/vendor/mpfb。</p></main></html>'''
(OUT/'index.html').write_text(page);print('Embedded screenshots:',page.count('<img'),'gallery bytes:',len(page.encode()))
