# v19：照片參考面頬與貼合頭盔

依使用者提供的四張日本武士甲冑照片調整自製面頬：幸村以第一張的突出鼻樑、鼻翼、頰線、張口與圓下巴為主要輪廓；家康另參考後三張的鬚飾、黑鐵與金色齒緣。保留真人雙眼，加強壓眉神情，以較低帽沿縮小裸露臉部範圍。面頬不覆蓋額頭，也不是帶兩個眼孔的整片面罩。

## 參考來源與限制

本輪視覺依據為使用者在對話提供的四張照片。第一張可見 John Fung 2013 版權標記；第二張可見 PIXTA 浮水印及編號 93290166；第三張可見 Dreamstime、編號 73950706 與 Marcovarro。第四張的來源未確認。上述資訊只是照片可見標記，沒有據此認定收藏機構、甲冑年代或歷史人物歸屬。

照片只用來觀察立體結構；未下載到遊戲資產、未去除浮水印，也未作材質。模型為本專案原創幾何，仍有簡化，並非照片實物等級雕刻或歷史復原。真人頭部來源及 MIT 授權沿用 v17/v18 記錄。

## 模型調整

鼻翼以外凸曲面及收窄孔緣塑形，口框具有內外殼與深色凹腔，遮住真人嘴部；家康加入細股灰白鬚飾與金色齒緣。鬚飾沿面罩表面射線貼合。漆甲的大面縮小既有圖集的 UV 取樣範圍，避免粗大的織紋蓋過金屬面部輪廓。漆甲、金屬、布繩繼續共用既有材質圖集，不新增紋理下載。

頭盔、前立、帽沿與內襯下壓最多 4.5 cm，側向收緊 4%。護頸下緣採漸變，避免整片向下硬移壓到肩甲。真人頭部與武器不跟著縮放。帽沿高度變化與選取數量記錄在 `manifest.json` 的 `menpo.helmet_fit`。

## 共用與預算

- 沿用原本的 92 骨、5 材質區塊與全場 14 張模型貼圖；沒有新貼圖或即時表情系統。
- 兩位仍低於 80,000 三角面，GLB 小於 6.1 MB（不含外部共享 PNG）。
- `build_commander_menpo.py --visor` 從不變的 v17 `*-face.blend` 重建，輸出 `*-visor.blend`；v18 的 `*-menpo.blend` 留作比較。
- 表情沿用授權來源眉眼形變，加上局部眉骨雕形；直接烘入網格。

## 貼合與驗證

面甲以真人皮膚射線貼合，再使用皮膚頂點、三角面中點及重心檢查外殼包覆。貼合 BVH 與匯出使用相同的三角切法，避免非平面四邊形在匯出時換對角線而出現皮膚穿插。沿用 2 mm 內外殼厚度。

`validate_face_motion.py --visor` 檢查 14 個動作、182 個取樣姿勢：頭臉／面甲隨骨，以及殼體頂點與變形後皮膚的有號距離。這不等於完整衣甲、武器碰撞測試；另以引擎正面、側面、全身、突刺、跑步截圖目視檢查。

## 重建與比較

```bash
npm run models:menpo
/workspace/yukimura-tools/render-env/bin/python tools/validate_face_motion.py --visor
# Vite 5180；由固定 v18 commit 建立比較快照
python3 - <<'PYTHON'
from pathlib import Path
import shutil, subprocess
out = Path('.tmp/menpo-v19/before')
out.mkdir(parents=True, exist_ok=True)
for kind in ['yukimura', 'ieyasu']:
    with (out / f'{kind}.glb').open('wb') as target:
        subprocess.run(['git', 'show', f'8960085d04021a143e394c645ff26e2a06d955b6:public/models/{kind}.glb'], stdout=target, check=True)
shutil.copytree('public/models/shared', out / 'shared', dirs_exist_ok=True)
PYTHON
node tools/capture-faces.mjs --visor
python3 tools/visor_gallery.py
```

現版比較頁位於 `public/review/menpo/index.html`，對照 v18 半面罩與 v19 照片參考面頬。同目錄 `v18.html` 保留前一版的頭部／表情記錄與原圖。
