"""Validate the five actual study PNGs and write a local review page."""
from pathlib import Path
import json,hashlib,struct,html,base64
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/open-hand'
r=json.loads((OUT/'render-2560.json').read_text())
assert {f['view'] for f in r['frames']}=={'open','grip','palm','beauty','beauty-palm'}
names={'beauty':'赤備籠手・手背近照','beauty-palm':'皮革手套・掌面近照','open':'開源人体基底・展開白模','grip':'握槍白模・手背','palm':'握槍白模・掌面'}
for f in r['frames']:
    data=(OUT/f['file']).read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
    w,h,bits,color=struct.unpack('>IIBB',data[16:26]);assert (w,h,bits)==(2560,2048,16)
    f.update({'resolution':[w,h],'bits_per_channel':bits,'png_color_type':color,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
r['scene_check']=json.loads((OUT/'scene-check.json').read_text())
r['scene_sha256']=hashlib.sha256((ROOT/'assets/cinema/open-hand-study.blend').read_bytes()).hexdigest()
(OUT/'review.json').write_text(json.dumps(r,indent=2)+'\n')
frames={f['view']:f for f in r['frames']}
cards=[]
for view in ('beauty','grip','palm','beauty-palm','open'):
    f=frames[view];name="data:image/png;base64,"+base64.b64encode((OUT/f["file"]).read_bytes()).decode("ascii")
    cards.append(f'<figure><img src="{name}" alt="{names[view]}"><figcaption>{names[view]}<small>2560 × 2048 · 16-bit PNG · CPU {f["seconds"]:.1f} 秒</small></figcaption></figure>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>真田・開源手部與籠手試作</title><style>*{box-sizing:border-box}body{margin:0;background:#151a1d;color:#ede7da;font:16px/1.8 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:36px 20px}h1{font-size:28px;letter-spacing:.1em}p,small{color:#b9bfc0}a{color:#ddb487}section{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;background:#20272b}figure:first-child{grid-column:1/-1}img{display:block;width:100%;height:auto}figcaption{padding:14px 18px}small{display:block;font-size:13px}@media(max-width:650px){section{grid-template-columns:1fr}}</style><main><h1>開源手部與籠手試作</h1><p>MPFB / MakeHuman CC0 網格與權重 · Blender Cycles 實際渲染</p><section>'''+''.join(cards)+'''</section><p>連續手部拓撲、22 根骨骼、五指關節、皮革縫線、七片穿孔甲片與六文錢手甲。第 1／24 幀分別為展開與握槍測試姿勢，尚非完成的抓取動畫。</p><p>本頁已內嵌五張原圖，可獨立開啟。素材：<a href="https://github.com/makehumancommunity/mpfb2">MPFB / MakeHuman</a>（網格、骨架與權重 CC0）。可編輯場景與驗證紀錄隨專案保存。</p><p>尚需處理遊戲用接觸修正、UV 重排、材質烘焙與 LOD；本次未改動線上遊戲。</p></main></html>'''
(OUT/'index.html').write_text(page.replace('人体','人體'))
print(json.dumps({'verified_images':len(r['frames']),'resolution':[2560,2048],'render_seconds':[f['seconds'] for f in r['frames']]},indent=2))
