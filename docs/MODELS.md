# 共用武士模型套件 v6・幸村甲冑精修

本版由本機 Blender 4.3.2 CPU 產生並接入 Babylon.js。未呼叫 Modal 或付費 3D 生成服務。此前的 image gen 人物／戰場圖是美術目標，**目前模型仍未達到那兩張插畫的造型與細節品質**。

## 可編輯資產與重建

- `assets/source/samurai-kit.blend`：792 個具名零件（共用套件＋幸村專用）、四個組裝角色、幸村骨架及封裝的 2D 參考圖。
- `tools/build_models.py`：幾何、配色、縫隙遮蔭與匯出。
- `tools/refine_hero.py`：幸村專用胸甲、兜、鹿角、面甲、肩甲、草摺、袴褲、足袋、槍刃及披風。
- `tools/painted_surfaces.py`：可重複產生的筆觸、繫繩、磨損、布紋與 PBR 圖集。
- `tools/samurai_rig.py`：14 根骨骼，idle／run／slash／reverse／thrust／spin 六個動作；硬甲剛性綁定，披風頂端與胸部混合權重。
- `tools/gltf_assets.py`：將 GLB 內重複貼圖抽成共用檔案，重新排列二進位 buffer views。
- `public/models/manifest.json`：本次面數、幾何大小及共用貼圖清單。

```sh
npm run models
npm run models:preview
npm test
npm run test:e2e
```

Blender 使用內附 NumPy，不需要下載模型或安裝貼圖工具。Cycles 預覽使用 CPU、2 執行緒、32 samples。重新執行 `models` 會覆寫生成的 `.blend` 和 GLB；手工修改請另存或回寫 Python 配方。

Blender Outliner 的 `00_SHARED_PARTS` 預設隱藏，內含 linked mesh 零件。四個 `10_*` collection 保留可編輯的組裝；`SanadaRig` 與 `yukimura_runtime` 保留匯出的骨架和六組 NLA 動作，為避免展示圖重疊預設 hide_render。2D 參考在 `REFERENCE` collection，不匯出到 GLB。

## 模型與下載預算

| 角色 | 三角形 | GLB 幾何／動畫大小 | 骨架 |
|---|---:|---:|---|
| 幸村 | 43,290 | 2.50 MiB | 14 骨、6 動作 |
| 赤備足輕 | 3,010 | 208 KiB | 無，幾何實例 |
| 德川足輕 | 2,866 | 188 KiB | 無，幾何實例 |
| 家康・修羅之影 | 8,520 | 494 KiB | 無，幾何實例 |

每個角色一個 primitive／一個 PBR 材質。三張共用貼圖合計約 1.50 MiB：1024² pigment、512² normal、512² roughness/metalness。四個 GLB 加上共用貼圖合計約 **4.87 MiB**。所有 GLB 引用相同的內容雜湊 URL，瀏覽器可共用資源。

**GLB 現在有外部貼圖依賴**：部署或搬移資產時必須一起保留 `public/models/shared/`，不能只搬四個 GLB。貼圖沒有遠端 CDN 依賴，也沒有前端憑證。

只有幸村使用可變形骨架；敵兵和隊友沿用共用幾何實例，避免每兵增加骨架計算。幸村直接使用載入的 skinned mesh，因此動畫綁定的是畫面上的角色。移動切換 run、攻擊依序觸發 slash／reverse／thrust／spin、靜止 idle；暫停停止動作時間。接地陰影另有繪製成本。

## 本次造型與材質

- 四段收腰胸甲，保留較大漆紅面與少量銅釘，取代等距圓筒狀胸甲。
- 五層帶厚度肩甲與肩頂護片、七組各五層草摺；輪廓和繫繩由幾何形成。
- 重做兜頂、護頸、眉庇、完整面甲與護喉；連續分叉鹿角取代分段圓錐接頭。
- 有方孔的六文錢銅飾、護腕、束口袴褲、較低的足袋輪廓、帶稜線的十文字槍刃。
- 垂墜披風和不規則下擺，背部六文錢沿布褶貼合。肩甲在近景及揮槍姿態檢查後外移，修正袖子穿出。
- 降低表面雜訊，區分漆甲、舊金與布的粗糙度；胸甲移除重複過密的繫繩印紋，改用較乾淨的磨損圖塊。
- 曲面甲片使用連續法線；維持相同 43,290 三角形，消除逐格硬邊造成的重複頂點後，GLB 從 4.36 MiB 降到 2.50 MiB。

主角資產檢查上限為 45k 三角形、3 MB 幾何／動畫；足輕仍各不超過 3,200 三角形。這是專案下載與幾何預算，不是實體手機效能保證。每個角色仍是一個 primitive／材質，主角六組動畫沿用原骨架；沒有為大量敵兵套用主角模型。

這一輪是專用幾何與共用程序材質的精修，**仍不等同於設定插畫品質，也不是完成高精度雕刻、重拓樸及高模烘焙**。法線圖仍由表面配方產生，AO 為頂點近距離遮蔭；尚無獨立手繪角色貼圖或 LOD。Modal 算力不會自行修正造型，這次使用本機 Blender CPU，未產生付費建模呼叫。

## 如何看實際結果

- `docs/art/models-lineup.png`：Blender Cycles 組装預覽。
- `docs/art/hero-runtime-front.png`、`hero-runtime-back.png`、`hero-runtime-side.png`、`hero-runtime-slash.png`：實際 GLB 在 Babylon.js 的近景與動作。
- `docs/art/hero-runtime-detail.png`：頭肩近景；`hero-runtime-pbr.png`：同模型不套墨線／紙色後處理的 PBR 近景。
- `docs/screenshots/battle.png`、`mobile.png`：遊戲畫面。
- `tools/model-preview.html`：Vite 開發服務中的模型檢視工具，支援旋轉、縮放、六組動作；不列入正式遊戲 UI 或 production bundle。開啟 Vite 後執行 `node tools/capture-model.mjs` 可重拍以上六張實際 GLB 截圖。

目前僅通過 Chromium 軟體 WebGL 的功能測試和手機尺寸／觸控模擬。這不等於實體手機效能測試；尚無真機 FPS 或熱降頻資料，也沒有全軍骨架動畫、布料物理、LOD 或完整高模到低模烘焙流程。

可選 Modal 腳本已同步攜帶 helper modules 與回收共用貼圖，但本次未執行遠端流程。它使用帳戶 CPU 資源；結果成功回傳後才寫入本機資產。
