# v21：面具與握持試作（未替換遊戲）

使用者較喜歡 v19 的外型，並提供槍術及雙手持刀照片，要求檢查手腕／手部。此版本產生獨立試作和對照圖；遊戲仍使用 v20 模型及原動作。

## 面具

以 v19 的輪廓控制點取代 v20 的大橢圓外框，保留眼部切線和收窄的下巴。減少鼻尖、鼻翼、雙頰和下巴的凸出量；唇框半徑由 4.5 mm 縮至 1.5 mm，鼻孔邊由 3 mm 縮至 1.3 mm。家康鬚股減少並降低明度。仍共用同一個生成器、骨架及貼圖。

頁面：`public/review/menpo/trial/`。左側／手機第一張為試作，右側／下一張為 v19。

## 槍術與劍術握持

照片用作姿態觀察，未收錄或作材質；不聲稱照片屬於同一流派，亦未把電影劇照直接當作標準術式。採用常見雙手刀的右手靠鍔、左手靠柄尾，以及長槍較長的雙手間距作為遊戲姿勢基準。

- 幸村：調整 `idle`、`run` 的後手高度、槍桿角度與前方空間。保持 42 cm 握點間距，突刺原有 30 cm 間距和動作不變。
- 家康：調整 `thrust`，避免蓄勢時將刀柄拉進軀幹。雙手保持在身體前方，維持 15 cm 握距。
- 手腕仍由武器軸周圍的旋轉求解，再配合手肘平面；前臂扭轉分配到兩段變形骨。使用既有 92 骨，離線烘焙，不新增即時 IK。
- 手指本輪維持既有握形，尚未新增逐招收放、滑槍和刀柄橢圓截面貼合。

| 動作 | 原版最大腕折 | 試作最大腕折 |
| --- | ---: | ---: |
| 幸村持槍 | 9.5° | 8.5° |
| 幸村奔跑 | 10.7° | 9.5° |
| 家康突刺 | 45.3° | 5.8° |

角度為骨架前臂與手掌軸的夾角；不代表人體活動範圍、醫療評估或武術評分。所有非倒地動作共 2,352 個手部取樣，試作最大握點偏差：幸村約 0.485 mm，家康約 0.112 mm。這是握點／軸線檢查，不等於逐指接觸或衣甲碰撞檢查。幸村全動作最大腕折仍為受擊約 34.9°；家康全動作最大值為奔跑約 32.6°，沒有將未修改動作的改善歸功於此次修改。

頁面：`public/review/technique/`。每個姿勢提供斜前方與側面。鏡頭使用相同角度、倍率與動作時間，目標追蹤雙手中心；原版截圖使用 v19，其手部與 v20 相同。

## 重建

```bash
npm run models:trial
/workspace/yukimura-tools/render-env/bin/python tools/validate_face_motion.py --trial
GRIP_REPORT_DIR=.tmp/menpo-v21/grip-before node --test tests/commander-grip.test.mjs
GRIP_REPORT_DIR=.tmp/menpo-v21/grip-after GRIP_MAX_WRIST_ANGLE=35 MODEL_TEST_ROOT=../.tmp/menpo-v21/models/ node --test tests/commander-grip.test.mjs
```

對照模型由 v19 commit `e26229c2b7155c8aa8e4b9a4e14b8f7b4e9c809c` 的 `public/models/{yukimura,ieyasu}.glb` 提取至 `.tmp/menpo-v21/before/`，並複製 `public/models/shared/` 至該目錄。Vite 檢視器開在 5180 埠後：

```bash
node tools/capture-faces.mjs --trial
node tools/capture-technique.mjs
python3 tools/trial_gallery.py
```

可編輯模型：`assets/optimized/commanders/*-trial.blend`；GLB 暫存於 `.tmp/menpo-v21/models/`。`models:trial` 不呼叫正式模型安裝腳本，因此不會覆寫 `public/models/`。

面具通過 14 動作／182 取樣姿勢的隨骨與殼體頂點間隙檢查。原始人體來源授權沿用 MPFB（CC0）及 Microsoft Rocketbox（MIT）的既有記錄。
