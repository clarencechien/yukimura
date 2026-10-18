# 未來赤備：頭部逐項精修

本次先處理頭部，不以整個人物增加面數代替修形。這是沿用原設計的頭部重製試作，新的頭部參考有細節改寫，並非原圖的精確幾何還原。

## 最新：頰部通氣框、下巴與共用漆面

重建左右主要通氣框與中央下巴護片，清除對應區域的舊碎面。通氣框以赤漆為主、細黃銅邊收口；框內保留實際開口，後方另放內縮的暗色布襯。下巴改為連續曲面，邊緣依原殼位置配適，中央薄黃銅飾片再投射到新護片上。這是 Blender 局部重建，沒有重新執行 image-to-3D。

| 上一輪 | 本輪 |
| --- | --- |
| ![先前通氣框與下巴碎面](iterations/pass22/mask.png) | ![通氣框與中央下巴修補](refined/mask.png) |
| ![先前側面](iterations/pass22/side.png) | ![目前側面](refined/side.png) |

鼻殼、上唇、眼眶折邊、頰框與下巴共用 512² 漆色及粗糙度貼圖；頰框金邊與下巴飾片共用黃銅色彩及粗糙度。漆面粗糙度約 0.47–0.53，黃銅約 0.40–0.48，並降低原赤漆的過亮反光。這些是細微材質變化，尚未補齊原甲片的磨損與接縫細節。

新增框體、下巴及飾片在匯出高版／檢視版檢查為單一連通、封閉零件，縮放到身體後未出現近零面積三角形；另檢查框內取樣射線、嘴部留空及 GLB 內確實包含共用粗糙度貼圖。框後布襯是另一零件，**不代表通氣孔穿透整個頭，也不代表全頭已封閉或可直接套動畫**。

本輪修整、烘焙與 Cycles 檢查圖使用本機 **CPU**；原始頭部的 TRELLIS.2 生成才使用 Modal H100 GPU。本輪沒有啟動新的 Modal GPU 作業。

**仍需處理**：新舊面罩是搭接零件，外側下顎、通氣框上方頰甲、盔沿與頸肩仍保留生成破面；眼眶兩側皮膚接合及新舊磨損也不一致。尚未焊接、綁骨架或替換遊戲。

## 前一階段：鼻翼、鼻孔與上唇修補

依原模型正側面輪廓重建鼻殼及上唇，清除對應舊面，鼻孔實際穿過鼻殼，後方另有內縮的暗色襯底。鼻孔切割與倒角後清除細碎面，並檢查接回身體的縮放、位移及 float32 精度。新增零件縮小後沒有近零面積三角形，鼻孔取樣射線留空；漆色貼圖沒有未烘焙黑色區域。此階段對照可見[修補前](iterations/pass16/mask.png)及[修補後](iterations/pass22/mask.png)。

## 前一階段：眼眶上緣與鼻樑收邊

上一輪真人眼眶已放入模型，但面罩的三角形截斷留下鋸齒和黑色尖刺。這輪沿連續曲線裁切原網格，交點內插原 UV，並移除舊金邊所在的窄帶，重建有厚度的漆甲折邊與細黃銅捲邊。鼻樑到兩側眼眶共用同一條輪廓，內襯同步調整；新增零件可以在 Blender 中獨立編輯。裁切過程共修整 758 個跨邊界面，產生 1,516 個邊界交點；數字描述局部裁切，不代表全頭重拓樸。

| 上一輪 | 本輪 |
| --- | --- |
| ![先前眼眶鋸齒](iterations/pass12/eyes.png) | ![連續面罩上緣](refined/eyes.png) |
| ![先前側面](iterations/pass12/side.png) | ![目前側面](refined/side.png) |

這次修的是**面罩上緣局部**。該階段保留鼻翼、下半面罩及盔沿的生成破面；鼻翼／上唇及主要通氣框／下巴已於後續局部重建；折邊目前共用新漆色與粗糙度，尚未補齊磨損貼圖；新舊漆面接合也尚未完成整體重拓樸。眼眶仍沿用上一輪的 Rocketbox 靜態表情，六文錢保留六枚薄浮雕與實際方孔。沒有宣稱整個頭部已經封閉或可直接套動畫。

## 前一階段：眼神與六文錢再調整

上一版的程序式眼睛太平、虹膜像分段圓盤，六文錢則像厚按鈕貼在額牌上。這輪改用專案已有的 **Microsoft Rocketbox／MIT 人臉眼眶區域**，保留眼皮形體、原 UV、虹膜色彩與皮膚法線；烘焙皺眉形變並壓低內眉，清除穿過新臉的舊表面。眼眶與面罩間另加內縮的暗色襯層，遮住側面接合空隙；邊緣尚未重拓樸焊接。這是靜態表情，尚未提供獨立視線或眨眼控制。

| 上次交付（第五輪） | 本次修整 |
| --- | --- |
| ![上一版眼神](iterations/pass5/eyes.png) | ![目前眼神](refined/eyes.png) |
| ![上一版錢紋](iterations/pass5/crest.png) | ![目前六文錢](refined/crest.png) |

六文錢改為較大、間距較緊的薄浮雕，加入外緣、內凹錢面、方孔唇邊與微凹凸法線。方孔是穿透錢體的實際幾何，孔後有深色凹座，**不穿透整個頭盔**。去除厚額牌，修補面沿頭盔曲面接合，再從原模型投射烘焙漆色及磨損；原四枚錢紋的顏色在投射前遮除。

本輪重用既有高版，只做本機 Blender CPU 修整、烘焙與渲染，沒有重新開 Modal GPU。模型、檢視器與下方的身體接合圖均同步更新；線上遊戲未替換。

## 檢查順序

1. **眼部**：雙眼是否真的存在；瞳孔、眼白、眼皮是否能辨認；是否被盔沿遮住；正面與斜側面是否合理。
2. **面罩**：鼻樑、鼻孔、嘴部通氣口、下巴輪廓；分辨真正開口與只是黑色貼圖。
3. **六文錢**：確實六枚、三乘二排列、彼此分離、方孔與邊緣清楚。
4. **頭盔與鹿角**：盔沿位置、角尖和分叉、左右厚度、護頸甲片是否黏連。
5. **材質與拓樸**：皮膚不能像金屬，漆甲與金屬反光應有區別；檢查碎片、退化面、減面損失。
6. **接回身體**：比例、脖頸銜接與肩甲干涉，最後才談綁骨架與遊戲 LOD。

## 01：原版補光檢查

| 原版頭部 | 眼部近拍 |
| --- | --- |
| ![原版頭部](baseline/front.png) | ![原版眼部](baseline/eyes.png) |

補光後仍看不到雙眼：眼部已變成平滑表面，六文錢也融合。這不是只調整燈光就能修復的問題。原版約 14.8 萬面，是 TRELLIS.2 全身生成後的匯出網格。

## 02：新頭部參考

![頭部參考](reference.png)

image gen 以原本角色為參考，產生單獨頭部、1254 × 1254 RGBA 透明圖。檢查可見雙眼、六枚分離方孔錢紋、面罩鼻孔和嘴部通氣口、完整鹿角。這是架空未來赤備造型，不是對歷史文物的精確復原。

## 03：H100／1536 實際生成

使用 TRELLIS.2＋DINOv3，單獨給頭部整張輸入，`1536_cascade`、seed 1615。實際解析度也是 1536，原網格 **34,550,544 三角面**。這是空間表示與網格數量，並不是 1536p 影片，也不代表正確的解剖結構。

| 生成後、未局部修整 | Blender 目前修整版 |
| --- | --- |
| ![生成頭部](high/front.png) | ![精修頭部](refined/front.png) |
| ![生成眼部](high/eyes.png) | ![精修眼部](refined/eyes.png) |
| ![生成錢紋](high/crest.png) | ![六枚方孔錢紋](refined/crest.png) |

頭盔、鼻樑、甲片與繫繩比原全身生成更清楚；但生成結果仍只有 **四枚錢紋**，眼睛也不清楚。下面是直接從減面前原網格取出的區域，未平滑或重建：四枚錢紋早已存在，不能歸因於手機面數限制。

![減面前原網格局部白模](source/crest.png)

保留原頂點位置的裁切共 8,083,931 面，邊界只是檢查裁切，不能用來判斷完整頭部是否封閉。原網格表面的密集紋路也不是精雕刻的皮膚細節。

[抽樣誤差報告](source-comparison.json)比較每個區域最多 5,000 個原始頂點到匯出網格最近三角形的距離。頭部高度正規化為 2 時，眼部 95 百分位誤差：高版 0.000568、輕版 0.001259。這是單向、有限抽樣的幾何差距，不檢查貼圖，也不能證明眼睛或錢紋正確。

## 04：實際修整與未通過項目

- **六文錢**：六個分離物件、三乘二排列；薄浮雕、外緣、內凹面、方孔及深色凹座，配合頭盔曲率。
- **眼睛**：改用 Rocketbox 的眼眶／眼皮／眼部網格、皮膚法線及原 UV；作者指定皺眉、內眉下壓，移除舊程序式眼白與虹膜零件。沿用來源素材的眼部高光，尚未製作獨立角膜與視線控制。
- **材質**：拆分漆甲、金屬、布與皮膚；額頭修補面投射烘焙原盔漆色，錢紋增加 512² 色彩與法線貼圖。局部仍需更多不規則磨損與邊緣修整。
- **面罩上緣**：曲線裁切與 UV 內插，另建連續漆甲折邊、黃銅唇邊和內襯；匯出後檢查新增折邊是單一連通且封閉的零件，不代表原下半面罩也封閉。
- **鼻殼／上唇**：重建有厚度的鼻殼與漸薄上唇，鼻孔實際穿透鼻殼，凹腔襯底是另外的零件；尚未焊接到舊頰甲。
- **通氣框／下巴**：重建主要頰框、凹腔布襯、中央下巴護片及薄黃銅飾片；共用漆色與粗糙度貼圖，保留外側原殼待修。
- **清理**：精修高版檢查未見近零面積三角形；此檢查不等於無自相交、全封閉或動畫合格。

第一輪眼皮太亮、像貼上去；第二輪嘗試借用原 UV，造成錢紋拉花。已棄用這兩個結果，留存失敗近拍便於追蹤：

| 第一輪：厚眼皮與貼片感 | 第二輪：UV 拉花 |
| --- | --- |
| ![第一輪問題](iterations/pass1/eyes.png) | ![第二輪問題](iterations/pass2/crest.png) |

**仍需細修**：眼部已有來源人臉結構，面罩上緣已局部重建，但兩側皮膚接合仍不夠自然，來源眼部的烘焙高光也不是完整的物理角膜；面罩有破碎邊緣、漆面高光不連續；嘴部開口比參考圖更大。不能把這些誤稱為完成的戰損。後腦與遮蔽區域是單圖推測，沒有背面真值；面罩尚未重建成乾淨、獨立、有壁厚的零件。

| 精修斜側 | 側面 | 背面 |
| --- | --- | --- |
| ![斜側](refined/three-quarter.png) | ![側面](refined/side.png) | ![背面](refined/back.png) |

## 05：接回原身體的比例試看

| 正面 | 斜側 |
| --- | --- |
| ![靜態接合正面](fitting/front.png) | ![靜態接合斜側](fitting/three-quarter.png) |

移除身體上原頭部區域，以縮放 0.26 的新頭部接入。**這是獨立靜態組裝，尚未焊接頸部、綁骨架或驗證動態穿插。** 護頸與肩甲附近仍有重疊接縫，不能當作可直接套動畫的角色。原身體材質、手指和甲片仍有舊缺陷，接合檢查保留原身體的 5 個近零面積三角形；頭部高版與檢視版則為 0。沒有替換線上遊戲。

下一輪順序：接著修通氣框上方頰甲、外側下顎與盔沿，再處理頸部、肩甲及材質一致性；造型穩定後才進行骨架、權重與實機 LOD。

## 下載與檢查

| 檔案 | 用途 | 三角面 | 貼圖 |
| --- | --- | ---: | --- |
| [生成高版 GLB](head-high.glb) | 保留生成結果，66.29 MB | 494,558 | 4096² |
| [生成輕版 GLB](head-light.glb) | 減面比較，19.46 MB | 148,229 | 2048² |
| [精修高版 GLB](refined/head-refined.glb) | 後續修整基底 | 531,710 | 原 4096²＋眼眶素材＋新增 512² |
| [精修檢視版 GLB](refined/head-preview.glb) | 約 29.5 MB、保留人臉眼眶與獨立錢紋 | 205,753 | 2048²＋眼眶素材＋512² |
| [Blender 原檔](refined/head-refined.blend) | 已內嵌材質，物件可分別編輯 | 高版 | 內嵌 |
| [互動檢視器 ZIP](viewer.zip) | 解壓後開啟 index.html、旋轉／白模／線框 | 檢視版 | 內嵌 |
| [接合 GLB](fitting/static-fit.glb) | 僅供靜態比例檢查 | 見檢查報告 | 內嵌 |

GitHub 檔案頁請按 **Download raw file**。本頁圖片可直接在 GitHub 文件查看；這次成果不在 Pages 遊戲內，也沒有把研究頁部署成網站。檢視器程式與模型均內嵌，測試詳見 [瀏覽器報告](viewer-verification.json)；手機尺寸模擬不代表實機效能。檢視版仍偏重，不是已驗證的手機 LOD。

[高版幾何檢查](high-inspection.json) · [輕版幾何檢查](light-inspection.json) · [精修幾何檢查](refined/mesh-inspection.json) · [檢視版檢查](refined/preview-inspection.json) · [匯出零件數驗證](part-verification.json) · [鼻殼／上唇檢查](refined/nasal-verification.json) · [檢視版鼻殼檢查](refined/nasal-preview-verification.json) · [通氣框／下巴檢查](refined/lower-verification.json) · [檢視版下巴檢查](refined/lower-preview-verification.json) · [修整參數](refined/refinement-report.json) · [接合參數](fitting/fit-report.json) · [接合幾何檢查](fitting/mesh-inspection.json) · [生成紀錄](generation.json) · [下載大小及 SHA-256](downloads.json) · [運算停止狀態](compute-status.json)

## 計算與重現

生成使用 Modal **H100 80GB**，載入約 93.7 秒、推論約 189.5 秒、保存原資料約 115.8 秒、高／輕版匯出約 98.1／38.5 秒，GPU 函式共約 549.4 秒。這不是帳單工時，未含環境準備、容器啟動及下載。Blender 修整、烘焙及 Cycles 檢查圖使用本機 CPU。高版和精修版比較圖均為 1000²／20 samples／相同檢查燈光；原網格及輕版局部圖為 900²／12 samples。

原始幾何約 284 MB、體素材質約 394 MB，保存於 Modal Volume `yukimura-trellis2-cache/results/future-sanada-head-v1/`，**未加入 Git**。在 `/workspace/yukimura`：

```sh
# 只下載，沒有重新推論；原資料存入被忽略的 .tmp/
/workspace/yukimura-tools/bin/python tools/run_trellis.py --head-study --download-only --include-source

# Blender 4.3.0 / bpy；numpy 1.26.4
/workspace/yukimura-tools/render-env/bin/python tools/refine_trellis_head.py
/workspace/yukimura-tools/render-env/bin/python tools/package_head_study.py
/workspace/yukimura-tools/render-env/bin/python tools/head_study_render.py --model docs/experiments/future-sanada/head-study/refined/head-refined.glb --output docs/experiments/future-sanada/head-study/refined --samples 20 --size 1000
/workspace/yukimura-tools/render-env/bin/python tools/render_trellis_study.py --model docs/experiments/future-sanada/head-study/fitting/static-fit.glb --output docs/experiments/future-sanada/head-study/fitting --size 1000 --samples 16 --skip-scene
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/head-study --head-study
python3 tools/verify_trellis_head_parts.py
python3 tools/verify_trellis_nasal.py --model docs/experiments/future-sanada/head-study/refined/head-refined.glb --report docs/experiments/future-sanada/head-study/refined/nasal-verification.json
python3 tools/verify_trellis_nasal.py --model docs/experiments/future-sanada/head-study/refined/head-preview.glb --report docs/experiments/future-sanada/head-study/refined/nasal-preview-verification.json
python3 tools/verify_trellis_lower_mask.py --model docs/experiments/future-sanada/head-study/refined/head-refined.glb --report docs/experiments/future-sanada/head-study/refined/lower-verification.json
python3 tools/verify_trellis_lower_mask.py --model docs/experiments/future-sanada/head-study/refined/head-preview.glb --report docs/experiments/future-sanada/head-study/refined/lower-preview-verification.json
node tools/check_trellis_head_viewer.mjs
```

`tools/trellis_head_modal.py` 使用本帳號已建好的 Modal image `im-CWPfod9BzDeCjqD07JU8Ui`，固定 TRELLIS.2 程式提交 `75fbf0183001ed9876c8dbb35de6b68552ee08bd`。其他帳號需先依原流程建立相同環境並替換 image ID。省略 `--download-only` 會重新使用 GPU 生成；`--export-only` 可從已快取原資料補匯出，仍需要 GPU。原資料在任何簡化之前保存；每次下載驗證 SHA-256。

來源授權沿用[上層說明](../README.md#來源與授權)；新增參考圖由 image gen 產生，不是歷史文物掃描。

眼眶來源：[Microsoft Rocketbox](https://github.com/microsoft/Microsoft-Rocketbox)，Male Adult 10，固定提交 `0943055db6ec570bcef9f2c8b41c9e5467c808f9`，沿用 repo 已有且經 SHA-256 驗證的 `public/review/candidates/rocketbox.glb`。[MIT 授權副本](ROCKETBOX-LICENSE.txt)也已放入下載檢視器。修改包括裁切眼眶區域、非等比配適、表情形變、膚色材質調整與一次細分插值；不是新增的人臉掃描，也不代表新增了高頻幾何細節。
