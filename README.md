# 真田・赤冬：修羅迴戰

**六文已備，此戰未終。**

手機與 laptop 的斜俯視 3D 戰鬥原型。以大坂冬之陣的藝術化場景，演繹幸村與傳說中的十勇士自修羅戰境重返大坂的架空故事。

## 並行美術路線

本分支新增 [《真田・六文劫》預渲染 2D 研究與參考圖](docs/routes/jigoku-2d/README.md)：Blender → 透明動畫貼圖 → 2D 引擎的另一條路線。已有文案、概念圖、[Blender 補光對照](docs/routes/jigoku-2d/RELIGHT_STUDY.md)，以及 [持槍待機／短刺動畫](docs/routes/jigoku-2d/YARI_MOTION.md)。最新為 [Phaser 燼關試槍：肩甲先轉落與胸肩接續](docs/routes/jigoku-2d/COMBAT_STUDY.md)，沿用 [固定肢段、骨盆先行與雙腿連動](docs/routes/jigoku-2d/YARI_RIGID_MOTION.md)，舊模型三幀另留作歷史比較；下列 v22 仍是既有遊戲基線。

## 目前版本

2026-10-14 依使用者指示暫停開發，保留已上線的 **v22**。幸村與家康已採用 v21 面具及 v22 握姿，並接入遊戲；不是只有比較頁更新。程式基線為 `1ecbcc5`。

- [遊戲](https://clarencechien.github.io/yukimura/?v=22)
- [手腕、握姿與動作對照](https://clarencechien.github.io/yukimura/review/wrists/?v=22)
- [目前狀態與交接](docs/STATUS.md)・[完整文件索引](docs/INDEX.md)

## 啟動與驗證

Node.js 22.12+；此環境已驗證 Node 24.19.0。前端不需要 Blender 或 Modal 憑證。

```sh
cd /workspace/yukimura
npm ci
npm run dev
```

`npm run build` 建置；`npm run preview` 檢查建置結果。依賴由 npm 安裝，執行時模型、貼圖及概念圖由網站本身提供。

```sh
npm test           # 規則、模型與動畫資料：28 項
npm run test:e2e   # 桌面、手機尺寸、通關與敗北：10 項
npm run test:pages # /yukimura/ 子路徑與資產：7 項
```

v22 基線本機與 CI 共 45 項通過，詳見 [驗證紀錄](docs/VALIDATION.md)。兩套瀏覽器測試會重建同一個 `dist`，請依序執行。Playwright 使用 `/usr/bin/chromium`，可設定 `CHROMIUM_PATH`，或以 `npx playwright install chromium` 安裝。E2E 使用 5175／4173 埠，Pages 測試使用 4174 埠。手機尺寸／觸控模擬不等於真機效能驗證。

## 操作與目標

- WASD／方向鍵移動，按住 J 四連段槍擊，空白鍵衝刺，K 六文赤蓮（蓄滿無雙）。
- F 切換十勇士結誓／破軍陣，P／Esc 暫停；右上角可切換音效。
- 手機左側搖桿、右側戰技按鈕，支援直向與橫向。
- 突破三段戰場、擊敗家康；擊破累積無雙，連擊每八次恢復少量體力。
- 戰前選擇初陣／猛將／修羅難度。通關解鎖下一周目，localStorage 保存進度，上限二十周目。

## 引擎與模型

使用 **Babylon.js 8 + TypeScript + Vite 7**。引擎處理 WebGL、相機、GLB、PBR 材質及 GPU 實例動畫；戰鬥規則由專案實作。

主選單只使用概念圖左側戰場；右側設定集不放入遊戲 UI。兩位主將使用 92 骨架及約 8.5–8.7 萬三角形，足輕約 3,500–3,700 三角形、18 骨架，共用零件、貼圖與動畫資料。地面和建物已有髒雪、泥水、風化木石材質及光影；模型仍未達到設定插畫品質。

[模型套件與重建](docs/MODELS.md)・[v22 握姿流程](docs/WRIST_STUDY_V22.md)・[戰鬥動作](docs/COMBAT.md)・[環境材質](docs/ENVIRONMENT.md)

模型製作與本輪離線驗證使用本機 Blender CPU；遊戲使用瀏覽器 GPU 渲染。沒有成功執行 Modal 遠端建模。`tools/modal_models.py` 是早期 CPU 建模實驗，未串接完整 v22 管線，不能用來重建目前主將。過去 Modal 連線曾回覆 CONNECT 403，本次文件整理未重試。憑證不可放進 `VITE_*`、前端、Git 或文件。

## 部署與範圍

GitHub Pages Source 已設為 GitHub Actions；一般 `main` push 會測試並部署，詳見 [部署說明](docs/DEPLOYMENT.md)。文件專用的 `[skip ci]` 提交不會更新部署。

已具備十名隨行角色、四向敵軍、獨立動畫相位、連擊、擊退、衝刺、無雙、陣形、家康戰、勝敗與周目，以及 WebAudio 合成音效。尚未完成十勇士獨立造型／忍術、完整角色 LOD、配樂／配音、更多關卡、真機效能量測、全部招式的手腕與衣甲碰撞修正。

冬之陣場景取自 1614 年背景，衝向家康的事件來自 1615 年夏之陣並經架空改編；十勇士屬傳說，修羅輪迴為創作，不能當作宗教或史實結論。史料核對狀態見 [歷史界線](docs/HISTORY.md)，文案見 [世界觀](docs/NARRATIVE.md)。
