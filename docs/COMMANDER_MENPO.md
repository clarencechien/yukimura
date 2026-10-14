# v18：真人頭部加上武士面頰

> 歷史／研究文件（2026-10-14 整理）：以下「目前」、測試數據與待辦指原記錄階段，不代表 v22 現況；舊版命令如需精確重現，應使用對應 Git 版本。目前採用範圍以 [狀態與交接](STATUS.md) 為準；參閱 [完整索引](INDEX.md)。

幸村使用赤漆面頰，家康使用黑鐵金飾。真人頭部、雙眼與原有頭盔仍保留。面罩為自製遊戲造型，並非歷史實物的精確復原。

## 幾何與材質

`build_commander_menpo.py` 讀取已提交的 v17 `*-face.blend`，以皮膚表面射線貼合鼻翼、面頰與下顎，再把鼻翼等細部包進曲面外殼。面罩包含 2 mm 厚度、內外表面、邊壁、金屬捲邊及真正鏤空的口部開口。真人頭部仍在面罩內，並未用平面皮膚代替。

兩位共用網格生成方式，配合臉型微調寬度；沿用 `samurai woven cords and fittings` 材質的漆、鐵、金屬區域。新增 1,332 三角面、約 52 KB GLB／人，沒有新增貼圖、材質區塊或骨架。兩位仍低於 80,000 三角面、92 骨、5 材質區塊；全場仍使用 14 張模型 PNG。

幸村 GLB 約 6.05 MB（不含外部貼圖），原有 6 MB 上限因此明確調整為 6.1 MB。面數上限、材質數和小兵預算保持原值，沒有為了通過檢查放寬這些限制。

## 綁定修正

v17 的高度式頸部混合權重延伸到下顎，強烈轉頭時會讓皮膚與剛性的面罩產生錯位。v18 把過渡移到 z=1.64–1.74 m，顎部與面罩均完整跟隨 `body.head`，頸部底端仍混合 `body.spine02`。整套沿用幸村八個、家康六個動作；家康面罩併入原材質區塊，繼續使用 GPU 骨骼動畫。

## 眉眼與殺氣

直接使用已驗證的 Rocketbox 頭部 `BrowDownLeft/Right`、`EyeBlinkLeft/Right` 形變，增加壓眉並適度收窄眼瞼；另在幾何上壓低內側眉骨、突出眉脊並雕出眉間皺褶。幸村保留少量左右差異，家康採對稱、較沉重的眉壓。雙眼仍清楚露出，不是加黑條遮住原本的眼睛。

表情烘入靜態網格，沒有新增 runtime morph target 或表情動畫。腳本驗證來源 SHA 及所有 1,707 個頭部頂點的對應，避免形變誤套到別的身體部位。比較頁另保留兩張修改眉眼前的同面罩近景，方便獨立判斷眼神變化。

## 驗證與限制

- `validate_face_motion.py --menpo` 每個動作取 13 個姿勢，共 182 個姿勢；檢查頭部／面罩頂點隨頭骨變換，以及殼體頂點至變形後皮膚的有號距離。負值會使檢查失敗。它不涵蓋所有表面交叉或完整衣甲／武器碰撞。
- `capture-faces.mjs --menpo` 使用 Babylon.js，對照 v17 真人頭部及 v18 面罩的正面、側面、全身、突刺與跑步，共 20 張同相機、同光線截圖。
- 原有頭部權重測試現在涵蓋下顎，防止頸部混合再次移到臉上。遊戲與 Pages 測試驗證載入、戰鬥、GPU 動畫及公開比較頁。
- 沒有新增表情動畫、髮鬚模擬或付費運算；肩甲輪廓與全身插畫質感仍是後續工作。

## 重建

```bash
npm run models:menpo
/workspace/yukimura-tools/render-env/bin/python tools/validate_face_motion.py --menpo
# 啟動 Vite 5180；v17 快照置於 .tmp/menpo-v18/before/，含 shared 貼圖。
node tools/capture-faces.mjs --menpo
python3 tools/menpo_gallery.py
```

`models:faces` 及上游完整模型流程已串接面罩步驟。可編輯成果存於 `assets/optimized/commanders/{yukimura,ieyasu}-menpo.blend`。v17 頭部來源及 Microsoft MIT 授權詳見 [HUMAN_COMMANDER_HEADS.md](HUMAN_COMMANDER_HEADS.md)。
