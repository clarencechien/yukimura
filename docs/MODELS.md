# 共用武士模型套件 v7・雙手槍術與全軍動畫

本版由本機 Blender 4.3.2 CPU 產生並接入 Babylon.js。未呼叫 Modal 或付費 3D 生成服務。此前的 image gen 人物／戰場圖是美術目標，**目前模型仍未達到那兩張插畫的造型與細節品質**。

## 可編輯資產與重建

- `assets/source/samurai-kit.blend`：806 個具名零件（共用套件＋幸村專用）、四個組裝角色、四套角色骨架及封裝的 2D 參考圖。
- `tools/build_models.py`：幾何、配色、縫隙遮蔭與匯出。
- `tools/refine_hero.py`：幸村專用胸甲、兜、鹿角、面甲、肩甲、草摺、袴褲、足袋、槍刃及披風。
- `tools/painted_surfaces.py`：可重複產生的筆觸、繫繩、磨損、布紋與 PBR 圖集。
- `tools/samurai_rig.py`：18 根骨骼；幸村八組動作，其他角色五組動作；雙手與雙腿以離線 IK 編排，硬甲剛性綁定，雙節披風及草摺混合權重。
- `tools/gltf_assets.py`：將 GLB 內重複貼圖抽成共用檔案，重新排列二進位 buffer views。
- `tools/bake-crowd.mjs`：以 Babylon.js 離線計算 60fps 骨骼矩陣，寫出共用 GPU palette。
- `src/crowd-motion.ts`：Babylon.js 原生 BakedVertexAnimationManager，每個實例獨立選擇動作與影格。
- `public/models/manifest.json`：本次面數、幾何大小及共用貼圖清單。

```sh
npm run models
npm run models:preview
npm test
npm run test:e2e
```

Blender 使用內附 NumPy，不需要下載模型或安裝貼圖工具。Cycles 預覽使用 CPU、2 執行緒、32 samples。重新執行 `models` 會覆寫生成的 `.blend` 和 GLB；手工修改請另存或回寫 Python 配方。

Blender Outliner 的 `00_SHARED_PARTS` 預設隱藏，內含 linked mesh 零件。四個 `10_*` collection 保留可編輯的組裝；各角色的 rig 與 runtime 物件保留匯出的骨架和 NLA 動作，為避免展示圖重疊預設 hide_render。2D 參考在 `REFERENCE` collection，不匯出到 GLB。

## 模型與下載預算

| 角色 | 三角形 | GLB 幾何／動畫大小 | 骨架 |
|---|---:|---:|---|
| 幸村 | 44,130 | 2.60 MiB | 18 骨、8 動作 |
| 赤備足輕 | 3,010 | 412 KiB | 18 骨、5 動作 |
| 德川足輕 | 2,866 | 382 KiB | 18 骨、5 動作 |
| 家康・修羅之影 | 8,520 | 824 KiB | 18 骨、5 動作 |

每個角色一個 primitive／一個 PBR 材質。三張共用貼圖合計約 1.51 MiB：1024² pigment、512² normal、512² roughness/metalness。三種 NPC 共用同一份 356,288 bytes 的 Float32 動畫 palette；四 GLB、貼圖及 palette 合計約 **6.04 MiB**，另有小型 JSON 索引。

部署時需一併保留 `public/models/shared/`（貼圖及動畫 .bin）與 `crowd-animation.json`，不能只搬四個 GLB。資產沒有遠端 CDN 或前端憑證依賴。

幸村以單一 skinned mesh 採樣動作，並混合切換姿態。群兵使用真正的 InstancedMesh，共用幾何與 GPU 骨骼矩陣；不為每個士兵建立 CPU 骨架。各角色擁有獨立動作時間、攻擊前搖、受擊與倒地狀態；暫停與命中頓挫會凍結影格。動畫預覽工具用 GLTF 骨架播放 NPC，瀏覽器測試另比對離線 palette 與 Babylon 載入的骨架矩陣，檢查烘焙座標一致。

## 本次造型與材質

- 四段收腰胸甲，保留較大漆紅面與少量銅釘，取代等距圓筒狀胸甲。
- 五層帶厚度肩甲與肩頂護片、七組各五層草摺；輪廓和繫繩由幾何形成。
- 重做兜頂、護頸、眉庇、完整面甲與護喉；連續分叉鹿角取代分段圓錐接頭。
- 有方孔的六文錢銅飾、護腕、束口袴褲、較低的足袋輪廓、帶稜線的十文字槍刃。
- 垂墜披風和不規則下擺，背部六文錢沿布褶貼合。肩甲在近景及揮槍姿態檢查後外移，修正袖子穿出。
- 降低表面雜訊，區分漆甲、舊金與布的粗糙度；胸甲移除重複過密的繫繩印紋，改用較乾淨的磨損圖塊。
- 曲面甲片使用連續法線；新手甲與彎曲手指改善握槍形狀，修正右手錯綁胸骨。槍桿與槍刃共用剛性變換，避免原比例調整使兵器彎折。
- 降低過重黑邊、細化繫繩，保留朱紅彩度；戰場加強暖主光與冷色陰影，減輕霧遮蔽。

主角資產檢查上限為 45k 三角形、3 MB 幾何／動畫；足輕仍各不超過 3,200 三角形。這是專案下載與幾何預算，不是實體手機效能保證。每個角色仍是一個 primitive／材質，主角八組動畫使用 18 骨架；沒有為大量敵兵套用主角模型。

這一輪是專用幾何與共用程序材質的精修，**仍不等同於設定插畫品質，也不是完成高精度雕刻、重拓樸及高模烘焙**。法線圖仍由表面配方產生，AO 為頂點近距離遮蔭；尚無獨立手繪角色貼圖或 LOD。Modal 算力不會自行修正造型，這次使用本機 Blender CPU，未產生付費建模呼叫。

## 如何看實際結果

- `docs/art/models-lineup.png`：Blender Cycles 組装預覽。
- `docs/art/hero-runtime-front.png`、`hero-runtime-back.png`、`hero-runtime-side.png`、`hero-runtime-slash.png`：實際 GLB 在 Babylon.js 的近景與動作。
- `docs/art/hero-runtime-detail.png`：頭肩近景；`hero-runtime-pbr.png`：同模型不套墨線／紙色後處理的 PBR 近景。
- `docs/screenshots/battle.png`、`mobile.png`：遊戲畫面；`animated-army.png` 為 100 敵兵加 10 隊友的測試情境。
- `docs/art/hero-motion.webm`、`army-motion.webm`：實際引擎錄影。Vite 開啟後用 `node tools/capture-motion.mjs` 重拍，需先 `npx playwright install ffmpeg`。
- `tools/model-preview.html`：Vite 開發服務中的模型檢視工具，支援旋轉、縮放、八組動作；`?model=ashigaru` 可看足輕；不列入正式遊戲 UI 或 production bundle。開啟 Vite 後執行 `node tools/capture-model.mjs` 可重拍以上六張實際 GLB 截圖。

目前僅通過 Chromium 軟體 WebGL 的功能測試和手機尺寸／觸控模擬。這不等於實體手機效能測試；尚無真機 FPS 或熱降頻資料，也沒有布料物理、LOD 或完整高模到低模烘焙流程。

可選 Modal 腳本已同步攜帶 helper modules 與回收共用貼圖，但本次未執行遠端流程。它使用帳戶 CPU 資源；結果成功回傳後才寫入本機資產，再以本機 Node.js／Babylon.js 生成群兵 palette。
