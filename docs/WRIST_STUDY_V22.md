# v22：掌面、手肘與指節的握姿試作

頁面：`review/wrists/`。2026-10-14 使用者確認採用後，v22 已安裝至正式遊戲：兩位主將沿用 v21 面具，使用 v22 持武器／突刺動畫；其他招式保持既有動作。家康的 GPU 群體動畫表已重烘焙，瀏覽器資產版本更新為 `commander-22`。

## 變更

- 幸村的持槍與突刺、家康的持刀與突刺，共四段既有動畫。其餘動作保留。
- 武器握點同時指定方向、掌面繞軸姿態與肘部 pole。使用固定的作者設定，取消這四段動作的腕折角度搜尋。肩／肘／腕不能到達目標時直接報錯，不拉長手臂。
- 幸村後手靠近身體中線，雙手保持 32 cm 間距；持槍改為朝前的準備姿勢。家康雙手保持 15 cm 間距，右手靠刀鍔、左手靠柄尾，握點前移並提高。
- 五指各有 FK 修正。拇指根部增加對握方向；食指末節收攏，其餘指節用較小修正維持握柄接觸。槍／刀的掌面與上肢姿勢分開設定，兩種握柄名義半徑同為 19.8 mm，因此共用這次校準的指節修正。
- 子指節跟隨父指節的剛體旋轉，沒有平移拉長指骨。沿用兩段前臂的扭轉分配、92 根骨骼、材質及貼圖；控制在 Blender 離線完成。

## 作者工作流程

本次借鑑 Rigify 的明確肘部方向、手部獨立控制與逐指 FK 做法，**沒有安裝 Rigify，也沒有把既有骨架換成 Rigify**。共用 MPFB 的變形骨架，採用 `wrist_study.py` 的兩骨解析 IK，再烘焙到現有骨骼。

`assets/source/weapon-grips.json` 是握姿來源：`center`、`axis`、`spacing`、左右 `radial`（掌面繞握柄方向）、`pole`（肘部彎曲平面）、`fingers`（三節附加旋轉）及 `thumb_opposition`。坐標為 Blender 模型／胸部局部坐標，前方 -Y、上方 Z；長度公尺、手指角度為度。不能把 pole 坐標當實際手肘位置，也不能把附加指節角度當人體絕對關節角度。

可編輯場景：`assets/optimized/commanders/{yukimura,ieyasu}-grip-study.blend`。內含原有完整骨架、可編輯動畫曲線及 `Weapon grip controls.json` 文字區塊。改姿勢來源 JSON 後重新執行 builder；修改文字區塊不會自動驅動模型。

```bash
npm run models:wrists
GRIP_POSE_CONFIG=assets/source/weapon-grips.json \
  GRIP_REPORT_DIR=.tmp/wrist-v22/grip-check \
  MODEL_TEST_ROOT=../.tmp/wrist-v22/models/ \
  node --test tests/commander-grip.test.mjs
blender --background --threads 2 --python-exit-code 1 --python tools/validate_wrist_study.py
# 開啟既有 Vite 開發伺服器 5180 後：
node tools/capture-wrist-study.mjs
python3 tools/wrist_gallery.py
```

Builder 固定從 v21 `*-trial.blend` 讀入，不累加修改，不改寫 `public/models`。匯出 GLB 在 `.tmp/wrist-v22/models`，畫面由 Babylon 實際載入該 GLB 擷取。沒有使用生成圖假裝建模結果。

## 驗證與範圍

- 既有 GLB 握點／軸向測試：兩位共 2,352 個非倒地手部取樣；v22 使用來源 JSON 中的握距，其餘動作仍用既有握距。動畫時長與循環回位一併檢查。
- 新增變形後手指表面檢查：四段動畫各 11 個時間點，兩手、每手五指。比較原版 Blender、試作 Blender、重新匯入的 GLB，涵蓋匯出時最多四骨權重的影響。
- 以握柄中心軸的 19.8 mm 圓柱作接觸近似，選擇該指權重超過 60% 的網格頂點。允許小於 2 mm 的表面壓入，以檢出大量穿柄，不能視為精確碰撞。
- 裸手視圖只顯示原有手臂／手部網格，改成單色方便辨識。肩部的開口是原模型藏在鎧甲內的裁切，不是新製完整裸體模型。
- 影片以 30 fps 取樣同一段 1 秒突刺，循環播放；不是動作捕捉，也不宣稱特定流派的標準槍術／劍術。
- 不以最小腕折角度作成功指標。仍需視覺確認前臂扭轉、護腕遮擋和整體動作；本輪沒有完整人體關節限制、逐三角形碰撞、槍上纏繩碰撞、滑握或所有招式間的過渡修正。

完整數據及檔案 SHA256 見試作頁的 `validation.json`、`capture.json`。Rigify／Godot 的開源參考與原始問題診斷見 [WRIST_RIG_REVIEW.md](WRIST_RIG_REVIEW.md)。

## 安裝到遊戲

`npm run models:install-wrists` 先重跑 GLB 握持與手指驗證，再由 `promote_wrists.py` 核對模型雜湊、骨架／材質數及共用貼圖，安裝兩位主將並重烘焙家康的群體動畫。`public/models/weapon-grips.json` 記錄正式握距，模型測試依此檢查。完整 `npm run models` 的最後階段也使用此安裝流程，避免重建後回到 v20。

本次安裝的 GLB 與 v22 比較頁所驗證的檔案相同，沒有在採用時另改造型或姿勢。幸村的動作切換沿用既有混合；家康沿用 GPU 動畫取樣，未新增跨招式混合。
