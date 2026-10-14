# 幸村高模與遊戲烘焙

> 歷史／研究文件（2026-10-14 整理）：以下「目前」、測試數據與待辦指原記錄階段，不代表 v22 現況；舊版命令如需精確重現，應使用對應 Git 版本。目前採用範圍以 [狀態與交接](STATUS.md) 為準；參閱 [完整索引](INDEX.md)。

v8 把幸村從共用小塊貼圖改為專用高模／低模流程：高模 1,321,960 三角形，遊戲網格 44,130 三角形。高模保留在 Blender，遊戲仍使用原本可變形的 18 骨、八組動作網格；沒有把高模直接塞入每一名士兵。

## 可檢查的產物

- `assets/source/samurai-kit.blend` 的 `20_YUKIMURA_HIGH` collection：具名、可分開編輯的高模零件，預設隱藏；取消隱藏後在原點檢查靜止姿態。
- `yukimura_runtime`：遊戲網格、獨立 `HeroBake` UV、專用烘焙材質及原有骨架動畫。
- `public/models/hero-bake.json`：實際高／低模三角形、貼圖解析度、烘焙方法、耗時與取樣設定；不是手填的面數。
- [高模彩色預覽](art/hero-highpoly.png)與[灰模近景](art/hero-highpoly-clay.png)：Blender 渲染真正的高模幾何。
- [遊戲模型近景](art/hero-runtime-detail.png)及[無後處理 PBR](art/hero-runtime-pbr.png)：Babylon.js 載入烘焙後 GLB；用來確認細節在遊戲中是否保留。

## 製作與烘焙

`tools/hero_highpoly.py` 在具名甲冑與布料零件上建立密集支撐網格，加入實際倒角、甲片內縮刻邊／波紋、面甲局部起伏與布料次級細褶。法線來自有幾何差異的高模及細微材質凹凸，而非只把既有低模增加面數後直接匯出。

低模重新建立不重疊的 UV。烘焙複本按零件分離，低模與對應高模採同一位移，讓射線不會誤命中相鄰肩甲、手指或披風背面。烘焙後恢復位置，原高模母版保持組裝狀態。

Cycles CPU 以 2 執行緒、16 samples 執行四個 2048² pass：無照明的基礎色、tangent-space normal、roughness/metallic、ambient occlusion。局部 AO 輕量合入基礎色，組裝縫隙沿用頂點遮蔭；顏色不重複乘上紅色頂點色，也不把固定光照烘焙到角色上。最後輸出三張專用貼圖，法線使用 glTF／OpenGL 慣例。

v9 家康也使用共用甲冑和獨立 1K 烘焙；兩種足輕繼續共用原三張 atlas 與一份群兵動畫 palette，家康另用刀柄握距的 palette。高模、灰模預覽和 Blender 源檔不進網站部署。

```sh
npm run models
blender -b assets/source/samurai-kit.blend --threads 2 --python-exit-code 1 --python tools/render_highpoly.py
npm test
npm run test:e2e
npm run test:pages
```

`npm run models` 會重新生成母版與烘焙，請把手工修改另存，或回寫到生成配方。此次使用本機 Blender CPU，沒有付費 API 呼叫。Modal 仍是可選流程，遠端 timeout 已留出烘焙時間，但本輪沒有宣稱遠端執行成功。

## 尚待精修

這是程序高模與實際烘焙的第一版，不等同於雕刻師手工完成的英雄資產。外輪廓仍受既有遊戲網格限制；解剖、布料張力、破損分布與獨立手繪色彩仍需繼續修飾。此次保留現有遊戲拓樸，沒有完成新的手工重拓樸、LOD 或實體手機效能量測。
