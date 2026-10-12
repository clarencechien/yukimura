# GitHub Pages 部署

公開遊戲：[真田・赤冬](https://clarencechien.github.io/yukimura/)。

2026-10-12 已啟用 GitHub Actions Source，首次部署成功。部署版本 `ba87470`，Actions run `38198847112`；公開站 HTTP 200，105 個檔案經 HTTPS 下載及 SHA-256 比對，與通過瀏覽器測試的建置相同。

## 自動部署

`.github/workflows/pages.yml` 在 `main` push 或手動 workflow_dispatch 時：

1. Node 22、`npm ci`。
2. 資產／規則測試。
3. 安裝 Chromium，先執行 `npm run test:e2e` 完整桌面／手機／戰鬥驗證，再執行 `npm run test:pages`：以 `/yukimura/` 建置並透過瀏覽器實際載入背景、四個 GLB、九張貼圖（幸村與家康各三張、足輕共用三張）、群兵動畫 JSON／足輕與家康兩份 binary palette 和開始戰鬥。
4. 上傳 `dist`，透過 GitHub 官方 Pages Actions 部署。

**第一次需在 repo Settings → Pages → Build and deployment → Source 選 GitHub Actions。** 有可用的 repository 管理 API 時可自動設定；若 API 被雲端網路阻擋，repository 管理者需在 GitHub 完成這個一次性設定，然後重新執行 workflow。若 repository 為 private，還須符合帳戶方案對 Pages 的支援；部署不會自動修改 repository 可見性。

部署是否成功以 Actions 的 `deploy` job 和公開網址實際回應為準，不以 Git push 成功代替。啟用後，每次推送 `main` 自動更新。

## 本機重現

```sh
npm test
npm run test:pages
```

普通開發使用 `npm run dev`；`npm run build` 仍採網站根路徑。Pages 使用 `npm run build:pages` 指定 Vite base；Babylon GLB 路徑使用 `import.meta.env.BASE_URL`，HTML 背景使用 `%BASE_URL%`。

部署輸出只包含遊戲需要的 `dist`，不會上傳 Blender 源檔、美術設定文件或環境憑證。GLB 依賴 `models/shared/` 中的貼圖；群兵動畫另依賴 `models/crowd-animation.json` 及 shared 中的 `.bin`。部署時需完整保留 models 目錄，以及 environment 目錄中的地面／木石／屋瓦材質。
