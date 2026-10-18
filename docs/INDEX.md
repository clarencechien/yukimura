# 文件索引

2026-10-17 更新。2D 分支已提供完整關卡，線上 3D 遊戲維持 v22；先讀 [狀態與交接](STATUS.md)。歷史文件保留當時的數據、比較圖、來源與限制，不應混作目前規格。一般啟動見 [README](../README.md)。

## 目前狀態、操作與部署

- [2D 燼關突圍：下載、操作、三段關卡與驗證](routes/jigoku-2d/PLAYABLE_LEVEL.md)

- [v22 狀態與交接](STATUS.md)
- [開發計畫與暫停點](PLAN.md)
- [GitHub Pages 部署](DEPLOYMENT.md)
- [驗證紀錄](VALIDATION.md)
- [槍路與破陣：戰鬥手感改版](COMBAT.md)
- [共用武士模型套件：v22](MODELS.md)
- [v22：掌面、手肘與指節握姿製作及遊戲採用](WRIST_STUDY_V22.md)

## 世界觀與美術方向

- [歷史與架空界線](HISTORY.md)
- [真田・赤冬：修羅迴戰](NARRATIVE.md)
- [赤冬美術規格](ART.md)
- [插畫風格：先定 2D，再建模](ILLUSTRATION_DIRECTION.md)
- [幸村精修：造型與遊戲驗證](HERO_REFINEMENT.md)

## 製作演進與比較紀錄

- [幸村高模與遊戲烘焙](HIGH_POLY.md)
- [家康、倒地與風雪戰鬥 v9](STORM_AND_COMMANDERS.md)
- [髒雪、建物與障礙物材質](ENVIRONMENT.md)
- [開源手部與籠手試作](OPEN_HAND_STUDY.md)
- [開源籠手：遊戲素材最佳化](OPEN_HAND_GAME_OPTIMIZATION.md)
- [幸村與家康：連續手部及握持修正](COMMANDER_MODEL_REFINEMENT.md)
- [v14・全身骨架與連續腕部](FULLBODY_RIG.md)
- [武將體格修正 v15](COMMANDER_PHYSIQUE.md)
- [v16：共用甲冑細節與雙倍腕部](SHARED_ARMOR_DETAILS.md)
- [v17：真人頭臉接入兩位主將](HUMAN_COMMANDER_HEADS.md)
- [v19：照片參考面頬與貼合頭盔](COMMANDER_VISOR.md)
- [v18：真人頭部加上武士面頰](COMMANDER_MENPO.md)
- [v20：重建面頬的立體造型](COMMANDER_MENPO_V20.md)
- [v21：面具與握持試作（歷史比較紀錄）](COMMANDER_TRIAL_V21.md)

## 研究與離線渲染

- [寫實人物與甲冑資源試載](CHARACTER_ASSET_RESEARCH.md)
- [手部與鎧甲精修：skill 與替代方法調查](HAND_ARMOR_METHODS.md)
- [手腕／雙手握武器：v21 問題與下一步](WRIST_RIG_REVIEW.md)
- [第一人稱影片試幀](CINEMATIC_TEST.md)
- [第一人稱試幀：模型與材質精修](CINEMATIC_REFINEMENT.md)

## 授權與來源

- [模型來源說明](../public/models/NOTICE.md)
- [MPFB／MakeHuman 素材授權](../assets/vendor/mpfb/LICENSE.ASSETS.md)
- [MPFB 程式授權](../assets/vendor/mpfb/LICENSE.md)
- [Rocketbox MIT 授權](../public/models/LICENSE-Rocketbox.txt)

上游授權文件原文保留；文件整理不修改第三方授權。

## 並行路線（2026-10-15）

- [真田・六文劫：預渲染 2D 研究、文案與三張參考圖](routes/jigoku-2d/README.md)（獨立分支，未替換 v22）。

- [六文劫：Blender 三幀試渲與 512／1024 比較](routes/jigoku-2d/BLENDER_STUDY.md)（實際 CPU 渲染，造型尚未達概念圖目標）。

- [路線修正：保留插畫的 2.5D 重打光](routes/jigoku-2d/ILLUSTRATION_RELIGHT.md)（目前優先方向；工具已查文件，尚未推論）。

- [插畫 2.5D 補光：中性／暖光／冷光實際結果](routes/jigoku-2d/RELIGHT_STUDY.md)（同一插畫，Blender 光照差異合成）。

- [赤槍初動：插畫持槍待機、短刺與補光圖集](routes/jigoku-2d/YARI_MOTION.md)（30 fps／36 幀，兩動作、三光照、手機／桌機解析度，未接入正式遊戲）。

- [短刺修正：固定肢段與肩肘腕連動](routes/jigoku-2d/YARI_RIGID_MOTION.md)（取代整圖拉伸，30 fps 前後對照，未接入正式遊戲）。

另有 [未來赤備：TRELLIS 兩代實測比較](experiments/future-sanada/README.md)：第一代＋DINOv2 與第二代＋DINOv3 均已生成、下載與五視角渲染；附 GLB、Blender 場景及互動檢視器。最新為[頭部逐項精修與身體試接](experiments/future-sanada/head-study/README.md)，包含原網格檢查、Rocketbox 人臉眼眶／薄浮雕六文錢／面罩上緣修整與近拍。仍需手部／甲片精修與骨架，未替換線上遊戲。
