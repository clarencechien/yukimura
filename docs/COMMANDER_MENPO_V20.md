# v20：重建面頬的立體造型

> 歷史／研究文件（2026-10-14 整理）：以下「目前」、測試數據與待辦指原記錄階段，不代表 v22 現況；舊版命令如需精確重現，應使用對應 Git 版本。目前採用範圍以 [狀態與交接](STATUS.md) 為準；參閱 [完整索引](INDEX.md)。

v19 已在線上，但仍以稀疏的平滑面殼為基底，鼻翼和頰肉在實際引擎畫面裡不夠清楚。比較頁又先顯示舊圖，使新版更難辨認。v20 重建面具拓撲，並讓新版在桌面左側、手機上方先出現。

## 造型與共用

`tools/sculpt_menpo.py` 建立圍繞口部的連續曲面：80 個角向分段、18 個徑向環。鼻樑、鼻頭、鼻翼、鼓頰、鼻唇溝與圓下巴使用各自的曲面起伏；鼻孔使用橢圓孔緣與深色凹部，嘴部使用連續厚唇框及凹腔。家康另有加密的灰白鬚股、齒緣。全部構件隨原本的頭骨變形。

兩位共用同一個生成器、92 骨骨架規格、5 個材質區塊與既有貼圖，沒有新增圖集或即時表情運算。沿用 v19 的低帽沿和壓眉表情。只提高兩名主將的面具網格密度，小兵模型及動畫資料不變。

| 模型 | v19 三角面 | v20 三角面 | v20 GLB |
| --- | ---: | ---: | ---: |
| 幸村 | 79,743 | 87,087 | 約 6.35 MB |
| 家康 | 76,995 | 85,503 | 約 6.13 MB |

GLB 大小不包含外部共享 PNG。主將預算調整為每位最多 90,000 三角面、7 MB GLB；這是有意增加面部幾何，並非效能測試失敗後放寬門檻。沒有宣稱特定手機 FPS。

## 參考與限制

延續使用者提供的四張武士甲冑照片，參考鼻翼、頰線、口框和下巴的構造；來源記錄見 [v19 說明](COMMANDER_VISOR.md)。照片未作遊戲貼圖、未收錄或移除浮水印。真人頭部沿用 Microsoft Rocketbox MIT 授權來源。

本版仍是風格化遊戲模型，不是照片等級雕刻或特定歷史甲冑的復原。鼻孔凹部為局部幾何與深色材質，未模擬真實可拆鼻件及完整內部構造。

## 驗證與重建

面頬外殼使用與 glTF 相同的三角切法，以皮膚頂點、三角形中點和重心檢查前向間隙；另外檢查鼻底斜面最近表面的方向，並對稱地保留額外 3 mm 餘量。另在 14 個動作、182 個取樣姿勢中檢查面具隨骨與殼體頂點對皮膚的距離；這不是完整衣甲／武器碰撞模擬。引擎截圖另檢查正面、側面、全身、突刺及奔跑。

```bash
npm run models:menpo
/workspace/yukimura-tools/render-env/bin/python tools/validate_face_motion.py --sculpt
# Vite 檢視器需在 5180 埠運行。
python3 - <<'PY'
from pathlib import Path
import shutil, subprocess
out = Path('.tmp/menpo-v20/before')
out.mkdir(parents=True, exist_ok=True)
for kind in ['yukimura', 'ieyasu']:
    with (out / f'{kind}.glb').open('wb') as target:
        subprocess.run(['git', 'show', f'e26229c2b7155c8aa8e4b9a4e14b8f7b4e9c809c:public/models/{kind}.glb'], stdout=target, check=True)
shutil.copytree('public/models/shared', out / 'shared', dirs_exist_ok=True)
PY
node tools/capture-faces.mjs --sculpt
python3 tools/visor_gallery.py --sculpt
npm test
npm run test:e2e
npm run test:pages
```

可編輯來源為 `assets/optimized/commanders/*-sculpt.blend`。現版比較頁位於 `public/review/menpo/index.html`；`v19.html` 與 `v18.html` 保留前版記錄。截圖使用不同版本檔名，遊戲模型載入版本提升為 `commander-20`。
