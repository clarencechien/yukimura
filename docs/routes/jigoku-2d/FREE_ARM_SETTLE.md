# 末段收腳：固定部件與腰甲遮擋

2026-10-16。分支 `art/jigoku-prerendered-2d`。

[互動檢視頁原始檔](free-arm-settle/index.html) · [30 fps MP4](free-arm-settle/settle-30fps.mp4) · [手機畫面](free-arm-settle/mobile.jpg) · [前輪五姿勢](FREE_ARM_TRANSITION.md)

前輪近地到跪地會換成另一張整身原畫，前腳突然收進身下，頭盔與腰甲也改變輪廓。這輪把近地原畫的 **護脛與鞋拆成固定部件**，先等手掌接地，再屈膝收腳；末段沿用同一張頭盔與胸甲，繞腰部前傾。

![實際瀏覽器：前輪換圖與本輪固定部件收腳](free-arm-settle/settle-preview.gif)

左側直接重播上一輪五姿勢；右側是本輪試作。400 ms 前沿用前輪動作，400 ms 起改用共用胸甲和修補後的下身，420 ms 手掌接地後才收腳，500 ms 完成。這仍是獨立 Canvas 試作，未替換 Phaser 倒地或線上 v22。

## 本輪修改

- **護脛與鞋**裁自前輪近地原畫，保留可見像素。膝點固定；護脛繞膝轉動、鞋跟隨踝點，兩段不拉長也不縮短。投影長度約 73.236／77.713 px，分別是膝到踝、踝到人工鞋尖標記，不能視為人體比例量測。
- **先撐掌、後收腳**：420 ms 前腳部保持原位。護脛逐漸轉 −45°，鞋延後跟上、最後轉 −70°；相對踝角全段小於 30°。延後鞋的轉動可避免中途腳尖往地面下方掃過。
- **胸甲繞腰前傾**：沿用原肩腕軌跡，胸甲與肩甲用同一個剛性轉換對齊肩點。400→540 ms 的腰部補償平移小於 4 px，實測最大約 3.085 px；以腰部轉動承接肩部下降。
- **遮擋分層**：腿部 → 下身與膝甲 → 胸甲 → 腰甲覆蓋片 → 空手部件。膝甲遮住護脛根部，腰甲覆蓋轉腰接縫；頭部畫在膝甲前方。收進去的鞋由下身 alpha 真正遮住，始終以 alpha=1 繪製。
- **既有空手完全重用**：85／90 px 上臂和前臂、撐掌貼圖、肩肘腕及掌根曲線都沿用前輪。掌根在 420 ms 後仍固定於 `[470,668]`。

![460 ms：掌根固定，護脛與鞋開始收進下身後方](free-arm-settle/pose-460.png)

[400 ms：收腳前](free-arm-settle/pose-400.png) · [接地](free-arm-settle/pose-420.png) · [開始收腳](free-arm-settle/pose-440.png) · [接近末姿](free-arm-settle/pose-480.png) · [末姿](free-arm-settle/pose-500.png) · [關節標記](free-arm-settle/joints.png)

![關閉手臂並將腳畫在遮擋層前：鞋與護脛仍完整存在](free-arm-settle/exposed-foot.png)

檢視頁的「查看被遮腳部」只改繪圖順序，不改腿部矩陣、不縮放、不淡出。上圖另外關閉手臂，方便看見藏在衣甲後的鞋。

## 素材與限制

一次 image gen 以三姿勢原圖的近地格為參考，移除近側護脛與鞋、補回藍色衣料，保留獨立原始輸出 `touch-shin-clean.png`。這張生成稿只用於下身及腰甲遮擋；頭盔、胸甲、肩甲、護脛和鞋都裁自既有原圖。新圖以單一等比例縮放重新註冊，沒有非等比變形。來源 SHA、比例、裁片多邊形與膝踝標記見 [settle.json](free-arm-settle/settle.json)。

新增六張裁片 RGBA8 估算約 **0.951 MiB**，不含重用貼圖與畫布緩衝。沒有新增 Blender／Modal 渲染或第三方素材。

**本輪末姿比前輪更前傾，並不是原跪姿的完全相同輪廓。** 固定膝點的平面收腳只是一種可重用的動作試作，尚未處理立體腿部旋轉、膝髖連動或碰撞受力。400 ms 切入修補下身時，膝甲／布料仍有細節差異；腰甲拼接、護脛裁邊及前段三次原畫切換也仍需精修。持刀側與武器未在本頁裝配。

下一步應把這段與前段共用同一組下身和遮擋素材，再加入持刀側及接續倒地，避免只在獨立末段看起來連貫。

## 檢查與重建

```sh
python3 tools/prepare_free_arm_settle.py
node --test tools/check_free_arm_settle.mjs tools/check_free_arm_transition.mjs tools/check_free_arm_support.mjs tools/check_free_arm_parts.mjs tools/check_free_arm_reach.mjs
python3 tools/check_free_arm_settle_art.py
node tools/check_free_arm_settle_browser.mjs
python3 tools/package_free_arm_settle.py
```

- **17 項相關測試通過**：新增 4 項腿部定長、延後收腳、手臂完全重用、腰軸對齊及時間邊界檢查，加上既有 13 項。
- [素材與鞋底檢查](free-arm-settle/art-check.json)：逐裁片核對可見像素；1001 個實際 JS 骨架取樣中，鞋上 alpha > 16 的像素未超過起始鞋底 Y=684。這只驗證螢幕投影高度，不代表三維地面碰撞正確。
- [瀏覽器檢查](free-arm-settle/browser-check.json)：實際 Canvas 肩／肘／腕／膝／踝接點、固定掌根與下身、遮擋開關及腿部 alpha=1；原速／慢速、逐姿勢、重播與 390 px 手機觸控均通過，無載入錯誤。
- [影片檢查](free-arm-settle/video-check.json)：30 張實際瀏覽器畫布，四分之一速度，均勻 30 fps／1 秒 MP4；GIF 逐取樣像素核對。30 fps 是播放頻率，不是每秒三十張新原畫。

前輪檢視頁、部件與正式遊戲維持 `4c114d2` 基線。HTTP 靜態服務路徑 `/docs/routes/jigoku-2d/free-arm-settle/`；此分支尚未部署到 Pages，GitHub HTML 頁只顯示原始碼，可先看動圖和影片。
