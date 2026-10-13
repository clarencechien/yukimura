# v14・全身骨架與連續腕部

這版更換幸村與家康的變形結構，改善 v13 將固定手型接到簡化前臂的接縫與僵硬轉腕。不是重新雕塑整套插畫級人物。

## 可檢查成果

- `renders/fullbody-v14/index.html`：調整前後、突刺與完整人物截圖，附四張原始人體變形圖；PNG 全部內嵌，無相對圖片連結問題。
- `assets/optimized/commanders/mpfb-fullbody.blend`：完整 CC0 人體、163 骨及中立／屈肘／前臂旋轉／轉腕測試，保留完整網格。
- `assets/optimized/commanders/yukimura-fullbody.blend`、`ieyasu-fullbody.blend`：可編輯遊戲角色，貼圖已封裝。
- `public/models/yukimura.glb`、`ieyasu.glb`：遊戲實際使用的匯出模型。

## 結構與動作

作者版使用 MPFB 原始 163 骨。遊戲版移除不使用的臉部與腳趾等骨骼，保留 74 根來源變形骨與 18 根現有武器、披風及動作控制骨，共 92 骨。胸甲、頭盔和腿甲仍採分片剛性綁定；手臂保留同一份人體網格，肩部切口藏於胸甲內，手腕沒有切斷或用球體拼接。

來源關節位置由相同版本 OBJ 的 helper 頂點重建，未使用不同體型的 JSON 範例座標。蒙皮保留並正規化最主要四個影響；細分／減面後，glTF 匯出再次裁切至四個影響。檢查採用與 Babylon.js 一致的線性蒙皮，不以 Blender 專用雙四元數效果代替遊戲結果。

前臂分成兩段承接轉腕。雙手仍鎖定武器握點，但允許繞槍桿調整方向；求解器同時選擇手肘方向，並持續追蹤同一個姿勢解，避免出招中途突然翻轉。衝刺改成朝前持槍，減少腕部反折。家康倒地時逐節鬆開手指，保留父子關係與指節長度。

材質分成原有盔甲圖集、皮革內襯與貼合護腕三個部分。家康的 GPU 動畫現在同步驅動全部三個 mesh，避免只出現盔甲、漏掉新手臂。兩種足輕仍使用 18 骨及原有 GLB。

| 角色 | 三角形 | 骨骼 | 材質部分 |
|---|---:|---:|---:|
| 幸村 | 63,193 | 92 | 3 |
| 家康 | 60,343 | 92 | 3 |

沿用原有九張共用 PNG，沒有重新進行整套高模材質烘焙，也未呼叫 Modal 或付費服務。兩位武將增加蒙皮與材質成本，並未將高骨數配置套用到全軍。實際 GLB 與動畫 palette 大小以 manifest 為準。

## 重建

環境沿用 Blender 4.3 與既有 Node 依賴，無新增外部套件。

```sh
# 從現有 samurai-kit.blend 重建輸入，轉接並安裝兩位武將；不重烘材質。
npm run models:rigs
node tools/bake-crowd.mjs
npm test
npm run test:e2e
npm run test:pages

# 完整模型／動畫重建流程也已接入 v14 轉接步驟。
npm run models
```

`tools/prepare_commander_base.py` 以作者檔 SHA-256 管理 `.tmp` 中的輸入快取。乾淨 checkout 可以直接從作者檔產生輸入，不需要留下本機快取。`tools/upgrade_commander_rigs.py` 先輸出到 `.tmp/fullbody-v14/models/`，`tools/promote_fullbody.py` 再更新遊戲 GLB 與 manifest。新的 `.blend` 保存在 `assets/optimized/commanders/`，原本完整高模套件仍在 `assets/source/`。

## 驗證範圍

- 匯出檔的雙手握點、武器軸、動作時間及循環起迄姿勢。
- 前臂軸與掌部長軸夾角小於 50°；這是反折回歸指標，不是精確的解剖學關節角量測。
- 左右腕部都存在跨前臂／腕骨的混合權重，30 根手指骨都有實際頂點權重；倒地時指節確實活動。
- 92 骨家康的 GPU palette 與實際載入的骨架矩陣一致，三個材質部分使用相同動畫影格。
- 桌面／直式手機版遊戲流程及 GitHub Pages 子路徑載入。

尚未完成：角色體型的手工雕塑、近距離皮革皺褶／皮膚細節、全姿勢甲片碰撞修正與真機效能量測。數值握點驗證不等於每根手指表面都無穿插。這版已能放入遊戲，但不是插畫精細度的最終美術驗收。

來源與授權沿用 `assets/vendor/mpfb/provenance.json`：MakeHuman Community MPFB，commit `d0a32e57a7f915cb2f2b95410e2117648c7bbb7e`，人體、骨架與權重 CC0-1.0；未把 GPL 外掛程式碼放入遊戲。

## 本次執行結果

26 項單元測試通過。完整瀏覽器測試先通過 9 項，新增的 Boss 分材質同步測試暴露預覽 fixture 重複產生家康；修正 fixture 的 `bossSpawned` 狀態後，該項重測通過，共 10 個測試案例通過。比較頁在 1280px 與 390px、停用 JavaScript 下，14 張內嵌圖片均成功解碼且無水平溢出。詳細數據與 GLB SHA-256 見 `renders/fullbody-v14/validation.json`。

直接對最終 GLB 的腕部變形骨取樣：幸村最大握點誤差 0.485 mm、掌臂軸夾角 34.87°；家康 0.543 mm、45.26°。兩者合計 2,352 個握持取樣點，另檢查前臂循環端點與混合權重。

GitHub Pages 子路徑測試 1 項通過：背景、四種模型、共用貼圖及開始戰鬥正常載入。本次未推送 GitHub，也未觸發部署。
