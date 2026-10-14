"""Publish the verified v22 study and encode deterministic engine frames."""
import json,shutil,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'renders/wrist-v22';OUT=ROOT/'public/review/wrists';OUT.mkdir(parents=True,exist_ok=True)
report=json.loads((ROOT/'.tmp/wrist-v22/validation.json').read_text());assert report['passed']
capture=json.loads((SOURCE/'capture.json').read_text());assert len(capture['results'])==32 and not capture['errors']
for kind in ['yukimura','ieyasu']:
    glb=ROOT/f'.tmp/wrist-v22/models/{kind}.glb'
    assert hashlib.sha256(glb.read_bytes()).hexdigest()==report['models'][kind]['glb_sha256']
for row in capture['results']:
    file=SOURCE/row['file'];row['sha256']=hashlib.sha256(file.read_bytes()).hexdigest();shutil.copy2(file,OUT/file.name)
for kind in ['yukimura','ieyasu']:
    for look in ['armor','bare']:
        frames=ROOT/f'.tmp/wrist-v22/frames/{kind}-{look}'
        assert len(list(frames.glob('*.png')))==30
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','30','-i',str(frames/'%03d.png'),
                        '-c:v','libvpx-vp9','-crf','30','-b:v','0','-pix_fmt','yuv420p',str(OUT/f'{kind}-{look}.webm')],check=True)
(OUT/'capture.json').write_text(json.dumps(capture,indent=2)+'\n')
shutil.copy2(ROOT/'.tmp/wrist-v22/validation.json',OUT/'validation.json')
css='''body{margin:0;background:#141c20;color:#eee7dc;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:28px 20px 64px}a{color:#e5b47b}h1,h2{font-family:serif}h1{font-size:clamp(28px,5vw,42px)}h2{margin-top:48px}h3{margin-top:32px}.pair,.views{display:grid;grid-template-columns:1fr 1fr;gap:16px}.views{grid-template-columns:repeat(3,1fr)}figure{margin:0;background:#202b2e;min-width:0}img,video{display:block;width:100%;height:auto}figcaption{padding:10px 14px;color:#ccd3d1}.new{outline:2px solid #b65243}.tag{color:#f4bb98}nav,p,footer{max-width:78ch}details{margin:24px 0}summary{cursor:pointer;color:#e5b47b}footer{margin-top:40px}@media(max-width:680px){main{padding:22px 14px}.pair,.views{grid-template-columns:1fr}}'''
def figure(kind,clip,look,view,version='wrist'):
    labels={'oblique':'斜前方','side':'側面','top':'俯視'}
    label=('v22 試作' if version=='wrist' else 'v21 原版')+' · '+('卸甲手臂' if look=='bare' else '穿甲')+' · '+labels[view]
    file=f'{kind}-{version}-{clip}-{look}-{view}.png'
    return f'<figure class="{"new" if version=="wrist" else ""}"><a href="{file}"><img loading="lazy" src="{file}" width="1000" height="850" alt="{kind} {clip} {label}"></a><figcaption>{label}</figcaption></figure>'
sections=[]
for kind,title in [('yukimura','幸村 · 長槍'),('ieyasu','家康 · 雙手刀')]:
    sections.append(f'<section><h2>{title}</h2>')
    sections.append('<h3>突刺動作 · 可暫停比較</h3><div class="pair">')
    for look,label in [('armor','穿甲'),('bare','卸甲手臂')]:
        poster=f'{kind}-wrist-thrust-{look}-oblique.png'
        sections.append(f'<figure><video controls loop muted playsinline preload="none" poster="{poster}" width="720" height="600" aria-label="{title} {label}突刺動畫"><source src="{kind}-{look}.webm" type="video/webm"></video><figcaption>{label} · 1 秒動作循環</figcaption></figure>')
    sections.append('</div>')
    for clip,name in [('idle','持槍' if kind=='yukimura' else '雙手持刀'),('thrust','突刺')]:
        sections.append(f'<h3>{name} · 新舊比較</h3><div class="pair">'+figure(kind,clip,'armor','oblique')+figure(kind,clip,'armor','oblique','trial')+'</div>')
        sections.append('<h3>卸甲檢查 · 看清手肘、手腕與指節</h3><div class="pair">'+figure(kind,clip,'bare','oblique')+figure(kind,clip,'bare','oblique','trial')+'</div>')
        sections.append('<details><summary>側面與俯視 · 卸甲／穿甲四個角度</summary><div class="pair">')
        for look in ['bare','armor']:
            for view in ['side','top']:sections.append(figure(kind,clip,look,view))
        sections.append('</div></details>')
    sections.append('</section>')
intro='''<nav><a href="../menpo/trial/">面具試作</a> · <a href="../technique/">上一輪握姿</a> · <a href="../../">遊戲</a></nav><p class="tag">V22 · 已套用至遊戲</p><h1>讓手肘、手腕與握柄一起就位</h1><p>幸村後手移近身體中線，槍尖朝前；家康將雙手提到胸前，保留手肘彎曲空間。拇指轉向對握，分別調整指節包覆，避免把手腕硬扭成看似筆直。</p><p>左側／手機第一張是新試作，右側／下一張是 v21。卸甲視圖保留同一套手臂與手指網格，以單色查看握姿；肩部開口是原本藏在鎧甲內的模型裁切。點圖可放大，動畫可暫停。</p>'''
footer='''<p>本輪持槍、持刀與突刺姿勢已套用至遊戲；其他招式沿用既有動作。沿用同一套 92 骨架與貼圖，已烘焙為遊戲可載入的 GLB；沒有新增手機即時 IK。這些是參考姿勢的遊戲動畫，並非特定流派的標準術式。</p><p>檢查涵蓋握點連續性與手指對名義握柄圓柱的頂點接觸；仍不等於完整人體關節限制、逐三角形或鎧甲碰撞驗證，也尚未處理其他招式與滑握。</p><a href="validation.json">接觸檢查與模型雜湊</a> · <a href="capture.json">引擎截圖記錄</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/WRIST_STUDY_V22.md">製作／重建記錄</a>'''.replace('本轮','本輪')
(OUT/'index.html').write_text(f'<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>赤冬 · 手腕與握姿試作 v22</title><style>{css}</style><main>{intro}{"".join(sections)}<footer>{footer}</footer></main></html>')
# Keep earlier trials intact while making the new result reachable from the
# page the user already has open. The original gallery generator has this link too.
for path in [ROOT/'public/review/menpo/trial/index.html',ROOT/'public/review/technique/index.html']:
    text=path.read_text();url='../../wrists/' if '/menpo/' in str(path) else '../wrists/'
    link=f'<a href="{url}">最新 v22 手腕與握姿試作 ↗</a> · '
    if '最新 v22 手腕與握姿試作' not in text:text=text.replace('<nav>','<nav>'+link,1)
    path.write_text(text)
print('Published 32 screenshots, 4 animation clips and validation evidence')
