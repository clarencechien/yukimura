"""Validate actual 4K PNGs and build a local review gallery/timing report."""
from pathlib import Path
import json,struct,hashlib,html,statistics

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/first-person'
render=json.loads((OUT/'render-3840.json').read_text())
assert len(render['frames'])==3
captions={1:'持槍・赤備手甲',120:'推進・雪中軍勢',240:'對峙・黑金家康'}
items=[]
for frame in render['frames']:
    path=OUT/frame['file'];raw=path.read_bytes()
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    width,height,bits,color=struct.unpack('>IIBB',raw[16:26])
    assert (width,height,bits,color)==(3840,2160,16,2),(path,width,height,bits,color)
    items.append({**frame,'caption':captions[frame['frame']],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
times=[i['seconds'] for i in items]
report={'frames':items,'resolution':[3840,2160],'png_bits_per_channel':16,'cpu_threads':4,
        'seconds_per_frame_range':[min(times),max(times)],
        'estimate_240_similar_frames_hours':round(statistics.mean(times)*240/3600,2),
        'estimate_scope':'Linear estimate from three CPU stills; excludes added animation, motion blur and new simulations. Not a Modal GPU measurement or quote.',
        'scene':'../../assets/cinema/first-person-lookdev.blend',
        'scene_sha256':hashlib.sha256((ROOT/'assets/cinema/first-person-lookdev.blend').read_bytes()).hexdigest()}
(OUT/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
cards=''.join(f'<figure><a href="{html.escape(i["file"])}"><img src="{html.escape(i["file"])}" loading="lazy" alt="{i["caption"]}"></a><figcaption>{i["caption"]}<small>4K · 16-bit PNG · CPU {i["seconds"]/60:.1f} 分鐘</small></figcaption></figure>' for i in items)
document=f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>真田 · 第一人稱試幀</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#101619;color:#e6e2d8;font:16px/1.7 system-ui,sans-serif}}main{{max-width:1320px;margin:auto;padding:40px 24px}}h1{{font-size:30px;letter-spacing:.12em}}header{{border-bottom:1px solid #54453e;margin-bottom:28px}}p,small{{color:#adb6b7}}section{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}figure{{margin:0;background:#1b2327}}figure:first-child{{grid-column:1/-1}}img{{display:block;width:100%;height:auto}}figcaption{{padding:16px;letter-spacing:.08em}}small{{display:block;font-size:13px;letter-spacing:0}}a{{color:#ddb897}}@media(max-width:700px){{section{{grid-template-columns:1fr}}}}</style>
<main><header><h1>真田 · 第一人稱試幀</h1><p>Blender Cycles 實際渲染 · 點圖開啟 3840 × 2160 原圖</p></header><section>{cards}</section>
<p>三個鏡頭／材質試拍點，尚非完成的動作影片。近景為專用手甲與現有雕刻手部、長槍；家康使用雕刻高模。手部造型、兵士與建物仍有精修空間。</p>
<p><a href="../../assets/cinema/first-person-lookdev.blend">Blender 場景</a> · <a href="review.json">規格與逐張耗時</a> · <a href="../../docs/CINEMATIC_TEST.md">製作與重建說明</a></p>
<p>本機 4 CPU 執行緒、32 samples、降噪；未使用 Modal GPU。240 幀在相同機器上的渲染時間線性估算約 {report['estimate_240_similar_frames_hours']:.1f} 小時，未計新增動畫效果，並非 GPU 報價。</p></main></html>'''
(OUT/'index.html').write_text(document)
print(json.dumps(report,ensure_ascii=False,indent=2))
