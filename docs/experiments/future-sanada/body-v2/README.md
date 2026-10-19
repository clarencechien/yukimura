# 未來赤備：全身重新生成與漆金材質（body v2）

頭部沿用已完成的[頭部逐項精修](../head-study/README.md)，本輪只處理身體。前一版程序式重建的甲片過於方塊化，已撤回；這次改回原始的 image gen 參考圖，以 **TRELLIS.2 1536 重新生成全身**，再做材質修正與頭部接合。**沒有用幾何原件取代生成的甲冑。**

## 最新：頸部清理（pass 4）

移除生成的頭部時，連帶截斷了頸部的繩子，留下兩段**懸在半空的流蘇尖**；舊頭部的頸口也空著，背後的頸甲（しころ）與衣領之間露出一道**黑縫**。上排是 pass 3，下排是本輪（1000²、24 samples）。

| | 正面 | 側面 | 背面 | 背面白模 |
| --- | --- | --- | --- | --- |
| pass 3 | ![](pass4/before/neck-front.png) | ![](pass4/before/neck-side.png) | ![](pass4/before/neck-back.png) | ![](pass4/before/clay-neck-back.png) |
| 本輪 | ![](pass4/renders/neck-front.png) | ![](pass4/renders/neck-side.png) | ![](pass4/renders/neck-back.png) | ![](pass4/renders/clay-neck-back.png) |

| 正面 | 斜側 | 側面 | 背面 | 白模 |
| --- | --- | --- | --- | --- |
| ![](pass4/renders/front.png) | ![](pass4/renders/three-quarter.png) | ![](pass4/renders/side.png) | ![](pass4/renders/back.png) | ![](pass4/renders/clay.png) |

**做法（[工具](../../../../tools/neck_cleanup.py)、[報告](pass4/neck-report.json)）**

1. **移除懸空碎片。** 生成的網格本來就有許多獨立零件，例如鉚釘、流蘇、繩結。因此不以「是否相連」判斷，而是看每塊與其他所有表面的最近距離：
   - 距離超過 6 mm 的視為懸空，共移除 13 塊、936 個頂點。
   - 其中包括兩段流蘇尖（分別離最近表面 6.5 cm 與 4.5 cm），以及頭盔內看不到的殘片。
2. **頸部內襯。** 在頭盔下方加一段深色布質內襯，形狀是從頸部中心向外量出來的：
   - 每個角度、每個高度各發一條射線，找到頸甲、衣領或面罩的內側，內襯就放在內側往內 4 mm 處，再平滑。
   - 原本試過固定橢圓，但後頸開口最寬，橢圓放太深擋不住，因此改用量測。

**檢查**：完整版 742,910 面，檢視版 474,114 面；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass4/mesh-inspection.json)、[檢視版](pass4/preview-inspection.json)）。[互動檢視器 ZIP](viewer.zip)（58 MB）已改用本輪模型，並通過桌面與手機尺寸的離線瀏覽器檢查（[報告](viewer-verification.json)）。

**下載**：[body-v2-pass4.glb](pass4/body-v2-pass4.glb)（93 MB，完整版）· [body-v2-pass4-preview.glb](pass4/body-v2-pass4-preview.glb)（59 MB）

**仍待處理**

- **頭與身體尚未焊接。** 兩者仍是分開的零件，目前只是靠內襯擋住縫隙。
- **還不能進遊戲。** 骨架、權重、動作與 LOD 都還沒做。

```sh
python tools/neck_cleanup.py --model docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb --output docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb
python tools/package_body_v2.py --model docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb --directory docs/experiments/future-sanada/body-v2/pass4 --name body-v2-pass4-preview
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass4
```

## 前一階段：手甲、手套、腿甲與能量槽（pass 3）

背甲與裙甲完成後，接著處理四肢。上排是 pass 2，下排是本輪；鏡位與燈光相同（1000²、24 samples）。第三欄是**去掉燈光的原色**：金屬金在暗攝影棚只反射暗環境，有燈光的圖會讓金色指節看起來偏暗。

| | 右手 | 左手 | 左手原色 | 左前臂 | 膝甲 | 左脛甲近拍 |
| --- | --- | --- | --- | --- | --- | --- |
| pass 2 | ![](pass3/before/hand-r-front.png) | ![](pass3/before/hand-l-front.png) | ![](pass3/before/albedo-hand-l.png) | ![](pass3/before/forearm-l.png) | ![](pass3/before/knees.png) | ![](pass3/before/seam-shin-l.png) |
| 本輪 | ![](pass3/renders/hand-r-front.png) | ![](pass3/renders/hand-l-front.png) | ![](pass3/renders/albedo-hand-l.png) | ![](pass3/renders/forearm-l.png) | ![](pass3/renders/knees.png) | ![](pass3/renders/seam-shin-l.png) |

[正面](pass3/renders/front.png) · [斜側](pass3/renders/three-quarter.png) · [背面](pass3/renders/back.png) · [右手原色](pass3/renders/albedo-hand-r.png) · [左手白模](pass3/renders/clay-hand-l-out.png)

**做法**

1. **四肢套用原圖投影。** 胸甲與前裙甲用的投影，延伸到袖甲、手甲、手套、膝甲、脛甲與靴子。各區只投正面，因為只有軀幹有背面來源圖。
   - 手套有了原圖的金色指節、紅色手背甲與金框，以及機械質感的黑色手套紋理。
   - 手指形狀沿用 TRELLIS 生成，白模可見五指與放鬆姿勢都還算完整，本輪沒有更動幾何。
2. **能量槽改成實體發光條。** 原圖的橘色能量槽只有 1–3 px 寬，比投影對齊的誤差（光流中位數約 20 px）還細。
   - 直接把發光畫進貼圖時，會把金邊和漆面高光誤判成光，變成到處散落的光點；這個試算已棄用。
   - 改為在原圖找出 8 條槽的中心線（[座標](pass3/energy-seams.json)、[尋找工具](../../../../tools/find_energy_seams.py)）：左右前臂、左胸側、兩個膝甲鏡片、兩條脛甲。
   - 以光流反推，再從正面射線投到身體表面，鋪上圓頂狀的發光條，下方加一道暗色槽（[工具](../../../../tools/energy_seam_strips.py)、[報告](pass3/energy-seam-report.json)）。
   - 發光以 glTF emissive＋`KHR_materials_emissive_strength` 匯出。

**檢查**：完整版 743,438 面，檢視版 473,718 面；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass3/mesh-inspection.json)、[檢視版](pass3/preview-inspection.json)）。互動檢視器隨後改用 pass 4 模型。

**下載**：[body-v2-pass3.glb](pass3/body-v2-pass3.glb)（93 MB，完整版）· [body-v2-pass3-preview.glb](pass3/body-v2-pass3-preview.glb)（59 MB）

**仍待處理**

- **能量槽偏白。** 在 Cycles／AgX 下，發光強度 ≥ 3 都會顯示成接近白色的核心；原圖本身也是白芯，只是外圍的橘色光暈沒有後製泛光。
- **手部背面沒有原圖。** 手掌與手背後側仍是生成貼圖。
- **頸部與骨架尚未處理。** 頸部還沒焊接，也還沒綁骨架。

```sh
python tools/project_reference.py --output docs/experiments/future-sanada/body-v2/pass3 --output-glb .tmp/v4/projected.glb
python tools/back_plate_shell.py --model .tmp/v4/projected.glb --output docs/experiments/future-sanada/body-v2/pass3 --name body-v2-shell.glb
python tools/find_energy_seams.py
python tools/energy_seam_strips.py --model <上一步的 body-v2-shell.glb> --output docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb
python tools/render_albedo.py --model docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb --output hand.png --target 0.376,-0.16,0.89 --span .35
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass3
```

## 前一階段：背甲與裙甲精修（pass 2）

背甲上下與前後裙甲仍有問題，本輪改為針對這兩處修整。上排是前一版，下排是本輪；鏡位與燈光相同（1000²、24 samples）。

| | 背甲上半 | 背甲下半／腰帶 | 前裙甲 | 後裙甲 |
| --- | --- | --- | --- | --- |
| 前一版 | ![](pass2/before/back-upper.png) | ![](pass2/before/back-lower.png) | ![](pass2/before/skirt-front.png) | ![](pass2/before/skirt-back.png) |
| 本輪 | ![](pass2/renders/back-upper.png) | ![](pass2/renders/back-lower.png) | ![](pass2/renders/skirt-front.png) | ![](pass2/renders/skirt-back.png) |

| 背甲白模：前一版 | 背甲白模：本輪 | 本輪正面 | 本輪背面 |
| --- | --- | --- | --- |
| ![](pass2/before/clay-back-upper.png) | ![](pass2/renders/clay-back-upper.png) | ![](pass2/renders/front.png) | ![](pass2/renders/back.png) |

**做法**

1. **把原圖投影回模型（前面）。** TRELLIS 的貼圖原本就是從同一張插畫生成，只是較糊。先以輪廓對齊原圖（重疊度 IoU 0.856），再用光流修正局部偏移（中位數約 20 px）。可見性以 z-buffer 判斷，再把原圖直接投到胸甲、腰帶與前裙甲（[投影工具](../../../../tools/project_reference.py)）。
   - 前裙甲因此有了原圖的金色波紋、黑色綴繩與鱗狀內襯。
   - 立體繩結與流蘇的位置和畫面不同，所以保留原本的紅色，不投影。
2. **背面來源圖。** 原圖沒有背面，因此用正面乾淨的部位組成[背面來源圖](pass2/back-reference.png)（[產生工具](../../../../tools/build_back_reference.py)）：
   - 背甲：取避開流蘇的五片胸前橫片，左右鏡像、依片距 37 px 往上延伸。
   - 中央裙板：繩結改以同一塊裙板的橫片補上。
3. **背甲外殼（[工具](../../../../tools/back_plate_shell.py)）。** 生成的背甲是封閉網格，但薄殼上有貫穿的洞，補洞處理不到。
   - 改在背甲表面加一層外殼：形狀由每格一條射線量出的實際表面決定，只有洞裡改用穩健多項式補平。
   - 依背面來源圖的橫片縫隙做出逐片重疊的高低差，邊緣沉入身體 5 mm，不會看到方框。
   - 貼圖直接用清晰的來源圖。生成的背甲仍保留在下面，沒有刪除。
4. **後裙甲不投影。** 試過兩種投影：直接投會讓綴繩重複一層，只取低頻色會變得髒亂並拖出金色條紋。
   - 去掉燈光檢查原色後，發現生成的後裙甲其實是乾淨的紅板加金邊，偏白是背光照在漆面造成的。
   - 因此只用保邊的雙邊濾波去除斑點。
5. **其他。**
   - 在胸甲與裙甲範圍補上 313 個小破洞（3–48 條邊）。
   - 非金屬部分的粗糙度至少 0.52，清漆減為原來的 0.66 倍，減少漆面泛白。

**檢查**：完整版 742,091 面，檢視版 472,372 面；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass2/mesh-inspection.json)、[檢視版](pass2/preview-inspection.json)）。互動檢視器隨後改用 pass 3 模型。參數見[投影報告](pass2/projection-report.json)、[背甲外殼報告](pass2/back-plate-report.json)、[對齊參數](pass2/alignment.json)。

**下載**：[body-v2-pass2.glb](pass2/body-v2-pass2.glb)（92 MB，完整版）· [body-v2-pass2-preview.glb](pass2/body-v2-pass2-preview.glb)（58 MB，身體減面 45%）

**仍待處理**

- **後裙甲仍偏亮。** 這是漆面在背光下的反光，原色沒有問題。
- **背面是推測。** 背甲的橫片沿用胸前的設計。
- **立體細節不一定對位。** 前裙甲投上的綴繩，未必每一列都對準模型上的凸起。
- **手部與頸部尚未處理。** 手部還沒精修，頸部也還沒焊接。

```sh
# 在 repo 根目錄，Blender 4.3 bpy＋NumPy＋SciPy＋OpenCV 4.10（CPU）
python tools/fit_reference_silhouette.py --vertices <生成身體頂點.npy>
python tools/build_back_reference.py
python tools/project_reference.py
python tools/back_plate_shell.py
python tools/package_body_v2.py --model docs/experiments/future-sanada/body-v2/pass2/body-v2-pass2.glb --directory docs/experiments/future-sanada/body-v2/pass2 --name body-v2-pass2-preview
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass2
```

## 先看全身（第一版）

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
| [互動檢視器 ZIP](viewer.zip)（58 MB） | 已改用 pass 4 模型；解壓後開啟 index.html | 474,114 | 內嵌 |

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
