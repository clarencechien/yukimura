# GitHub Pages 部署

## 2D《燼關突圍》

入口：<https://clarencechien.github.io/yukimura/jigoku/>。同一份 Pages artifact 同時包含根目錄的 3D v22 與 `jigoku/` 的 2D 遊戲。

工作流程固定取用 2D 分支已驗證提交 `44d6f935102fc9361146504a06467841fd25a663`，執行 10 項規則測試、單檔建置及桌機／手機瀏覽器檢查，再把單檔 HTML、Phaser 授權、下載 ZIP 與 `version.txt` 加入 `dist/jigoku/`。引擎及 32 份素材內嵌，不依賴 GitHub 原始檔網址。

後續 2D 發版需在 `.github/workflows/pages.yml` 更新這個固定提交，再由 main 的工作流程發佈；單純推送美術分支不會修改線上版。

[公開遊戲 v22](https://clarencechien.github.io/yukimura/?v=22) 已部署。Repository 的 Pages Source **已設為 GitHub Actions**，不需再次設定。

## 最新驗證基線

2026-10-14，程式／資產提交 `1ecbcc5c6be707a814a8777558f2e47bf3b064bc`，[Actions run 38523594856](https://github.com/clarencechien/yukimura/actions/runs/38523594856) 成功。兩位主將已採用 v22 候選 GLB，家康動畫 palette 已重烘焙。

本機及 CI 共 45 項測試通過；公開站抽查 HTML、JS／CSS、兩位主將 GLB、動畫 palette、manifest 及 review 狀態等 15 個檔案，HTTP 200 且 SHA-256 與建置一致。此為該遊戲提交的驗證，文件整理不重跑部署。首次部署為 2026-10-12 的 `ba87470`／run `38198847112`，不是目前版本。

## 自動部署

`.github/workflows/pages.yml` 在一般 `main` push 或手動 `workflow_dispatch` 時：

1. 使用 Node 22，執行 `npm ci`。
2. 執行 `npm test`（目前 28 項資產／規則測試）。
3. 安裝 Chromium，依序執行 `npm run test:e2e`（10 項）及 `npm run test:pages`（7 項）。
4. 上傳 `dist`，透過 GitHub 官方 Pages Actions 部署。

文件專用提交若包含 `[skip ci]`，會略過 push workflow，網站維持前一次成功部署。Git push 成功不等於部署成功；判定部署需同時確認 Actions 與公開站回應。

## 本機重現

```sh
npm ci
npm test
npm run test:e2e
npm run test:pages
```

兩套瀏覽器測試都改寫 `dist`，不可同時執行。一般開發用 `npm run dev`；一般建置 `npm run build` 使用根路徑，Pages 用 `npm run build:pages` 指定 `/yukimura/`。GLB 使用 `import.meta.env.BASE_URL`，HTML 背景使用 `%BASE_URL%`。

## 部署內容

Vite 的 `dist` 包含遊戲及 `public/` 內的 review 比較頁與媒體；不包含 Blender 源檔、`docs/` 研究文件或環境憑證。不能只部署單一 `index.html` 或 GLB。

模型共有四個 GLB、14 張共用 PNG、兩份共用 binary palette，以及模型／群體動畫 manifest、握姿設定及授權文件。必須保留 `models/shared/`、`models/crowd-animation.json`、`models/weapon-grips.json`，以及環境材質等完整建置輸出。

模型與群體動畫使用 `rev=commander-22`。修改模型後須同步重烘焙 palette；測試會比對 palette 的 `source_sha256`，防止新模型搭配舊動畫資料。[完整資產預算](MODELS.md)・[驗證紀錄](VALIDATION.md)。
