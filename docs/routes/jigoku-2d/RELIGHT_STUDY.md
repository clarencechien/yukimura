# 插畫 2.5D 補光：第一輪實際結果

> 後續已完成 [持槍待機／短刺與三種補光](YARI_MOTION.md)。本文保留第一輪無武器站姿的實驗內容與限制。

2026-10-15（Asia/Taipei），分支 `art/jigoku-prerendered-2d`。這輪使用插畫本身，沒有匯入舊 v22 人物模型。

![中性、暖火光、冷鬼火對照](relight/comparison.jpg)

[互動原圖切換比較頁](relight-review.html) · [中性 PNG](relight/neutral.png) · [暖光 PNG](relight/warm-left.png) · [冷光 PNG](relight/cool-right.png)

## 做了什麼

1. 以 [既有人物設定圖](art/02-yukimura-model-reference.png) 為參考，由 image gen 整理一次 [單人透明素材](../../../assets/source/jigoku-2d/yukimura-illustration-cutout.png)，尺寸 1024×1536。這一步是生成式整理，與設定表的角色並非逐像素剪貼相同；以整理後的素材作為本輪固定基準。
2. 在 Blender 建立一張與圖片對齊的起伏薄片，以人工指定的頭盔、胸甲、肩甲、手臂等 19 個區域估計粗略表面方向。不是完整人形模型，也沒有用圖片亮度當深度。
3. 使用同一正交相機與 UV，Cycles 實際計算中性、左暖、右冷照明。先取得灰白表面的中性反應，再計算各色光相對它的亮度比例。
4. 在線性色彩空間把受限的補光比例乘回原圖，完全沿用原圖 Alpha。原圖的面具、繫繩、六文錢、手指與布紋沒有在每張結果重新生成。

這是 **保留原畫的補光合成**。原來畫好的陰影、高光仍存在，沒有宣稱已分離出真實底色或還原實體材質。

## 這輪能證明什麼

- 三張均為 1024×1536 RGBA PNG，透明度陣列與準備好的原始素材 **逐像素相同**。
- 中性版在不透明人物區域，RGB 每個色頻最多只差 **1 / 255**；平均絕對差約 **0.413 / 255**，屬輸出量化差異。
- 暖光／冷光只改 RGB；來源像素位置、輪廓與構圖不變。這是相對新單人素材的驗證，不是宣稱與原多視角設定圖逐像素相同。
- 使用 Blender 4.3.2、Cycles CPU、4 執行緒、64 samples。三張最終圖的渲染與寫檔共 **73.22 秒**，不含 image gen、前置中性參考與表面診斷圖。
- 沒有執行 Marigold、IC-Light、Depth Anything、Modal 或 GPU 推論；本次選用可直接驗證的人工表面代理。

檢查資料：[validation.json](relight/validation.json)、[render-report.json](relight/render-report.json)。靜態比較頁另以 Chromium 測試桌面、390 px 手機尺寸、原圖切換與圖片載入，見 [browser-check.json](relight/browser-check.json)。這些不代表遊戲 FPS 或戰鬥動畫已驗證。

## 限制與下一個合適步驟

本輪已保住插畫細節，比以舊模型重畫更符合這條路線。但粗表面沒有甲片級別的法線／粗糙度／金屬度，新增照明主要是柔和的明暗與色光變化；不能正確移走原圖的高光，也不能產生準確的細部遮蔭。

目前是前方站姿、無武器素材，不是遊戲俯角或持槍姿勢。這一輪還沒有頭、手臂、槍、披風的獨立動作分層，也沒有翻身、背面或連續動畫。

下一步應先製作同一造型的固定遊戲俯角持槍圖，再分離手臂／槍／披風，做小幅待機與補光循環。若需要更明確的甲片反光，再評估法線／材質估計；不回頭以舊 3D 模型代替插畫。

## 編輯與重建

- [Blender 場景](../../../assets/optimized/jigoku-2d/illustration-relight.blend)：已封裝原圖與中性光照參考。時間軸 frame 1／2／3 分別是中性／暖光／冷光，燈光能量使用固定插值。
- [人工表面配置](../../../assets/source/jigoku-2d/relight-surfaces.json)：修改頭盔等區域的中心、範圍與起伏程度。它只是圖片座標上的粗形體，不是解剖尺寸。
- [Blender 渲染腳本](../../../tools/render_illustration_relight.py)：從原圖和配置重建場景，輸出三個照明版本。
- [比較與檢查腳本](../../../tools/review_illustration_relight.py)：比對原圖／輸出 Alpha、色值、雜湊；以 Pillow 排版縮圖，沒有額外銳化或生成式修補。

```sh
blender --background --threads 4 --python-exit-code 1 \
  --python tools/render_illustration_relight.py
python3 tools/review_illustration_relight.py
```

比較腳本需要 NumPy、Pillow 與 Noto Sans CJK 字型。場景內的中性參考已封裝，若修改起伏／基準光源，應以腳本重算參考，再產生最終圖。直接旋轉相機無法得到角色背面。

所有結果只保存於此分支的美術研究目錄，未替換 v22 遊戲資產或部署 Pages。
