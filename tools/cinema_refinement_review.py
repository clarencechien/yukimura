"""Validate final stills and create an accessible before/after image comparison."""
from pathlib import Path
import hashlib
import html
import json
import struct

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/first-person-refined'
report=json.loads((OUT/'render-3840.json').read_text())
assert {f['frame'] for f in report['frames']}=={1,240}
captions={1:'赤備護臂與握槍近景',240:'黑金家康與雪中軍勢'}
cards=[]
for f in report['frames']:
    path=OUT/f['file'];raw=path.read_bytes()
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>IIBB',raw[16:26])==(3840,2160,16,2)
    f['sha256']=hashlib.sha256(raw).hexdigest();f['bytes']=len(raw)
    before='../first-person/'+f['file']
    assert (OUT/before).is_file()
    fid=f['frame'];name=html.escape(f['file'])
    cards.append(f'''<section><h2>{captions[fid]}</h2>
<div class="compare" id="compare-{fid}"><img src="{name}" alt="本次精修：{captions[fid]}" loading="lazy"><img class="before" src="{before}" alt="上一版：{captions[fid]}" loading="lazy"><span class="divider" aria-hidden="true"></span><span class="label old">上一版</span><span class="label new">本次精修</span></div>
<label for="slider-{fid}">拖曳比較，或使用左右方向鍵</label><input id="slider-{fid}" type="range" min="0" max="100" value="50" data-frame="{fid}" aria-label="{captions[fid]}的前後對照比例">
<p><a href="{name}">本次 4K 原圖</a> · <a href="{before}">上一版 4K 原圖</a><small>Cycles CPU · 32 samples · {f['seconds']/60:.1f} 分鐘</small></p></section>''')
scene=ROOT/'assets/cinema/first-person-refined.blend'
report['scene_sha256']=hashlib.sha256(scene.read_bytes()).hexdigest()
report['scene_check']=json.loads((OUT/'scene-check.json').read_text())
(OUT/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
document='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>赤冬 · 模型精修前後對照</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111719;color:#e5e1d6;font:16px/1.75 system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:32px 20px}h1{font-size:28px;letter-spacing:.12em}h2{font-size:20px}section{margin:40px 0}p,small,label{color:#b0b7b7}small{display:block}a{color:#dfb18b}.compare{position:relative;--split:50%;overflow:hidden;aspect-ratio:16/9;background:#202527}.compare img{display:block;width:100%;height:100%;object-fit:contain}.before{position:absolute;inset:0;clip-path:inset(0 calc(100% - var(--split)) 0 0)}.divider{position:absolute;top:0;bottom:0;left:var(--split);width:2px;background:#ead9bc}.label{position:absolute;top:12px;padding:3px 10px;background:#101417cc;font-size:13px}.old{left:12px}.new{right:12px}input{display:block;width:100%;margin:12px 0;accent-color:#b53c32}label{font-size:13px}header{border-bottom:1px solid #51483e;padding-bottom:12px}</style>
<main><header><h1>赤冬 · 模型精修前後對照</h1><p>相同鏡頭 · 實際 Blender 幾何與材質 · 3840 × 2160 / 16-bit PNG</p></header>
'''+''.join(cards)+'''<p>本次加入分層甲片、繫繩、鉚釘、六文錢手甲、彎曲手指與袖口褶皺；城樓補上瓦片、窗格、木構和不規則石牆，戰場加入髒雪、碎木、稻草、箭矢，以及四組共用的兵士姿勢。燈光、材質及霧也有調整。</p>
<p>這是离線影片用的細節版本，仍是三個姿勢的構圖測試。尚未完成連續動畫、遊戲烘焙與手機效能最佳化；人物臉部和布料造型仍有精修空間。</p>
<p><a href="../../assets/cinema/first-person-refined.blend">可編輯 Blender 場景</a> · <a href="review.json">規格與驗證紀錄</a> · <a href="../../docs/CINEMATIC_REFINEMENT.md">製作與重建說明</a></p></main>
<script>document.querySelectorAll('input[data-frame]').forEach(input=>{input.addEventListener('input',()=>document.getElementById('compare-'+input.dataset.frame).style.setProperty('--split',input.value+'%'))})</script></html>'''
(OUT/'index.html').write_text(document.replace('离線','離線'))
print(json.dumps({'frames':report['frames'],'scene_sha256':report['scene_sha256']},ensure_ascii=False,indent=2))
