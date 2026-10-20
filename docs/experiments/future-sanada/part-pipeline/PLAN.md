# 未來赤備：拆件生成＋既有骨架組裝（計劃）

分支 `future-sanada-part-pipeline`。body v2（pass 1–9）證明：整身一次生成再後修，近看品質到頂，也無法乾淨綁骨。本計劃改為**先產生乾淨的多視圖與單件圖，逐件生成 3D，再組到遊戲現有的骨架上**，產出可在 Babylon.js 遊戲與 Blender 影片中使用的可動角色，並搭配場景。

## 限制與前提

- **排除中國來源的工具與模型**：Hunyuan3D 系列、Tripo／TripoSG／UniRig（VAST）、ByteDance（Seedream、Puppeteer、MagicArticulate）、Qwen、OmniPart／SAMPart3D、PartCrafter、Pixal3D，以及會拉進上述模型的 ComfyUI 工作流程。
- **只用開源／可自架**的 3D 生成（方案 A），跑在既有的 Modal H100。
- **圖像生成**用 OpenRouter（`or_key`）上的西方模型。**額度上限 10 美元，目前剩約 7.9 美元**：每一張都要有目的，先小量 A/B 再決定。
- **遊戲規格**（現行測試）：武將 ≤ 90,000 三角面、< 7 MB、恰好 92 個關節（18 個控制骨＋74 個 MPFB `body.*` 變形骨）、8 個動作（`idle run slash reverse thrust spin dash hurt`），見 `tests/models.test.mjs`、`tests/fullbody-rig.test.mjs`、`tests/commander-grip.test.mjs`。
- **影片規格**：另出高精度版（LOD0），貼圖 2–4K、面數不設遊戲上限，Cycles 算圖。

## 調查結論（2026-10-19）

| 階段 | 採用 | 來源／授權 | 備註 |
| --- | --- | --- | --- |
| 多視圖、單件圖 | `openai/gpt-image-2.5-flare`（主）、`google/gemini-3-pro-image`（備） | OpenAI／Google；輸出歸使用者 | 兩者都沒有正交三視圖的公開評測，**先 A/B**（第 0 階段） |
| 圖轉 3D | TRELLIS.2，**一件一張圖** | Microsoft，MIT；DINOv3 編碼器為 Meta 授權（待核對條款） | 官方推論只吃單張圖；多視圖只在訓練程式碼，社群節點未驗證，不採用 |
| 拆件生成 | 不用模型，改為**逐件生成** | — | PartTrellis 權重未釋出、授權不明；PartField／PartPacker 為 NVIDIA 非商用 |
| 重拓撲 | Blender 內建 QuadriFlow，或 Instant Meshes | BSD 類 | 之後在 Blender 從高模烘焙法線、顏色 |
| 規則甲片 | 沿用 pass 8–9 的 `lame_panels.py`（程式生成水平甲片） | 本 repo | 胴、草摺、袖這類規則排列的甲，程式生成比 AI 穩；貼圖改用新的單件圖 |
| 身體與骨架 | 既有 MPFB 92 關節武將骨架（`assets/optimized/commanders/mpfb-fullbody.blend`） | MPFB 資料 CC0 | 甲片逐片 100% 綁單一骨（與現行 `FULLBODY_RIG.md` 相同），布與軟件做權重轉移 |
| 軟件權重 | Robust Skin Weights Transfer | 方法來自 Epic 研究員；程式 MIT | 只用於繩、布、草摺吊帶 |
| 動作 | 先沿用遊戲現有 8 個手 K 動作（同一骨架，零轉換） | 本 repo | 影片需要時再加 Quaternius Universal Animation Library（CC0），自寫骨名對應重定向，不依賴需登入的外掛 |
| 場景 | Poly Haven（CC0）HDRI、材質、模型；既有程序戰場與 `assets/cinema/*.blend` | CC0／本 repo | 雪景 HDRI（如 `passendorf_snow`）、`castle_brick_*`、`modular_fort_01`、燈籠等 |
| 生成式場景（選配） | NVIDIA Lyra 1.0 → 高斯潑濺 | Apache-2.0＋NVIDIA Open Model License（可商用，待核對） | Babylon.js 8/9 可直接載入 .ply/.spz/.sog；Lyra 2.0 為研究授權，不用 |

不採用：RigNet（GPL、舊 CUDA）、Anymate（無授權檔）、Mixamo（禁止再散布原始檔，且需 Adobe 帳號）、Stability SPAR3D（年營收門檻）、Meta SAM 3D（附使用限制）。

## 階段與驗收

每個階段結束都產出對照圖給你看，**通過才進下一階段**。

### 第 0 階段：圖像模型 A/B（約 0.5 美元）
- 同一提示、同一張原圖，請 `gpt-image-2.5-flare`、`gemini-3-pro-image` 各畫一張**正面、A 姿勢、正交、純色背景**的全身設定圖（必要時加 `flux-3-image`）。
- 比較：與原圖造型一致度、左右對稱、甲片排列是否規則、手腳是否完整。選一個模型用到底。

### 第 1 階段：設定圖（約 1 美元）
- 全身三視圖：正面先畫，側面與背面以正面為參考圖再畫。A 姿勢與 MPFB 預設姿勢一致，方便套骨架。
- 這組圖是後續所有單件的造型依據，也補上原圖沒有的背面。

### 第 2 階段：單件圖（約 3 美元）
- 部件：頭盔（含鹿角前立、面頰）、胴（前、後）、袖、草摺一片、籠手（前臂甲）、手甲、佩楯（大腿甲）、膝甲、脛當、足甲。
- 左右對稱的件只畫一邊，3D 時鏡像。每件放在純色背景、3/4 視角（TRELLIS 最擅長的角度），保留厚度與邊緣。

### 第 3 階段：逐件 3D（Modal）
- 每件跑 TRELLIS.2 1536，兩個 seed 擇優。
- 規則甲片（胴、草摺、袖）兩條路並行：TRELLIS 生成，以及 `lame_panels.py` 程式甲片貼上新圖，近拍比較後擇一。
- 驗收：每件的白模與上色近拍（1000²），和 body v2 pass 9 的同部位並排。

### 第 4 階段：清理與組裝
- 每件重拓撲＋烘焙（遊戲版約 3–8k 面／件，影片版保留高模）。
- 在 MPFB 身體上依骨架位置擺放、縮放各件；甲片逐片綁到對應骨；繩與流蘇沿用 `tie_cords.py`。
- 驗收：A 姿勢全身四向、白模；抬手、彎膝、扭腰三個測試姿勢檢查穿插。

### 第 5 階段：進遊戲
- 匯出符合 92 關節、8 動作的 GLB；通過 `npm test` 的模型測試（面數、大小、骨架、握槍）；重烘 crowd palette。
- 驗收：遊戲內錄影（Playwright），對照現有幸村。

### 第 6 階段：場景與影片
- 遊戲：既有程序戰場加入 Poly Haven 材質與道具。
- 影片：Blender 場景＝Poly Haven 雪景 HDRI＋城郭道具＋既有 cinema 場景，角色用 LOD0，跑 8–10 秒短片。
- 選配：Lyra 1.0 生成背景潑濺，在 Babylon 試載。

## 風險

- **TRELLIS 單件仍可能凹凸**：對策是重拓撲＋烘焙，以及規則甲片改程式生成。
- **圖像模型不聽「正交、A 姿勢」**：第 0 階段就會看出來；必要時以身體剪影當參考圖約束。
- **預算**：每階段開始前先估算張數；額度不足時停下來問你。
- **授權待核對**：DINOv3 條款、Lyra 1.0 的 NVIDIA Open Model License；核對前不把成果放進遊戲正式版。

## 產出位置

- 計劃與各階段報告：`docs/experiments/future-sanada/part-pipeline/`
- 生成的圖：`.../part-pipeline/images/`（含提示詞與模型名稱的 `prompts.json`）
- 3D 成果與對照圖：`.../part-pipeline/stageN/`
- 工具：`tools/part_pipeline/`（圖像生成、Modal 逐件生成、組裝、匯出）
