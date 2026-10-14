"""Publish the v21 design study without replacing the live game models."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'renders/menpo-v21'
style='''body{margin:0;background:#141c20;color:#eee7dc;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px 20px 64px}a{color:#e5b47b}h1,h2{font-family:serif}h1{font-size:clamp(28px,5vw,42px)}h2{margin-top:40px}h3{font-size:18px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2e}.pair figure:first-child{outline:2px solid #b65243}img{display:block;width:100%;height:auto}figcaption{padding:10px 16px}p,figcaption{color:#c3cdce}.tag{color:#f4bb98}table{border-collapse:collapse;width:100%}th,td{padding:8px;border-bottom:1px solid #425052;text-align:left}footer{margin-top:40px}@media(max-width:640px){main{padding:24px 14px}.pair{grid-template-columns:1fr}}'''

def page(title,intro,sections,footer):
    return f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{style}</style><main>{intro}{''.join(sections)}<footer>{footer}</footer></main></html>'''

def publish_images(source,out,count):
    out.mkdir(parents=True,exist_ok=True)
    capture=json.loads((source/'capture.json').read_text())
    assert len(capture['results'])==count and not capture['errors']
    for row in capture['results']:shutil.copy2(source/row['file'],out/row['file'])
    shutil.copy2(source/'capture.json',out/'capture.json')

def pair(kind,clip,view):
    result=['<div class="pair">']
    for rig,label in [('trial','v21 試作'),('trial-before','v19 參考版')]:
        file=f'{kind}-{rig}-{clip}-{view}.png'
        result.append(f'<figure><a href="{file}"><img src="{file}" width="1000" height="1000" alt="{kind} {clip} {view} {label}"></a><figcaption>{label}</figcaption></figure>')
    return ''.join(result)+'</div>'

out=ROOT/'public/review/menpo/trial'
publish_images(SOURCE,out,20)
motion=json.loads((SOURCE/'motion-check.json').read_text());assert motion['passed']
shutil.copy2(SOURCE/'motion-check.json',out/'motion-check.json')
sections=[]
for kind,label in [('yukimura','幸村 · 赤漆'),('ieyasu','家康 · 黑鐵金飾')]:
    sections.append(f'<section><h2>{label}</h2>')
    for clip,view,label in [('idle','face','正面'),('idle','profile','側面'),('idle','full','全身'),('thrust','action','突刺'),('run','action','奔跑')]:
        sections.append(f'<h3>{label}</h3>'+pair(kind,clip,view))
    sections.append('</section>')
intro='''<nav><a href="../">現行遊戲模型 v20</a> · <a href="../../technique/">槍術與劍術手部試作 ↗</a></nav><p class="tag">V21 · 造型試作，尚未替換遊戲模型</p><h1>回到俐落的面具輪廓</h1><p>以你較喜歡的 v19 為基準，保留較高的頰側、收窄的下巴與眼部切線，減少 v20 鼓起的雙頰和厚唇。鼻翼與口框仍有立體細節，但改為較薄的金屬邊。</p><p>左側／手機第一張為 v21 試作，右側／下一張是 v19。正面、側面使用相同相機、光線與動作時間；戰鬥圖另包含本輪握持姿勢調整。</p>'''
footer='''<a href="capture.json">引擎截圖</a> · <a href="motion-check.json">182 個姿勢檢查</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/COMMANDER_TRIAL_V21.md">製作記錄</a><p>真人頭部衍生自 Microsoft Rocketbox（MIT），人體手部來源為 MPFB（CC0）。照片僅作構造參考，未收錄或用作貼圖。</p>'''
(out/'index.html').write_text(page('赤冬 · 面具試作 v21',intro,sections,footer))

out=ROOT/'public/review/technique'
publish_images(SOURCE/'grip',out,24)
metrics={}
for kind in ['yukimura','ieyasu']:
    metrics[kind]={}
    for version in ['before','after']:
        metrics[kind][version]=json.loads((ROOT/f'.tmp/menpo-v21/grip-{version}/{kind}.json').read_text())
(out/'grip-check.json').write_text(json.dumps(metrics,indent=2)+'\n')
sections=['<table><thead><tr><th>動作</th><th>原版最大腕折</th><th>試作最大腕折</th></tr></thead><tbody>']
for kind,clip,label in [('yukimura','idle','幸村・持槍'),('yukimura','run','幸村・奔跑'),('ieyasu','thrust','家康・突刺')]:
    angles=[metrics[kind][v]['clips'][clip]['maxWristAngle'] for v in ['before','after']]
    sections.append(f'<tr><td>{label}</td><td>{angles[0]:.1f}°</td><td>{angles[1]:.1f}°</td></tr>')
sections.append('</tbody></table>')
for kind,label in [('yukimura','幸村 · 長槍'),('ieyasu','家康 · 雙手刀')]:
    sections.append(f'<section><h2>{label}</h2>')
    for clip,label in [('idle','持武器'),('run','奔跑'),('thrust','突刺')]:
        for view,angle in [('oblique','斜前方'),('side','側面')]:
            sections.append(f'<h3>{label} · {angle}</h3>'+pair(kind,clip,view))
    sections.append('</section>')
intro='''<nav><a href="../menpo/trial/">面具試作 ↗</a> · <a href="../../">目前遊戲</a></nav><p class="tag">V21 · 握持試作，尚未替換遊戲動作</p><h1>讓手腕順接前臂</h1><p>長槍以較長的雙手間距導向、推送；常見雙手刀握法則右手近刀鍔、左手近柄尾。這次依提供照片檢查握持與腕肘連線，沒有宣稱特定流派的標準動作。</p><p>家康原本突刺時把刀柄收得太靠近軀幹；試作將雙手移到身體前方，減少左腕折回。幸村調整持槍／奔跑時的後手高度與槍桿角度。原版的幸村突刺腕折已較小，本輪保留。</p><p>左側／手機第一張是試作。原版截圖使用 v19，其手部與 v20 相同；角度、倍率與動作時間一致，鏡頭追蹤雙手中心。</p><p>角度是模型前臂與手掌軸的最大夾角，屬於骨架檢查指標，不是人體活動範圍或武術評分。兩位合計 2,352 個手部取樣，握點偏差均小於 0.5 mm；這不等於逐指接觸或衣甲碰撞驗證。</p>'''
footer='''<a href="capture.json">引擎截圖</a> · <a href="grip-check.json">分動作握持量測</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/COMMANDER_TRIAL_V21.md">製作記錄</a><p>保留原有手指握形；尚未新增逐招的手指收放、滑槍或刀柄橢圓截面貼合。動作已離線烘焙，未增加執行時 IK。</p>'''
(out/'index.html').write_text(page('赤冬 · 槍術與劍術握持試作',intro,sections,footer))
