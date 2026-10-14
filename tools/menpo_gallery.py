"""Publish actual Babylon v17/v18 comparisons and the mask motion checks."""
import html
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'renders/menpo-v18'
OUT=ROOT/'public/review/menpo'
OUT.mkdir(parents=True,exist_ok=True)
capture=json.loads((SOURCE/'capture.json').read_text())
assert len(capture['results'])==20 and not capture['errors']
motion=json.loads((SOURCE/'motion-check.json').read_text())
assert motion['passed'] and len(motion['results'])==14
for row in capture['results']:shutil.copy2(SOURCE/row['file'],OUT/row['file'])
for kind in ['yukimura','ieyasu']:shutil.copy2(SOURCE/f'{kind}-neutral-menpo.png',OUT/f'{kind}-neutral-menpo.png')
for name in ['capture.json','motion-check.json']:shutil.copy2(SOURCE/name,OUT/name)
shutil.copy2(ROOT/'public/models/LICENSE-Rocketbox.txt',OUT/'LICENSE-Rocketbox.txt')
manifest=json.loads((ROOT/'public/models/manifest.json').read_text())
sections=[]
for kind,label in [('yukimura','真田幸村 · 赤漆面頰'),('ieyasu','德川家康 · 黑鐵金飾')]:
    stats=manifest['variants'][kind]
    sections.append(f'<section><h2>{label}</h2><p class="muted">{stats["triangles"]:,} 三角面 · {stats["bytes"]/1048576:.2f} MiB GLB · 92 骨 · 5 材質區塊</p>')
    sections.append('<h3>眼神精修 · 同一面罩與光線</h3><div class="pair">')
    for file,caption in [(f'{kind}-neutral-menpo.png','調整前 · 平視表情'),(f'{kind}-menpo-idle-face.png','遊戲現版 · 壓眉、皺眉與凝視')]:
        sections.append(f'<figure><a href="{file}"><img src="{file}" width="1000" height="1000" alt="{html.escape(label+" / "+caption)}"></a><figcaption>{caption}</figcaption></figure>')
    sections.append('</div>')
    for clip,view,title in [('idle','face','面罩與雙眼'),('idle','profile','鼻翼、面頰與頸甲'),('idle','full','全身輪廓'),('thrust','action','突刺'),('run','action','奔跑')]:
        sections.append(f'<h3>{title}</h3><div class="pair">')
        for rig,caption in [('menpo-before','前版 v17 · 真人頭部'),('menpo','遊戲現版 v18 · 真人頭部＋面罩')]:
            file=f'{kind}-{rig}-{clip}-{view}.png'
            sections.append(f'<figure><a href="{file}"><img src="{file}" width="1000" height="1000" alt="{html.escape(label+" / "+title+" / "+caption)}"></a><figcaption>{caption}</figcaption></figure>')
        sections.append('</div>')
    sections.append('</section>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>赤冬 · 真人面罩 v18</title>
<style>body{margin:0;background:#131b1e;color:#eee7dc;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px 20px 64px}a{color:#e5b47b}h1,h2{font-family:serif}h1{font-size:clamp(28px,5vw,44px)}h2{font-size:30px;margin-bottom:0}h3{font-size:17px;margin-top:32px}.muted,figcaption{color:#bac3c3}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2e}img{display:block;width:100%;height:auto}figcaption{padding:10px 16px;font-size:14px}section{border-top:1px solid #425052;margin-top:44px;padding-top:22px}.intro{max-width:880px}.tag{color:#da9c81;font-size:13px;letter-spacing:.1em}footer{margin-top:48px;font-size:14px}@media(max-width:640px){.pair{grid-template-columns:1fr}main{padding:24px 14px}}</style>
<main><a href="../../">進入遊戲 ↗</a> · <a href="../faces/">前版真人頭部</a> · <a href="../candidates/">開源素材記錄</a>
<p class="tag">MENPO / 已接入遊戲角色</p><h1>真人為骨，面頰為甲。</h1>
<div class="intro"><p>保留真人頭部與雙眼，為幸村加上赤漆面頰，為家康加上黑鐵金飾。曲面沿鼻翼、面頰與下顎包覆；2 mm 殼體、捲邊及真正鏤空的口部開口，讓面罩有可見的厚度。</p>
<p>兩位都壓低內側眉骨、收窄眼瞼，加入眉間皺褶。幸村眼神較銳利、略帶左右差異；家康眉壓更重、凝視更沉。利用來源的眉眼形變加上局部雕形，直接烘進網格，不額外增加即時表情運算。</p>
<p>兩人共用面罩製作方式、既有材質與貼圖，不增加骨架。修正下顎權重，讓臉與面罩一同轉動，頸部底端保留平滑過渡。</p>
<p class="muted">以下是 Babylon.js 實際模型截圖，前後採同一相機、光線及動作時間。每位增加 1,332 個三角面、約 52 KB GLB；模型貼圖仍為全場共 14 張。此為本作武士風格設計，不宣稱是歷史面頰的精確復原。</p>
<p>兩位主將共 14 個動作、182 個姿勢通過頭部／面罩隨骨及殼體頂點與皮膚的間隙檢查。這不等於完整衣甲碰撞模擬；肩甲、髮鬚、表情與整體插畫光影仍可再精修。</p></div>
'''+''.join(sections)+'''
<footer><p>Human head derived from Microsoft Rocketbox Male Adult 10. Copyright (c) 2020 Microsoft, <a href="LICENSE-Rocketbox.txt">MIT license</a>. 面罩為本專案自製，沿用既有甲冑貼圖。</p>
<p><a href="capture.json">引擎截圖紀錄</a> · <a href="motion-check.json">動作與皮膚間隙檢查</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/COMMANDER_MENPO.md">製作與重建紀錄</a></p></footer></main></html>'''
(OUT/'index.html').write_text(page)
