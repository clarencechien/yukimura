# 共用武士模型套件 v5・貼圖與骨架

本版由本機 Blender 4.3.2 CPU 產生並接入 Babylon.js。未呼叫 Modal 或付費 3D 生成服務。此前的 image gen 人物／戰場圖是美術目標，**目前模型仍未達到那兩張插畫的造型與細節品質**。

## 可編輯資產與重建

- `assets/source/samurai-kit.blend`：393 個共用具名零件、四個組裝角色、幸村骨架及封裝的 2D 參考圖。
- `tools/build_models.py`：幾何、配色、縫隙遮蔭與匯出。
- `tools/painted_surfaces.py`：可重複產生的筆觸、繫繩、磨損、布紋與 PBR 圖集。
- `tools/samurai_rig.py`：14 根骨骼，idle／run／slash 三個動作；硬甲剛性綁定，披風頂端與胸部混合權重。
- `tools/gltf_assets.py`：將 GLB 內重複貼圖抽成共用檔案，重新排列二進位 buffer views。
- `public/models/manifest.json`：本次面數、幾何大小及共用貼圖清單。

```sh
npm run models
npm run models:preview
npm test
npm run test:e2e
```

Blender 使用內附 NumPy，不需要下載模型或安裝貼圖工具。Cycles 預覽使用 CPU、2 執行緒、32 samples。重新執行 `models` 會覆寫生成的 `.blend` 和 GLB；手工修改請另存或回寫 Python 配方。

Blender Outliner 的 `00_SHARED_PARTS` 預設隱藏，內含 linked mesh 零件。四個 `10_*` collection 保留可編輯的組裝；`SanadaRig` 與 `yukimura_runtime` 保留匯出的骨架和三組 NLA 動作，為避免展示圖重疊預設 hide_render。2D 參考在 `REFERENCE` collection，不匯出到 GLB。

## 模型與下載預算

| 角色 | 三角形 | GLB 幾何／動畫大小 | 骨架 |
|---|---:|---:|---|
| 幸村 | 9,886 | 874 KiB | 14 骨、3 動作 |
| 赤備足輕 | 3,010 | 208 KiB | 無，幾何實例 |
| 德川足輕 | 2,866 | 188 KiB | 無，幾何實例 |
| 家康・修羅之影 | 8,520 | 494 KiB | 無，幾何實例 |

每個角色一個 primitive／一個 PBR 材質。三張共用貼圖合計約 1.59 MiB：1024² pigment、512² normal、512² roughness/metalness。四個 GLB 加上共用貼圖合計約 **3.32 MiB**。所有 GLB 引用相同的內容雜湊 URL，瀏覽器可共用資源。

**GLB 現在有外部貼圖依賴**：部署或搬移資產時必須一起保留 `public/models/shared/`，不能只搬四個 GLB。貼圖沒有遠端 CDN 依賴，也沒有前端憑證。

只有幸村使用可變形骨架；敵兵和隊友沿用共用幾何實例，避免每兵增加骨架計算。幸村直接使用載入的 skinned mesh，因此動畫綁定的是畫面上的角色。移動切換 run、攻擊觸發 slash、靜止 idle；暫停停止動作時間。接地陰影另有繪製成本。

## 本次造型與材質

- 五層弧形兜護頸、面甲、分叉鹿角和兜前六文錢。
- 長草摺的甲片紋理、肩甲包邊、曲面脛甲、手指與前臂鐵片。
- 編繩腰帶、帶褶袴褲、分格皺褶破披風及背部六文錢。
- 十文字槍由橫桿改為左右有刃形狀。
- 筆觸色差、刮傷、磨邊、繫繩與織物細節；近距離縫隙遮蔭寫入頂點色。

這些仍是程序造型和程序貼圖，不能稱為依設定圖完成的精雕或手繪資產。造型和藝術處理是目前主要瓶頸；Modal 算力不會自行修正人體、布褶、面甲或筆觸。後續應先完成幸村的高精度造型，再製作遊戲網格、烘焙細節、建立 LOD，最後決定手機預算。不要先以最低面數限制主角品質。

## 如何看實際結果

- `docs/art/models-lineup.png`：Blender Cycles 組装預覽。
- `docs/art/hero-runtime-front.png`、`hero-runtime-back.png`、`hero-runtime-slash.png`：實際 GLB 在 Babylon.js 的近景與動作。
- `docs/screenshots/battle.png`、`mobile.png`：遊戲畫面。
- `tools/model-preview.html`：Vite 開發服務中的模型檢視工具，支援旋轉、縮放、三組動作；不列入正式遊戲 UI 或 production bundle。

目前僅通過 Chromium 軟體 WebGL 的功能測試和手機尺寸／觸控模擬。這不等於實體手機效能測試；尚無真機 FPS 或熱降頻資料，也沒有全軍骨架動畫、布料物理、LOD 或完整高模到低模烘焙流程。

可選 Modal 腳本已同步攜帶 helper modules 與回收共用貼圖，但本次未執行遠端流程。它使用帳戶 CPU 資源；結果成功回傳後才寫入本機資產。
