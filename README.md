# 真田・赤冬：修羅迴戰

**六文已備，此戰未終。**

手機與 laptop 的斜俯視 3D 戰鬥原型。以大坂冬之陣的藝術化場景，演繹幸村與傳說中的十勇士自修羅戰境重返大坂的架空故事。

## 啟動

Node.js 22.12+（此環境已驗證 24.19.0）。

```sh
cd /workspace/yukimura
npm ci
npm run dev
```

正式建置：`npm run build`；本機檢查建置結果：`npm run preview`。
依賴、模型與概念圖均隨專案本機載入，前端不需要 Modal 憑證。

## GitHub Pages

遊戲已上線：[真田・赤冬](https://clarencechien.github.io/yukimura/)。`main` 的 push 會觸發部署 workflow；此 repository 已設定 Pages Source 為 GitHub Actions。

部署與子路徑測試見 [部署說明](docs/DEPLOYMENT.md)。v9 加入沿用主角甲冑的黑金家康、兩種分段倒地、風雪粒子與赤蓮技能特效；保留幸村高模烘焙、全軍骨架動畫與雙手握槍；實際近景及仍待完成的手工雕修／手機最佳化見 [幸村精修規格](docs/HERO_REFINEMENT.md)。

實際引擎錄影：[幸村八組動作](docs/art/hero-motion.webm)・[隊友與敵軍實戰](docs/art/army-motion.webm)。

## 操作與目標

- WASD／方向鍵移動，按住 J 四連段槍擊，空白鍵踏雪衝刺，K 六文赤蓮（蓄滿無雙）。
- F 切換十勇士結誓／破軍陣，P／Esc 暫停。
- 手機左側搖桿，右側戰技按鈕；支援直向與橫向。
- 四連段包含橫掃、反掃、突刺與迴旋；無雙分段爆發，敵兵會擊退／擊飛／倒地。右上角可切換音效。
- 向前突破三段戰場，擊敗家康本陣的修羅之影。擊破累積無雙，連擊每八次恢復少量體力。
- 戰前選擇初陣／猛將／修羅難度。通關解鎖下一周目，localStorage 保存進度；目前上限二十周目，到上限仍可重玩。

## 引擎與美術

Babylon.js 處理 WebGL 場景、相機、GLB、材質與實例化。TypeScript + Vite 處理應用與建置，遊戲規則自訂。場景使用髒雪／泥水／風化木石的 PBR 材質；靜態物件依材質合併並投影、士兵模型實例化，軟體繪圖環境自動降低內部解析度。

`public/art/concept.png` 是原創 2D 方向板；主選單只顯示其左側戰場裁切，右側設定集不進入遊戲 UI。`public/models/*.glb` 是本機 Blender 匯出的四個遊戲資產，須一併部署 `public/models/shared/`。幸村使用專用 2K 高模烘焙貼圖與單一骨架模型，大量足輕保留約三千面的實例；可重用零件、編輯流程與實際下載預算見 [模型套件](docs/MODELS.md)。

```sh
npm run models # 需要 Blender；此環境使用 4.3.2
```

Blender 未提供 Draco 函式庫時會提示，但本專案輸出不使用 Draco，普通 GLB 已通過實際載入測試。

可選的 Modal 遠端流程：

```sh
python -m venv /workspace/yukimura-tools
/workspace/yukimura-tools/bin/pip install -r tools/requirements.txt
/workspace/yukimura-tools/bin/modal run tools/modal_models.py
```

SDK 支援從安全環境中的 `modal_token_id` / `modal_token_secret` 對應至 `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`。不將它們放進任何 `VITE_*` 變數、前端檔案、Git 或聊天。此流程呼叫 Modal CPU 工作來執行 Blender，會使用 Modal 帳戶資源。遠端程式收到成功結果才會覆寫本機 GLB，再以本機 Node.js／Babylon.js 烘焙共用群兵動畫資料；請先執行 npm ci。

目前：憑證變數已注入，但 Modal 連線失敗；代理對 `api.modal.com` 回覆 CONNECT 403。**模型已由本機 Blender 生成，未宣稱由 Modal 成功生成。**

## 驗證

```sh
npm test        # 戰鬥與周目規則
npm run test:e2e # 建置 + 桌面／手機／通關／敗北回歸
```

Playwright 預設使用 `/usr/bin/chromium`；其他機器可設定 `CHROMIUM_PATH`，或執行 `npx playwright install chromium` 安裝瀏覽器。測試啟動 5175 開發服務與 4173 預覽服務。
完整戰鬥測試使用僅存在於 Vite 開發模式的固定時間步進，仍透過實際鍵盤事件與完整遊戲規則完成通關；正式建置不含此控制介面。

## 文件

- [家康、倒地與風雪特效](docs/STORM_AND_COMMANDERS.md)
- [戰鬥操作與手感](docs/COMBAT.md)
- [開發計畫](docs/PLAN.md)
- [完整世界觀與文案](docs/NARRATIVE.md)
- [歷史與架空界線](docs/HISTORY.md)
- [美術規格](docs/ART.md)
- [共用模型與成本](docs/MODELS.md)
- [幸村高模與烘焙流程](docs/HIGH_POLY.md)
- [髒雪、建物與障礙物材質](docs/ENVIRONMENT.md)
- [插畫風格與 2D→3D 流程](docs/ILLUSTRATION_DIRECTION.md)
- [驗證紀錄與限制](docs/VALIDATION.md)

## 原型範圍

已做：具八組骨架動作及動作銜接的幸村、各自跑動／刺擊的十名隨行角色、具跑動／攻擊／受擊／倒地動畫的敵軍、四向生成敵軍、攻擊與擊退、衝刺、無雙、陣形、連擊、家康戰、勝敗、周目、手機觸控與敘事。
尚未做：十勇士各自的模型／忍術、角色 LOD、配樂與角色配音、更多關卡、實體手機效能基準。場景是低多邊形原型，不能把概念圖當作實機畫質承諾。
史料來源仍受網路政策限制，背景文件標示為待核對；十勇士為傳說角色，修羅輪迴為創作設定。
