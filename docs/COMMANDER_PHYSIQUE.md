# 武將體格修正 v15

前一版完成連續手腕與全身骨架，但沿用的 MPFB 人體手臂仍偏纖細；為配合槍柄放大的手掌，與前臂及厚重肩甲的比例不協調。本次修改實際遊戲網格的體格，而不是增加骨骼或細分面数。

## 造型

- 幸村的上臂沿長度變化，中央橫截面的半徑倍率最高 1.70，肘端收至 1.28；前臂近肘最高 1.64，向腕部收至 1.16。這些是塑形參數，不是整條手臂的尺寸倍率。
- 家康使用更厚實的體格，對應最大半徑倍率 1.784 / 1.7168。
- 胸背比腰部增加更多寬度與深度，大腿、小腿略增厚；肩甲只小幅增加包覆空間。
- 前臂甲片與軟組織使用同一個形變範圍。手腕處逐漸消退，保留純手指頂點、握槍中心、骨架綁定與動畫。
- 原本近黑的手套／布料底色略提亮。沒有新增材質貼圖或微表面雕刻。

幸村仍為 63,193 三角形，家康仍為 60,343 三角形，各 92 個遊戲骨骼、3 個材質。GPU 動畫方式不變；手機效能未實測。無付費 API 或 Modal 工作。

## 重建與檢視

`npm run models:physique` 從 `assets/optimized/commanders/*-fullbody.blend` 讀取未修改的 v14 來源，產生 `*-physique.blend` 與 v15 GLB，安裝到 `public/models` 並重建小兵／家康 GPU 動畫調色盤。重跑不會累積塑形。

`npm run models:rigs` 會先重建 v14 全身骨架，再執行上述體格修正。既有 npm `models` / `models:animations` 管線亦已串接。

內部檢視：啟動 Vite port 5180，執行 `node tools/capture-physique.mjs`、`python3 tools/physique_gallery.py`。截圖包含兩位角色、前後版本、待機、突刺、幸村橫掃／衝刺、家康倒地。`renders/physique-v15/index.html` 是離線可用的 16 張圖比較頁；圖片嵌在 HTML 內。

## 限制

本次修正體格輪廓，尚未解決厚重肩甲隨上臂外翻、完整的手掌解剖／握持表面、皮革皺褶與鎧甲微細節。現有骨架握持測試只能證明握持座標與軸向穩定，不能代替對每個手指接觸與穿模的視覺審查。沒有宣稱達到插畫精細度。

本機資產已更新；本次未推送或部署 GitHub Pages。

## 驗證

- `npm test`：26 項通過，包含既有幾何／蒙皮預算、連續手腕及跨動作握持座標檢查。
- `npm run build`：TypeScript 與 Vite 生產建置通過。
- `npx playwright test tests/browser/army.spec.mjs --grep 'Ieyasu instances|ieyasu: baked'`：2 項通過，比對 GPU／CPU 骨架並確認家康三個材質部件同步顯示。
- `renders/physique-v15/validation.json` 記錄資產 SHA-256、塑形資訊與驗證範圍。此輪未重跑完整瀏覽器套件或 Pages 測試。
