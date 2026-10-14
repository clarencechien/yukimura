# 開源籠手：遊戲素材最佳化

> 歷史／研究文件（2026-10-14 整理）：以下「目前」、測試數據與待辦指原記錄階段，不代表 v22 現況；舊版命令如需精確重現，應使用對應 Git 版本。目前採用範圍以 [狀態與交接](STATUS.md) 為準；參閱 [完整索引](INDEX.md)。

## 交付

- `renders/open-hand/index.html`：五張原始 2560 × 2048 PNG 已轉為 data URI 內嵌。先前的相對路徑在文件預覽器中無法解析，這版不依賴相鄰圖片檔。
- `renders/open-hand/game-model.html`：內嵌 Babylon.js、兩個 GLB 和所有貼圖，可旋轉、切換 LOD；不使用 CDN。文件預覽器若禁用 JavaScript，會顯示內嵌的實際模型截圖；互動操作需下載後用支援 WebGL 的瀏覽器開啟。
- `assets/optimized/open-hand/kote-lod0.glb`、`kote-lod1.glb`：遊戲引擎可讀取的模型，各自內嵌三張 1024 × 1024 貼圖。
- `assets/optimized/open-hand/kote-game.blend`：已封裝貼圖的近景模型工作檔。

## 實際減量

|項目|原始試作|近景 LOD 0|遠景 LOD 1|
|---|---:|---:|---:|
|三角面|124,240|23,990|10,795|
|幾何物件／mesh primitive|346|1|1|
|GLB 大小|未匯出|3,875,892 bytes（3.70 MiB）|3,129,640 bytes（2.98 MiB）|
|材質|多個程序材質|1|1|
|骨骼|22|22|22|

GLB 頂點因 UV 接縫和法線拆分，實際分別為 24,523 與 14,713；不能把 Blender 編輯網格頂點數當成 GPU 頂點數。三張貼圖已包含於 GLB。原始三角面數不含測試槍桿。

## 轉換方式

將第 24 幀的握槍變形和 Shrinkwrap 接觸修正固化到網格，以此姿勢作為新的骨架 bind pose。保留手部 skin weights，甲片及縫線使用原來的骨骼依附關係；GLB 使用最多四個骨骼權重。

減面後重新製作 UV atlas，烘焙 Base Color、程序凹凸的切線空間 Normal、Roughness／Metallic。ORM 貼圖的 R 固定為 1，**本次沒有烘焙 AO**。三種材質貼圖共用於兩個 LOD；法線來自減面模型的程序材質，尚非完整高模到低模的雕刻細節投射。材質合併使用標準 metallic-roughness PBR，原始赤漆 clearcoat 尚未另做遮罩。

LOD 1 使用同一 UV atlas 再減面。手機檢視預設 LOD 1；這是獨立手部素材，不能把同等預算直接套到大量小兵身上。

## 驗證

`verify_open_hand_glb.py` 解析兩個 GLB，確認單一 mesh primitive／材質、22 joints、內嵌圖片、UV／法線／切線／權重屬性；重新匯入 Blender，檢查權重正規化、有限座標，以及轉動前臂骨骼後的實際頂點變形。

`verify-open-hand-web.mjs` 使用 Chromium + 軟體 WebGL，在 1280 和 390 px 寬度驗證五張內嵌原圖、兩個 LOD、貼圖載入及頁面無水平溢出。結果在 `renders/open-hand/glb-check.json` 和 `web-check.json`。測試亦確認沒有相鄰檔案或外部 HTTP 子資源請求，且停用 JavaScript 時仍能顯示內嵌截圖。這是瀏覽器功能與版面驗證，**不是實機手機效能測試**。

## 重建

```bash
python3 tools/open_hand_review.py
/workspace/yukimura-tools/render-env/bin/python tools/optimize_open_hand.py
/workspace/yukimura-tools/render-env/bin/python tools/verify_open_hand_glb.py
python3 tools/open_hand_web_review.py
# 在另一個終端機啟動專案根目錄的 HTTP 伺服器（測試專用）
python3 -m http.server 8767 --bind 127.0.0.1
node tools/verify-open-hand-web.mjs
```

沿用現有 bpy、Babylon.js、esbuild、Playwright，未新增依賴或付費服務。MPFB 人體與權重仍遵循來源的 CC0 授權；來源及雜湊保留於 `assets/vendor/mpfb/`。

## 尚待完成

目前只提供固定握槍的 bind pose，沒有開合手動畫。骨架可以帶動模型，但手指大幅轉動後的接觸和甲片穿插尚未驗收。拇指根部、皮革壓褶、磨損的美術精修，以及正式角色接合、遊戲內動作和實機效能測試仍待完成。本次未替換或部署線上遊戲資產。
