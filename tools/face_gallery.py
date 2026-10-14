"""Publish same-camera Babylon comparisons of the installed v17 commanders."""
import html
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'renders/face-v17'
OUT=ROOT/'public/review/faces'
OUT.mkdir(parents=True,exist_ok=True)
capture=json.loads((SOURCE/'capture.json').read_text())
for row in capture['results']:shutil.copy2(SOURCE/row['file'],OUT/row['file'])
for name in ['capture.json','motion-check.json']:shutil.copy2(SOURCE/name,OUT/name)
shutil.copy2(ROOT/'public/models/LICENSE-Rocketbox.txt',OUT/'LICENSE-Rocketbox.txt')
manifest=json.loads((ROOT/'public/models/manifest.json').read_text())
sections=[]
for kind,label in [('yukimura','真田幸村'),('ieyasu','德川家康')]:
    stats=manifest['variants'][kind]
    sections.append(f'<section><h2>{label}</h2><p class="muted">{stats["triangles"]:,} 三角面 · {stats["bytes"]/1048576:.2f} MiB GLB · 原有 92 骨戰鬥骨架</p>')
    for clip,view,title in [('idle','face','正面近景'),('idle','profile','側面與頸部'),('idle','full','全身比例'),('thrust','action','突刺'),('run','action','奔跑')]:
        sections.append(f'<h3>{title}</h3><div class="pair">')
        for rig,caption in [('face-before','調整前 · v16 面甲與簡化五官'),('face','已套用 · v17 真人頭臉')]:
            file=f'{kind}-{rig}-{clip}-{view}.png'
            sections.append(f'<figure><a href="{file}"><img src="{file}" width="1000" height="1000" alt="{html.escape(label+" / "+title+" / "+caption)}"></a><figcaption>{caption}</figcaption></figure>')
        sections.append('</div>')
    sections.append('</section>')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>赤冬 · 武將頭臉精修 v17</title>
<style>body{margin:0;background:#131b1e;color:#eee7dc;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px 20px 64px}a{color:#e5b47b}h1,h2{font-family:serif}h1{font-size:clamp(28px,5vw,44px)}h2{font-size:30px;margin-bottom:0}h3{font-size:17px;margin-top:32px}.muted,figcaption{color:#bac3c3}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2e}img{display:block;width:100%;height:auto}figcaption{padding:10px 16px;font-size:14px}section{border-top:1px solid #425052;margin-top:44px;padding-top:22px}.intro{max-width:880px}.tag{color:#da9c81;font-size:13px;letter-spacing:.1em}footer{margin-top:48px;font-size:14px}@media(max-width:640px){.pair{grid-template-columns:1fr}main{padding:24px 14px}}</style>
<main><a href="../../">進入遊戲 ↗</a> · <a href="../candidates/">素材選型記錄</a> · <a href="../">v16 甲冑比較</a>
<p class="tag">目前遊戲為 v18：<a href="../menpo/">查看真人頭部加上面罩的新版比較 ↗</a>。本頁保留 v17 頭臉製作記錄。</p>
<p class="tag">CHARACTER UPDATE / 已接入遊戲角色</p><h1>武將頭臉，從面甲走向真人。</h1>
<div class="intro"><p>幸村與家康已換上由 Microsoft Rocketbox 改裝的頭臉：保留眼皮、鼻翼、唇線與耳朵，重新調整頭型、頸部權重與皮膚。幸村增加短鬚與精悍輪廓；家康加寬下顎、調整頰部，加入灰鬚與年長感。</p>
<p>兩人共用頭部拓撲、皮膚法線、頭盔內襯與繫帶製作方式。頭部跟隨原有戰鬥骨架；皮膚採獨立材質，避免套上甲冑的金屬敲紋與清漆。</p>
<p class="muted">以下均為 Babylon.js 實際 GLB 截圖，前後採相同相機、光線與動作時間。不是離線插畫。手機／GPU 效能仍需真機量測；目前肩甲、手腕比例及整體甲冑仍有插畫精修空間。</p>
<p>驗證：兩位主將共 14 個動作、182 個取樣姿勢的頭部隨骨檢查。這次沒有新增即時表情／口型動畫，也沒有更動小兵模型。</p></div>
'''+''.join(sections)+'''
<footer><p>Human head derived from Microsoft Rocketbox Male Adult 10. Copyright (c) 2020 Microsoft, <a href="LICENSE-Rocketbox.txt">MIT license</a>. Modifications: head extraction, fitted proportions, mature complexion, neck skin weights and shared helmet attachments.</p>
<p><a href="capture.json">即時截圖與材質紀錄</a> · <a href="motion-check.json">182 姿勢驗證</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/HUMAN_COMMANDER_HEADS.md">製作與重建紀錄</a></p></footer></main></html>'''
(OUT/'index.html').write_text(page)
