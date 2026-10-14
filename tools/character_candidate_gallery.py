"""Publish a self-contained-source study page using relative, Pages-safe URLs."""
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/review/candidates'
ASSETS = ROOT / 'assets/research/character-candidates'
stats = {r['id']: r for r in json.loads((OUT / 'validation.json').read_text())}
for p in ASSETS.iterdir():
    shutil.copy2(p, OUT / p.name)
shutil.copy2(ROOT / 'renders/detail-v16/yukimura-detail-idle-armor.png', OUT / 'current-yukimura.png')


def figure(file, label):
    return f'<figure><a href="{file}"><img src="{file}" alt="{html.escape(label)}" width="1000" height="1200"></a><figcaption>{label}</figcaption></figure>'


def numbers(name):
    s = stats[name]
    return f'{s["export_triangles"]:,} 三角面 · {s["bones"]} 骨骼 · GLB {s["glb_bytes"] / 1048576:.1f} MiB'


page = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>赤冬 · 寫實人物素材試載</title>
<style>body{margin:0;background:#131b1e;color:#ece6d9;font:16px/1.8 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 20px 60px}h1{font-family:serif;font-size:clamp(28px,5vw,44px);line-height:1.3}h2{font-family:serif;font-size:26px}a{color:#e3b67b}p{max-width:850px}small,.meta{color:#b7c2c4}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;background:#202a2e}img{display:block;width:100%;height:auto;aspect-ratio:5/6;object-fit:contain}figcaption{padding:12px 16px}section{margin-top:48px;border-top:1px solid #435054;padding-top:24px}.tag{font-size:13px;color:#ffbd99;letter-spacing:.08em}li{margin:10px 0}footer{margin-top:48px;font-size:14px}@media(max-width:640px){.grid{grid-template-columns:1fr}main{padding:24px 16px}}</style>
<main><a href="../">← 現行模型比較</a> · <a href="../../">遊戲</a>
<p class="tag">ART STUDY / 已完成素材的實際試載</p><h1>從木偶輪廓，走向可信的人物。</h1>
<p><strong>後續進度：</strong>幸村與家康已完成頭臉改裝並接入遊戲。<a href="../faces/">查看 v17 人物精修與動作比較 ↗</a></p>
<p>此頁保留素材選型時的試載：臉部解剖、皮膚貼圖、衣褶和甲片結構。下方是下載原始候選的 Blender 渲染，武將改裝成品請看上方的 v17 比較頁。</p>
<p class="meta">Cycles CPU · 32 samples · 1,000 × 1,200 · 本頁預覽貼圖上限 1,024 px · 無付費素材／Modal 作業</p>
<section><p class="tag">01 / 可改裝的人體候選</p><h2>Rocketbox：先把眼、鼻、嘴做好</h2>
<p>Microsoft / Rocketbox，MIT 授權。模型包含完整人體骨架、五指和皮膚貼圖。原 FBX 有 175 個表情形變；預覽 GLB 保留選定的眉頭、眨眼與張口表情。現代衣服、髮型與角色年齡仍須重作，這是人體底材。</p>
<p class="meta">''' + numbers('rocketbox') + '''</p><div class="grid">''' + figure('rocketbox-detail.png', '臉部近照 · 眼皮、鼻翼、唇線與膚色細節') + figure('rocketbox-full.png', '全身比例 · 現代服裝僅供檢查原資產') + '''</div>
<p><a href="rocketbox.glb">下載預覽 GLB</a> · <a href="rocketbox-babylon.png">Babylon.js 實際試載截圖</a> · <a href="rocketbox-LICENSE.txt">MIT 完整授權</a> · <a href="https://github.com/microsoft/Microsoft-Rocketbox">官方來源</a></p></section>
<section><p class="tag">02 / 可改作，但造型不適合直接替換</p><h2>Cyber Samurai：甲片和布料的製作品質</h2>
<p>KhoaMinh 的科幻武士。可觀察甲片厚度、零件搭接、衣褶和不同材質的表面反應。機械軀幹、銀色胸甲不符合大坂赤備；沒有骨架、動畫與手機 LOD，目前只作製作參考與技術試載。</p>
<p class="meta">''' + numbers('cyber-samurai') + '''</p><div class="grid">''' + figure('cyber-samurai-full.png', '全身 · 原作科幻造型，非歷史甲冑') + figure('cyber-samurai-detail.png', '甲片近照 · 分層、厚度及 PBR 材質') + '''</div>
<p><a href="cyber-samurai.glb">下載預覽 GLB</a> · <a href="cyber-samurai-babylon.png">Babylon.js 實際試載截圖</a> · <a href="cyber-samurai-LICENSE.txt">原資產授權與作者署名</a></p>
<p><small>This work is based on <a href="https://sketchfab.com/3d-models/cyber-samurai-26ccafaddb2745ceb56ae5cfc65bfed5">Cyber Samurai</a> by <a href="https://sketchfab.com/duongminhkhoa231">KhoaMinh</a>, licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Changes: uniform scale, reduced preview textures, Blender import/export and studio lighting. Source and licence verified through the pinned Tresjs/assets mirror; original platform currently inaccessible from the build environment.</small></p></section>
<section><p class="tag">03 / 本作要修正的地方</p><h2>讓赤備像穿在真人身上</h2><div class="grid">''' + figure('current-yukimura.png', '現行幸村 · Babylon.js v16 截圖；與上方為不同資產、相機及渲染器') + '''<div><p>目前面罩下的臉仍偏幾何拼接，肩甲和身體的連接也太僵硬。增加金邊、繩結或面數，無法替代解剖與實物结构。</p><ol><li>先做一個成熟武將頭部，處理眼眶、鼻翼、嘴唇、頸部與頭盔接縫。</li><li>把厚實感放在前臂、上臂、內襯和籠手，讓腕部保有自然彎曲空間。</li><li>依當世具足的構造重做甲片與繫帶，再配置赤漆、黑鐵、金屬、皮革和布料。</li><li>頭部、身體、骨架和甲片做成共用套件，再由同一資產產生兩位主將與小兵 LOD。</li></ol><p>尚未找到已核實授權、造型合適、可直接換上的完整免費武士甲。PBR Kabuto 的 NC-ND 與 Quill Samurai 的 Editorial 授權，均已排除遊戲改装。</p></div></div></section>
<footer><a href="sources.json">固定版本、原始檔雜湊與來源</a> · <a href="validation.json">匯入／匯出數據</a> · <a href="browser-check.json">Babylon.js 試載結果</a> · <a href="https://github.com/clarencechien/yukimura/blob/main/docs/CHARACTER_ASSET_RESEARCH.md">完整選型記錄與重建方式</a><p>圖片可直接點開；所有圖片與 GLB 使用相對網址，支援 GitHub Pages 子路徑。網頁未自動載入大型 3D 檔案。</p></footer></main></html>'''
(OUT / 'index.html').write_text(page)
