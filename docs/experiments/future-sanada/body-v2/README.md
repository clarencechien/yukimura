# 未來赤備：全身重新生成與漆金材質（body v2）

頭部沿用已完成的[頭部逐項精修](../head-study/README.md)，本輪只處理身體。前一版程序式重建的甲片過於方塊化，已撤回；這次改回原始的 image gen 參考圖，以 **TRELLIS.2 1536 重新生成全身**，再做材質修正與頭部接合。**沒有用幾何原件取代生成的甲冑。**

## 先看全身

| 修整前：既有頭部＋原 1024 生成身體 | 本輪：1536 重新生成＋漆金材質＋同一顆頭 |
| --- | --- |
| ![修整前正面](before/front.png) | ![本輪正面](refined/front.png) |
| ![修整前斜側](before/three-quarter.png) | ![本輪斜側](refined/three-quarter.png) |
| ![修整前背面](before/back.png) | ![本輪背面](refined/back.png) |

| 部位 | 修整前 | 本輪 |
| --- | --- | --- |
| 頭頸接合 | ![](before/neck.png) | ![](refined/neck.png) |
| 胸甲、腰繩 | ![](before/torso.png) | ![](refined/torso.png) |
| 膝脛、靴 | ![](before/legs.png) | ![](refined/legs.png) |
| 手、前臂 | ![](before/hands.png) | ![](refined/hands.png) |
| 背甲 | ![](before/back-detail.png) | ![](refined/back-detail.png) |

[側面](refined/side.png) · [白模](refined/clay.png) · [胸前白模](refined/clay-torso.png) · [修整前白模](before/clay.png)

兩欄使用同一支 [render_body_v2.py](../../../../tools/render_body_v2.py)、相同鏡位與燈光（Blender 4.3／Cycles CPU、1000²、24 samples、降噪）。「修整前」是頭部研究留下的[靜態接合 GLB](../head-study/fitting/static-fit.glb)。

## 做了什麼

1. **重新生成，比較兩個 seed。** 相同參考圖，`1536_cascade`，seed 1615 與 7 各生成一次（原版為 `1024_cascade`）。原網格由 593 萬面提升到約 1,200 萬面，胸甲橫片、綴繩、膝蓋和脛甲的分隔都更明確。選用 **seed 7**：漆色較紅、胸前繩結與比例較接近參考圖。見 [兩個 seed 的原始輸出](selection/seeds-1615-vs-7.png)（上排 1615、下排 7，未修正材質）。
2. **改用封閉重網格匯出。** 原始網格本身有約 44.9 萬條邊界邊，甲片上會出現黑色裂縫。從快取的原資料重新匯出，開啟 TRELLIS.2 官方範例使用的 `remesh=True`（未重新推論），裂縫消失；代價是細小邊緣稍微變軟。見 [重網格前後對照](selection/remesh-cracks.png)（上：原匯出，下：重網格；右側為白模）。
3. **材質拆分（[trellis_body_materials.py](../../../../tools/trellis_body_materials.py)）。** 生成貼圖把赤漆設成約 0.51 的金屬度，因此整套像銅。依色相、明度與原金屬度把每個貼圖像素分成三類：
   - 赤漆：金屬度 0.51 → 0.016，粗糙度 0.44，色相拉回參考圖的約 4°，再加一層由遮罩控制的淡清漆。
   - 鍍金邊：生成時被畫成銅色的亮邊改為參考圖的老黃銅，保留金屬感。
   - 黑色內甲：低金屬、偏粗糙。

   參考圖的金色只出現在邊緣，背甲與小腿後側卻生成成整片銅板。用形態學開運算找出這些寬面積，改回赤漆，約占貼圖 0.6%。
4. **接回完成的頭部。** 頭部研究的檢視版頭部（37 個網格，含 Rocketbox 眼眶與六文錢）以對稱、修剪式 ICP 對齊生成身體自己的頭盔：縮放 0.2497，鹿角寬度 0.397 對 0.395，與身體的頭盔吻合。在銳利匯出上量測後，換算到重網格的座標系（[換算工具](../../../../tools/transfer_head_fit.py)、[參數](head-fit.json)）。舊頭部依區域及距離刪除，不使用方盒裁切，以免削掉衣領與肩甲頂部。

## 數據

| 項目 | 原版（1024） | 本輪（1536、seed 7） |
| --- | ---: | ---: |
| 原網格三角面 | 5,931,928 | 12,224,520 |
| 身體匯出三角面 | 148,107 | 566,543（重網格） |
| 全身（含頭部）三角面 | 見[接合檢查](../head-study/fitting/mesh-inspection.json) | 718,116 |
| 赤漆平均金屬度 | ~0.7 | 0.016 |
| 近零面積三角形 | 5 | 0 |

推論使用 Modal **H100 80GB**。Seed 7：載入 88.4 秒、推論 153.9 秒、儲存原資料 41.4 秒；重網格匯出 57.3 秒（另一次僅匯出的呼叫，總計 66.3 秒）。Seed 1615：載入 92.1 秒、推論 139.4 秒。不含容器啟動與下載。材質、接合與渲染全在本機 CPU。見 [seed 7 生成紀錄](generation.json) 與 [seed 1615 生成紀錄](generation-seed-1615.json)。

## 下載與檢查

| 檔案 | 用途 | 三角面 | 貼圖 |
| --- | --- | ---: | --- |
| [body-v2.glb](refined/body-v2.glb)（91 MB） | 完整版，後續修整基底 | 718,116 | 身體 4096² 色彩、2048² 金屬／粗糙、1024² 清漆遮罩 |
| [body-v2-preview.glb](refined/body-v2-preview.glb)（57 MB） | 身體減面 45%，檢視器使用 | 448,280 | ≤ 2048² |
| [互動檢視器 ZIP](viewer.zip)（54 MB） | 解壓後開啟 index.html；正／側／背、白模、網格、自轉 | 448,280 | 內嵌 |

GitHub 檔案頁按 **Download raw file**。Blender 可直接匯入 GLB；`.blend` 太大，未放入 Git，可依下方指令重建。

- 幾何：[完整版](refined/mesh-inspection.json)、[檢視版](refined/preview-inspection.json)。0 個近零面積三角形，所有 primitive 都有法線，貼圖內嵌，清漆以 `KHR_materials_clearcoat` 匯出。
- 處理參數：[修整報告](refined/refinement-report.json)、[檢視版報告](refined/preview-report.json)、[渲染紀錄](refined/render-report.json)。
- 檢視器：[瀏覽器驗證](viewer-verification.json)、[桌面](viewer-1280.png)、[手機尺寸](viewer-390.png)。Chromium 軟體 WebGL，本機 HTTP 載入後切斷網路操作，無錯誤、無外部請求、無水平溢出。不是實機效能測試。

## 仍待處理

- **背面是單圖推測。** 背甲仍有幾塊暗斑和金色斑點。
- **手部未另行精修。** 手是 TRELLIS 原生，五指可辨認，但指縫和手背甲仍較糊。
- **頭身仍是搭接。** 頭部與身體是兩組零件，頸部未焊接；目前只做目視檢查，尚未做穿插計算，也未測動態。
- **材質為自動分類。** 依顏色自動判斷，少數邊界像素會判錯，未手繪磨損。
- **尚未進遊戲。** 還沒有骨架、權重、動作、LOD，也沒有替換線上遊戲。

## 重現

在 repo 根目錄執行。生成結果與原資料存於 Modal Volume `yukimura-trellis2-cache/results/future-sanada-body-v2/seed-{1615,7}/`，**未加入 Git**。

```sh
# 生成（GPU）：兩個 seed，原資料在匯出前保存
python tools/run_trellis.py --body-study --seeds 1615,7 --include-source
# 從快取原資料做封閉重網格匯出（GPU，不重新推論）
python tools/run_trellis.py --body-study --seeds 7 --export-only --remesh
# 只下載，不開 GPU
python tools/run_trellis.py --body-study --seeds 7 --download-only

# Blender 4.3 bpy＋NumPy 1.26＋SciPy 1.13（CPU）
python tools/fit_trellis_head_v2.py --body .tmp/body-v2/seed-7/body-high.glb --output .tmp/fit-high.json
python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-7/body-high.glb --no-head --output .tmp/v2-high   # 只為取得銳利匯出的座標系
python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-7/body-remesh.glb --no-head --output .tmp/v2-remesh
python tools/transfer_head_fit.py --fit .tmp/fit-high.json --source-report .tmp/v2-high/refinement-report.json --target-report .tmp/v2-remesh/refinement-report.json --output docs/experiments/future-sanada/body-v2/head-fit.json
python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-7/body-remesh.glb
python tools/package_body_v2.py
python tools/render_body_v2.py --model docs/experiments/future-sanada/body-v2/refined/body-v2.glb --output docs/experiments/future-sanada/body-v2/refined --size 1000 --samples 24 --views front,three-quarter,side,back,clay,neck,torso,hands,legs,back-detail,clay-torso
python tools/inspect_trellis_glb.py --model docs/experiments/future-sanada/body-v2/refined/body-v2.glb --report docs/experiments/future-sanada/body-v2/refined/mesh-inspection.json
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2
CHROMIUM_PATH=<chromium> node tools/check_trellis_head_viewer.mjs --body-v2
```

`run_trellis.py` 也接受環境變數 `modal`／`modal_secret` 作為 Modal token。不要把金鑰寫進程式或 Git。生成使用與頭部研究相同的 Modal image 及 TRELLIS.2 commit `75fbf0183001ed9876c8dbb35de6b68552ee08bd`。

來源與授權沿用[上層說明](../README.md#來源與授權)。眼眶來源見[頭部研究](../head-study/README.md)與 [Rocketbox MIT 授權](../head-study/ROCKETBOX-LICENSE.txt)。檢視器 ZIP 內含 TRELLIS、Rocketbox 及 Babylon.js 授權。
