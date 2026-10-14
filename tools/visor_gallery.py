"""Publish actual Babylon v18/v19 comparisons and the mask motion checks."""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCULPT='--sculpt' in sys.argv
SOURCE=ROOT/('renders/menpo-v20' if SCULPT else 'renders/menpo-v19')
OUT=ROOT/'public/review/menpo'
OUT.mkdir(parents=True,exist_ok=True)
capture=json.loads((SOURCE/'capture.json').read_text())
assert len(capture['results'])==20 and not capture['errors']
motion=json.loads((SOURCE/'motion-check.json').read_text())
assert motion['passed'] and len(motion['results'])==14
for row in capture['results']:shutil.copy2(SOURCE/row['file'],OUT/row['file'])
for name in ['capture.json','motion-check.json']:shutil.copy2(SOURCE/name,OUT/name)
shutil.copy2(ROOT/'public/models/LICENSE-Rocketbox.txt',OUT/'LICENSE-Rocketbox.txt')
manifest=json.loads((ROOT/'public/models/manifest.json').read_text())
sections=[]
for kind,label in [('yukimura','真田幸村 · 赤漆面頰'),('ieyasu','德川家康 · 黑鐵金飾')]:
    stats=manifest['variants'][kind]
    sections.append(f'<section id="{kind}"><h2>{label}</h2><p class="muted">{stats["triangles"]:,} 三角面 · {stats["bytes"]/1048576:.2f} MiB GLB · 92 骨 · 5 材質區塊</p>')
    for clip,view,title in [('idle','face','面罩與雙眼'),('idle','profile','鼻翼、面頰與頸甲'),('idle','full','全身輪廓'),('thrust','action','突刺'),('run','action','奔跑')]:
        sections.append(f'<h3>{title}</h3><div class="pair">')
        for rig,caption in ([('sculpt','新版 v20 · 立體鼻翼、鼓頰與厚唇框'),('sculpt-before','舊版 v19 · 平滑面殼')] if SCULPT else [('visor-before','前版 v18 · 半面罩與較高帽沿'),('visor','遊戲現版 v19 · 武士面頬與貼合頭盔')]):
            file=f'{kind}-{rig}-{clip}-{view}.png'
            sections.append(f'<figure><a href="{file}"><img src="{file}" width="1000" height="1000" alt="{html.escape(label+" / "+title+" / "+caption)}"></a><figcaption>{caption}</figcaption></figure>')
        sections.append('</div>')
    sections.append('</section>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>赤冬 · 武士面頬 v19</title>
<style>body{margin:0;background:#131b1e;color:#eee7dc;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px 20px 64px}a{color:#e5b47b}h1,h2{font-family:serif}h1{font-size:clamp(28px,5vw,44px)}h2{font-size:30px;margin-bottom:0}h3{font-size:17px;margin-top:32px}.muted,figcaption{color:#bac3c3}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2e}img{display:block;width:100%;height:auto}figcaption{padding:10px 16px;font-size:14px}section{border-top:1px solid #425052;margin-top:44px;padding-top:22px}.intro{max-width:880px}.tag{color:#da9c81;font-size:13px;letter-spacing:.1em}footer{margin-top:48px;font-size:14px}@media(max-width:640px){.pair{grid-template-columns:1fr}main{padding:24px 14px}}</style>
<main><a href="../../">進入遊戲 ↗</a> · <a href="v18.html">v18 半面罩記錄</a> · <a href="../faces/">真人頭部來源</a> · <a href="../candidates/">開源素材記錄</a>
<p class="tag">MENPO / 已接入遊戲角色</p><h1>依武士面頬照片，重整鼻口與兜的輪廓。</h1>
<div class="intro"><p>依使用者提供的四張甲冑照片，重新塑造突出的鼻樑與鼻翼、頰部起伏、張口邊框與較圓的下巴。幸村採深赤漆；家康採黑鐵金飾，加入灰白鬚飾與金色齒緣。鼻口凹腔遮住真人嘴部，低帽沿下保留雙眼與壓眉神情。</p>
<p>頭盔下壓 4.5 公分、側邊收緊 4%，內襯與護頸順勢調整；避免帽沿離眉眼太遠，讓頭盔與面甲形成完整輪廓。下緣採漸變調整，保留肩甲的活動空間。</p>
<p class="muted">以下為 Babylon.js 實際截圖，前後使用相同相機、光線與動作時間。沿用原有 92 骨、5 個材質區塊及全部模型貼圖；每位仍低於 8 萬三角面、GLB 低於 6.1 MB（不含外部貼圖）。這是參考照片構造的遊戲造型，仍是簡化網格，並非實物等級雕刻或特定年代的復原。</p>
<p>14 個動作、182 個姿勢通過面罩／頭部隨骨及殼體頂點與皮膚間隙檢查；不是完整衣甲碰撞模擬。表情為烘入網格的戰鬥神情，沒有新增即時表情運算。</p></div>
'''+''.join(sections)+'''
<footer><p>Human head derived from Microsoft Rocketbox Male Adult 10. Copyright (c) 2020 Microsoft, <a href="LICENSE-Rocketbox.txt">MIT license</a>. 面罩為本專案自製，沿用既有甲冑貼圖。參考照片只用來觀察造型，未收錄、去浮水印或用作遊戲貼圖；照片中的甲冑年代與收藏來源尚未核實。</p>
<p><a href="capture.json">引擎截圖紀錄</a> · <a href="motion-check.json">動作與皮膚間隙檢查</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/COMMANDER_VISOR.md">製作與重建紀錄</a></p></footer></main></html>'''
if SCULPT:
    start=page.index('<p class="tag">');end=page.index('<section',start)
    page=page[:start]+"""<p class="tag">V20 / 新版模型已接入遊戲</p><p><a href="trial/">查看較俐落的 v21 面具試作 ↗</a> · <a href="../technique/">槍術與劍術握持試作 ↗</a></p><h1>重新塑形的武士面頬</h1>
<div class="intro"><p><strong>新版在左邊；手機版先顯示新版。</strong>右邊／下方是上一版 v19，方便直接比較。</p>
<p>上一版仍像平滑面殼。這次重建鼻頭、立體鼻翼、鼓頰與鼻唇溝，使用連續曲面包圍嘴部，加厚唇框並塑出圓下巴；家康的鬚飾也增加厚度。</p>
<p>以下均為 Babylon.js 實際模型截圖，兩版相機、光線及動作時間相同。仍沿用 92 骨、5 材質區塊與全部既有貼圖。只增加主將面具的幾何密度，小兵未增加面數。</p>
<p class="muted">參考使用者提供的武士甲冑照片塑形，仍為風格化遊戲模型，並非實物復原。14 個動作、182 個取樣姿勢通過面罩隨骨與殼體頂點間隙檢查。</p></div>
"""+page[end:]
    page=page.replace('赤冬 · 武士面頬 v19','赤冬 · 立體面頬 v20').replace('COMMANDER_VISOR.md','COMMANDER_MENPO_V20.md')
    page=page.replace('<a href="v18.html">v18 半面罩記錄</a>','<a href="v19.html">v19 記錄</a> · <a href="v18.html">v18 記錄</a>')
    page=page.replace('figure{margin:0;', '.pair figure:first-child{outline:2px solid #b65243}.pair figure:first-child figcaption{color:#ffd8b2;font-weight:700}figure{margin:0;')
(OUT/'index.html').write_text(page)
