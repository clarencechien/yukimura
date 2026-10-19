# 未來赤備：全身重新生成與漆金材質（body v2）

頭部沿用已完成的[頭部逐項精修](../head-study/README.md)，本輪只處理身體。前一版程序式重建的甲片過於方塊化，已撤回；這次改回原始的 image gen 參考圖，以 **TRELLIS.2 1536 重新生成全身**，再做材質修正與頭部接合。**沒有用幾何原件取代生成的甲冑。**

## 最新：側面草摺、背甲、肩部與頸前流蘇（pass 9）

處理 pass 8 留下的四項：側面草摺、背甲接縫、肩上的舊碎片、頸前流蘇。上排是 pass 8，下排是本輪（1000²、24 samples）。

| | 左腰側 | 右腰側 | 背甲 | 背甲側緣 | 肩前（畫面右） | 肩前（畫面左） | 頸前流蘇 | 頸前流蘇側面 | 肩流蘇 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pass 8 | ![](pass9/before/hip-l.png) | ![](pass9/before/hip-r.png) | ![](pass9/before/back-upper.png) | ![](pass9/before/seam-back-l.png) | ![](pass9/before/patch-l.png) | ![](pass9/before/patch-r.png) | ![](pass9/before/tassel-neck.png) | ![](pass9/before/tassel-neck-side.png) | ![](pass9/before/tassel-shoulder.png) |
| 本輪 | ![](pass9/renders/hip-l.png) | ![](pass9/renders/hip-r.png) | ![](pass9/renders/back-upper.png) | ![](pass9/renders/seam-back-l.png) | ![](pass9/renders/patch-l.png) | ![](pass9/renders/patch-r.png) | ![](pass9/renders/tassel-neck.png) | ![](pass9/renders/tassel-neck-side.png) | ![](pass9/renders/tassel-shoulder.png) |

| 正面 | 斜側 | 側面 | 背面 | 白模 |
| --- | --- | --- | --- | --- |
| ![](pass9/renders/front.png) | ![](pass9/renders/three-quarter.png) | ![](pass9/renders/side.png) | ![](pass9/renders/back.png) | ![](pass9/renders/clay.png) |

**做法**

1. **側面草摺（[lame_panels.py](../../../../tools/lame_panels.py)、[報告](pass9/lame-panels-report.json)）**
   - 左右腰側各加一片草摺，從正側面取表面，與前後草摺同樣是 5 枚、等高等距的水平甲片。
   - 手臂垂在側面擋住草摺，所以甲片建在手臂後方、貼著腰。打到手臂的射線離擬合面太遠，會被穩健擬合當成離群值剔除，只留下腰側的表面。
2. **背甲改為甲片**
   - pass 2 的背甲外殼整個移除，改以和胸甲相同的做法，建 6 片水平背甲（z 1.16–1.45 m）。
   - 背面原圖沒有畫，因此背甲貼圖沿用胸甲的拉直條。胸甲第一條畫有頸前流蘇，背甲第一片改用第二條，避免背上出現畫上去的流蘇。
   - 外殼與新甲片的接縫因此不存在了。
3. **肩上的舊碎片**
   - 槳狀板被壓平的那塊在畫面右側（角色左肩前）。胸甲最上面兩片在這一側延長 6.5 cm，蓋住那塊；下面四片維持原寬，避免伸進手臂。
4. **流蘇（[tie_cords.py](../../../../tools/tie_cords.py)、[報告](pass9/tie-report.json)）**
   - **頸前流蘇：** pass 8 的流蘇頭剛好落在第一片胸甲的金邊上，線束一開始就卡在金邊裡，被推成水平、往前翻。這次把兩條尾繩從 5.5 cm 加長到 8.5 cm，讓流蘇頭垂到金邊下方。
   - **線束：** 上半部仍是束緊的硬束，只在繫結處樞轉；下半部改成較軟的絲線，碰到甲片的捲邊時會順著垂下，不再像棍子一樣搭在上面。
   - **線的方向：** 每條線改用流蘇頭固定的放射方向，投影到中心線的垂直面上。沿中心線傳遞的座標框在彎處會扭轉，使線束散開，這次已修正。中心線在撞擊時的細小抖動，在鋪線前先平滑掉，線不再呈鋸齒狀。
   - **肩流蘇：** 錨點再外移 2 cm，離開新甲片的捲邊，流蘇可以自由垂下。

**檔案（完整版，四個一起載入）**

| 部分 | 檔案 | 大小 | 三角面 |
| --- | --- | ---: | ---: |
| 頭 | [body-v2-pass9-head.glb](pass9/body-v2-pass9-head.glb) | 30.3 MB | 227,742 |
| 身體 | [body-v2-pass9-body.glb](pass9/body-v2-pass9-body.glb) | 61.0 MB | 491,356 |
| 甲片 | [body-v2-pass9-plates.glb](pass9/body-v2-pass9-plates.glb) | 4.8 MB | 131,600 |
| 繩子 | [body-v2-pass9-cords.glb](pass9/body-v2-pass9-cords.glb) | 2.7 MB | 115,866 |
| 合併檢視版 | [body-v2-pass9-preview.glb](pass9/body-v2-pass9-preview.glb) | 76.6 MB | 698,349 |

身體的面數比 pass 8 少，因為背甲外殼移除了；甲片的面數增加，因為多了背甲與兩片側草摺。

**檢查**
- 四個部分與檢視版都沒有近零面積三角形，所有 primitive 都有法線（`pass9/inspection-*.json`、[檢視版](pass9/preview-inspection.json)）。
- 射線檢查無穿透縫（[報告](pass9/merge-report.json)）。
- [互動檢視器 ZIP](viewer.zip) 已改用本輪模型，並通過離線瀏覽器檢查。

**仍待處理**
- **側面草摺的上緣：** 兩側最上面兩片在部分光線下偏亮，而且邊緣被手臂與前草摺切成斜的。正側面看不到，斜看才會注意到。
- **頸前流蘇側面：** 胸甲外傾，流蘇順著甲面斜靠，側面看約 30–40°。這是物理結果，若要更貼身，需要讓流蘇頭再往後收。
- **背甲貼圖：** 背面原圖沒有畫，現在借用胸甲的貼圖，綴繩與金扣的位置是推測的。

```sh
python tools/lame_panels.py --model .tmp/cleared.glb --output .tmp/plates.glb
python tools/clean_limb_texture.py --model .tmp/plates.glb --output .tmp/clean.glb
python tools/tie_cords.py --model .tmp/clean.glb --output .tmp/tied.glb
python tools/merge_character.py --model .tmp/tied.glb --output docs/experiments/future-sanada/body-v2/pass9/body-v2-pass9.glb --split
python tools/package_body_v2.py --model .tmp/tied.glb --directory docs/experiments/future-sanada/body-v2/pass9 --name body-v2-pass9-preview --join
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass9
```

（`.tmp/cleared.glb` 與 pass 8 相同，由 pass 6 的 `neck_cords.py --clear-only` 與 `waist_cord.py --clear-only` 產生。）

## 前一階段：全身板甲改為水平規則、拆檔（pass 8）

依回饋：胸甲應該是**水平的橫片**，不該斜得不規則；其餘的甲也一起修，並把檔案拆開。上排是 pass 7，下排是本輪（1000²、24 samples）。

| 原圖：胸甲與草摺 |
| --- |
| ![](pass8/reference-plates.png) |

| | 胸甲 | 胸甲白模 | 前草摺 | 後草摺 | 左袖 | 右袖 | 膝 | 脛 | 前臂 | 頸部 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pass 7 | ![](pass8/before/plate-chest.png) | ![](pass8/before/clay-plate-chest.png) | ![](pass8/before/kusazuri-front.png) | ![](pass8/before/kusazuri-back.png) | ![](pass8/before/sode-l.png) | ![](pass8/before/sode-r.png) | ![](pass8/before/knees.png) | ![](pass8/before/shins.png) | ![](pass8/before/forearm-l.png) | ![](pass8/before/neck-front.png) |
| 本輪 | ![](pass8/renders/plate-chest.png) | ![](pass8/renders/clay-plate-chest.png) | ![](pass8/renders/kusazuri-front.png) | ![](pass8/renders/kusazuri-back.png) | ![](pass8/renders/sode-l.png) | ![](pass8/renders/sode-r.png) | ![](pass8/renders/knees.png) | ![](pass8/renders/shins.png) | ![](pass8/renders/forearm-l.png) | ![](pass8/renders/neck-front.png) |

| 正面 | 斜側 | 側面 | 背面 | 白模 |
| --- | --- | --- | --- | --- |
| ![](pass8/renders/front.png) | ![](pass8/renders/three-quarter.png) | ![](pass8/renders/side.png) | ![](pass8/renders/back.png) | ![](pass8/renders/clay.png) |

**做法**

1. **胸甲、草摺、袖甲：改為模型空間水平的甲片（[lame_panels.py](../../../../tools/lame_panels.py)、[報告](pass8/lame-panels-report.json)）**
   - 上一版照原圖描邊，但原圖人物是側轉的，畫出來的甲片又弧又斜。這次在模型上直接排成等高、等距的水平片。
   - 胸甲 6 片。草摺有前 2、後 3 共 5 片面板，每片 5 枚，底片最大。左右袖甲各 1。
   - 每片的面在自己的視角下以射線取得表面，再以穩健多項式擬合、去除凹凸。
   - 甲片外傾、上緣塞進上片，下緣有捲邊與金邊；兩端用四次曲線向後彎，包住身體。
2. **貼圖把原圖拉直**
   - 胸甲：沿描出的弧線逐片把原圖的胸甲拉成水平條，原本畫的綴繩、金扣和縫跟著變成水平、對齊甲片邊緣。
   - 草摺與袖甲：取原圖正面那片草摺，含綴繩列與底片金波紋。
   - 所有甲片共用一張貼圖：原圖乘上反照率修正，約 1.7 MB。
3. **四肢機械甲（[clean_limb_texture.py](../../../../tools/clean_limb_texture.py)、[報告](pass8/limb-texture-report.json)）**
   - 白模可見膝、脛、前臂的幾何其實還算乾淨。我先試了保邊的網格平滑，平均只動 0.6 mm，看不出差別，已放棄。
   - 凹凸感其實來自生成貼圖上的暗色污斑。因此在四肢區把每個貼圖像素分成赤漆、金、黑三類，各自在同類內做保邊平滑，去掉污斑，同時保留邊緣與金線。
4. **繩子重新綁上**：甲片重建後重跑物理。肩繩錨點往前移 1.1 cm，避開新甲片的上緣，否則流蘇會被卡住、壓扁。
5. **拆檔（[merge_character.py](../../../../tools/merge_character.py) `--split`）**：完整版拆成頭、身體、甲片、繩子 4 個 GLB，加上一份 [manifest](pass8/body-v2-pass8-manifest.json)，記錄大小與 SHA-256。四個檔案使用同一座標系，一起載入即為完整角色。

**檔案（完整版，四個一起載入）**

| 部分 | 檔案 | 大小 | 三角面 |
| --- | --- | ---: | ---: |
| 頭 | [body-v2-pass8-head.glb](pass8/body-v2-pass8-head.glb) | 30.3 MB | 227,742 |
| 身體 | [body-v2-pass8-body.glb](pass8/body-v2-pass8-body.glb) | 62.0 MB | 515,312 |
| 甲片 | [body-v2-pass8-plates.glb](pass8/body-v2-pass8-plates.glb) | 3.9 MB | 94,232 |
| 繩子 | [body-v2-pass8-cords.glb](pass8/body-v2-pass8-cords.glb) | 2.8 MB | 120,176 |
| 合併檢視版 | [body-v2-pass8-preview.glb](pass8/body-v2-pass8-preview.glb) | 76.8 MB | 689,247 |

**檢查**
- 四個部分與檢視版都沒有近零面積三角形，所有 primitive 都有法線（`pass8/inspection-*.json`、[檢視版](pass8/preview-inspection.json)）。
- 射線檢查無穿透縫（[報告](pass8/merge-report.json)）。
- [互動檢視器 ZIP](viewer.zip) 曾改用本輪模型，現已改用 pass 9。

**仍待處理（已在 pass 9 處理）**
- **側面草摺：** 左右側的草摺被垂下的手臂擋住，這次沒有重建。
- **背甲與甲片的接合：** 背甲外殼（pass 2）和新甲片的交界，近看還有接縫。
- **肩上的舊碎片：** 右肩槳狀板壓平處的陰影仍在。
- **頸前流蘇：** 掛在第二片胸甲的捲邊上，線束在那裡往外翻。這是物理結果，但不一定是你要的樣子。

```sh
python tools/lame_panels.py --model .tmp/cleared.glb --output .tmp/plates.glb
python tools/clean_limb_texture.py --model .tmp/plates.glb --output .tmp/clean.glb
python tools/tie_cords.py --model .tmp/clean.glb --output .tmp/tied.glb
python tools/merge_character.py --model .tmp/tied.glb --output docs/experiments/future-sanada/body-v2/pass8/body-v2-pass8.glb --split
python tools/package_body_v2.py --model .tmp/tied.glb --directory docs/experiments/future-sanada/body-v2/pass8 --name body-v2-pass8-preview --join
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass8
```

（`.tmp/cleared.glb` 由 pass 6 的 `neck_cords.py --clear-only` 與 `waist_cord.py --clear-only` 產生。）

## 前一階段：板甲第一步：胸甲重建（pass 7）

開始修板甲。全身檢查結果：
- **胸甲：** 表面凹凸、邊緣波浪，綴繩結成團。TRELLIS 還把原圖的兩片甲合成一片。
- **袖甲：** 像融化一樣。
- **腿甲：** 一團一團，原圖則是俐落的機械板加金邊。

問題在形狀而不是顏色（顏色先前的投影已經修正）。所以這一輪的做法是依原圖重建乾淨的板片，先從最顯眼的胸甲開始。上排是 pass 6，下排是本輪（1000²、24 samples）。

| 原圖：胸甲 |
| --- |
| ![](pass7/reference-chest.png) |

| | 胸甲 | 胸甲白模 | 上半身 | 頸結 | 頸部 |
| --- | --- | --- | --- | --- | --- |
| pass 6 | ![](pass7/before/plate-chest.png) | ![](pass7/before/clay-plate-chest.png) | ![](pass7/before/torso.png) | ![](pass7/before/knot-neck.png) | ![](pass7/before/neck-front.png) |
| 本輪 | ![](pass7/renders/plate-chest.png) | ![](pass7/renders/clay-plate-chest.png) | ![](pass7/renders/torso.png) | ![](pass7/renders/knot-neck.png) | ![](pass7/renders/neck-front.png) |

[正面](pass7/renders/front.png) · [斜側](pass7/renders/three-quarter.png) · [側面](pass7/renders/side.png) · [白模](pass7/renders/clay.png)

**做法（[chest_lames.py](../../../../tools/chest_lames.py)、[報告](pass7/chest-lames-report.json)）**

1. **在原圖上描甲片：** 沿 50 個欄位追蹤深色縫隙線，再以二次曲線擬合，得到頂片上緣、5 條縫、下緣共 7 條弧線，與原圖的弧度一致。
2. **轉到模型上：** 透過剪影對齊與光流的反向映射，把弧線換算到模型座標。光流在公分尺度有雜訊，會讓甲片邊緣出現折角，所以幾何改用擬合過的平滑三次映射。
3. **建出甲片**（頂片加 5 片）：
   - 建在平滑化的胸甲曲面上，每片往下緣外傾 5.5 mm，上緣塞進上一片下面，厚 2.5 mm。
   - 下緣加上捲邊與金色邊條。
   - 原本凹凸的表面往後推，成為縫隙中的暗色內層。
4. **貼圖：** UV 直接用原圖像素，所以原圖畫的縫、綴繩與金扣，天生就和甲片邊緣對齊。第一次試算是先定幾何再投影貼圖，結果畫的縫和實際邊緣錯開，已改掉。
5. **繩子重綁：** 胸甲重建後重新跑繩子物理，頸流蘇改為垂在新的甲片階梯上。

**檢查**：完整版 902,084 面、97 MB，檢視版 633,869 面；兩者都沒有近零面積三角形，射線檢查無穿透縫（[完整版](pass7/mesh-inspection.json)、[檢視版](pass7/preview-inspection.json)、[合併](pass7/merge-report.json)）。互動檢視器隨後改用 pass 8 模型。

**下載**：[body-v2-pass7.glb](pass7/body-v2-pass7.glb)（97 MB）· [body-v2-pass7-preview.glb](pass7/body-v2-pass7-preview.glb)（74 MB）

**接下來**
- **其他甲：** 用同一套方法處理袖甲、裙甲和腿甲。
- **檔案大小：** 完整版已接近 GitHub 單檔 100 MB 上限，再加板甲前要先縮減，例如壓縮身體貼圖或拆檔。
- **右肩：** 舊槳狀板壓平處的陰影仍待處理。

```sh
python tools/neck_cords.py --model docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb --output .tmp/clear-neck.glb --clear-only
python tools/waist_cord.py --model .tmp/clear-neck.glb --output .tmp/cleared.glb --clear-only
python tools/chest_lames.py --model .tmp/cleared.glb --output .tmp/chest.glb
python tools/tie_cords.py --model .tmp/chest.glb --output .tmp/tied.glb
python tools/merge_character.py --model .tmp/tied.glb --output docs/experiments/future-sanada/body-v2/pass7/body-v2-pass7.glb
python tools/package_body_v2.py --model .tmp/tied.glb --directory docs/experiments/future-sanada/body-v2/pass7 --name body-v2-pass7-preview --join
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass7
```

## 前一階段：以物理重做繩結、繩子與流蘇（pass 6）

上一版的回饋是腰結太死板、頸結遠看可以但近看不行。近拍檢查找到三個原因：結是一疊圓盤、流蘇是幾片平板，繩子是規則的三股扭繩。原圖則是編繩自己打成的結，流蘇是很多細線折過圓頭、用細繩束起後自然垂下。上排是 pass 5，下排是本輪（1000²、24 samples）。

| 原圖：頸結 | 原圖：腰結 |
| --- | --- |
| ![](pass6/reference-neck-knot.png) | ![](pass6/reference-waist-knot.png) |

| | 頸結近拍 | 頸部 | 腰結近拍 | 腰結斜側 | 腰部 | 肩繩流蘇 |
| --- | --- | --- | --- | --- | --- | --- |
| pass 5 | ![](pass6/before/knot-neck.png) | ![](pass6/before/neck-front.png) | ![](pass6/before/knot-waist.png) | ![](pass6/before/knot-waist-side.png) | ![](pass6/before/audit-waist.png) | ![](pass6/before/tassel-shoulder.png) |
| 本輪 | ![](pass6/renders/knot-neck.png) | ![](pass6/renders/neck-front.png) | ![](pass6/renders/knot-waist.png) | ![](pass6/renders/knot-waist-side.png) | ![](pass6/renders/audit-waist.png) | ![](pass6/renders/tassel-shoulder.png) |

| 正面 | 斜側 | 側面 | 背面 | 白模 |
| --- | --- | --- | --- | --- |
| ![](pass6/renders/front.png) | ![](pass6/renders/three-quarter.png) | ![](pass6/renders/side.png) | ![](pass6/renders/back.png) | ![](pass6/renders/clay.png) |

**做法**

1. **物理模擬（[cord_physics.py](../../../../tools/cord_physics.py)，position-based dynamics）**
   - 繩子以粒子鏈表示，含拉伸與彎曲約束、重力與阻尼。
   - 與盔甲表面碰撞時帶摩擦，繩與繩之間互相推開。
   - 單次推出距離設上限，避免粒子在單層薄殼上被推到另一側而彈跳。
2. **繩子掛法（[tie_cords.py](../../../../tools/tie_cords.py)）**
   - 頸繩從面罩兩側下來，靠重力垂墜、貼著盔甲到喉前的結。
   - 肩繩從金具垂下；腰繩繞腰一圈，自然貼合身體。
   - 結下的短繩把較重的流蘇頭垂下。
3. **結**：改成原圖那種圓球狀的裝飾結（monkey's fist）。兩組各三圈的編繩互相交錯、一上一下，旋轉 45° 讓正面看到斜向交叉。腰結旁的繩圈拿掉，比較接近原圖。
4. **編繩質感**
   - 繩子改成平滑圓管，加上可重複的 kongo-gumi 編紋法線貼圖與顏色貼圖（[braid-normal](pass6/braid-normal.png)、[braid-color](pass6/braid-color.png)）。近看可見人字編紋。
   - 輪廓乾淨，繩子三角面從約 9.6 萬降到 2.4 萬。
5. **流蘇**
   - 流蘇整束當作一條有厚度的物理繩：從束口下方垂直落下，有彎曲剛性，碰到盔甲會順著貼上。
   - 每個流蘇 120 條細線依中心線排成先鼓後收的形狀，並往上翻過圓頭，再以黃銅細繩纏 4.5 圈束起。
   - 一開始逐條模擬線束，結果亂成拖把狀，因此改為整束模擬。
6. **流蘇接回繩子**（依回饋修正：流蘇「像憑空冒出來」）
   - 原因是結到流蘇的短繩太短，大部分藏在球結或流蘇頭裡；頭部的線又從一個點開始，看起來像黏上去的。
   - 短繩加長：頸 3 → 5.5 cm、腰 2.8/3.6 → 5/6 cm，可以看到繩子從結延伸進流蘇。
   - 頭部的線改從繩子表面開始往外鋪開，接口再用 5 圈細線纏住。
7. **清除舊繩**
   - 原本長在胸甲上的槳狀板、腰部舊結與流蘇，壓平前先在曲面上做 Tutte 鬆弛，展開被壓扁而互相重疊的三角形，以免留下碎片。
   - 壓平後的區域改用周圍盔甲貼圖的中位色。
   - 鬆弛後退化的面會被消除（頸部 40 面、腰部 209 面）。

**檢查**
- 完整版 862,466 面，檢視版 594,251 面，都是單一物件；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass6/mesh-inspection.json)、[檢視版](pass6/preview-inspection.json)）。
- 頭身縫隙重新用射線檢查：能穿透看到背景的為 0（[報告](pass6/merge-report.json)）。
- 模擬參數與結果見[繩結報告](pass6/tie-report.json)，清除紀錄見[頸部](pass6/neck-clear-report.json)、[腰部](pass6/waist-clear-report.json)。
- 完整版為了壓在 GitHub 100 MB 限制內，沒有存切線；依 glTF 規範，閱讀器會自行以 MikkTSpace 計算。檢視版則有存切線。
- 互動檢視器隨後改用 pass 7 模型。

**下載**：[body-v2-pass6.glb](pass6/body-v2-pass6.glb)（95.5 MB，完整版）· [body-v2-pass6-preview.glb](pass6/body-v2-pass6-preview.glb)（72 MB）

**仍待處理**

- **右肩槳狀板壓平處仍不乾淨。** 壓平後仍有暗色起皺的陰影，平常被肩流蘇擋住，從側面近看才看得到。
- **流蘇線數很多。** 6 個流蘇共約 8.5 萬面，遊戲版需要改成卡片式或做 LOD。
- **還沒做骨架。** 骨架與動作依指示，等細節確認後再進行。

```sh
python tools/neck_cords.py --model docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb --output .tmp/clear-neck.glb --clear-only
python tools/waist_cord.py --model .tmp/clear-neck.glb --output .tmp/cleared.glb --clear-only
python tools/tie_cords.py --model .tmp/cleared.glb --output .tmp/tied.glb
python tools/merge_character.py --model .tmp/tied.glb --output docs/experiments/future-sanada/body-v2/pass6/body-v2-pass6.glb
python tools/package_body_v2.py --model .tmp/tied.glb --directory docs/experiments/future-sanada/body-v2/pass6 --name body-v2-pass6-preview --join
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass6
```

## 前一階段：依原圖重做頸繩與腰繩、頭身合併（pass 5）

對照原插圖：頸部是一條**粗編繩**，從面罩兩側繞到喉前打結，下面**並排垂兩個流蘇**；兩肩金具也各垂一條編繩與長流蘇。腰部是**更粗的編繩**，結旁有兩個繩圈，下面垂兩個流蘇。TRELLIS 生成的版本卻是一個歪的圓錐、兩片「槳狀」紅板，以及一個光滑的心形結。上排是 pass 4，下排是本輪（1000²、24 samples）。

| 原圖：頸部 | 原圖：腰部 |
| --- | --- |
| ![](pass5/reference-neck.png) | ![](pass5/reference-waist.png) |

| | 頸部正面 | 頸部斜側 | 腰結 | 胸前 | 背後腰帶 |
| --- | --- | --- | --- | --- | --- |
| pass 4 | ![](pass5/before/neck-front.png) | ![](pass5/before/neck-low.png) | ![](pass5/before/audit-waist.png) | ![](pass5/before/torso.png) | ![](pass5/before/back-lower.png) |
| 本輪 | ![](pass5/renders/neck-front.png) | ![](pass5/renders/neck-low.png) | ![](pass5/renders/audit-waist.png) | ![](pass5/renders/torso.png) | ![](pass5/renders/back-lower.png) |

| 正面 | 斜側 | 側面 | 背面 | 白模 |
| --- | --- | --- | --- | --- |
| ![](pass5/renders/front.png) | ![](pass5/renders/three-quarter.png) | ![](pass5/renders/side.png) | ![](pass5/renders/back.png) | ![](pass5/renders/clay.png) |

**做法**

1. **頸繩（[工具](../../../../tools/neck_cords.py)、[報告](pass5/cords-report.json)）**
   - 移除歪掉的圓錐流蘇，以及圍在下巴、凹凸不平的舊繩圈；舊繩圈依繩子的紅色貼圖判斷。
   - 兩片「槳狀」板和胸甲長在一起，直接刪會撕出破洞（第一次試算就是如此）。改為以周圍胸甲擬合曲面，把它們壓平貼回胸甲。
   - 新繩依原圖重建：三股編繩，從面罩兩側繞到喉前打結，下面垂兩個流蘇；兩肩各一條編繩加長流蘇。位置都由正面射線放到表面上。
2. **腰繩（[工具](../../../../tools/waist_cord.py)、[報告](pass5/waist-report.json)）**
   - 舊心形結與流蘇同樣壓平，原本的光亮紅貼圖改成深色布帶，對應原圖結後方的黑色腰帶。
   - 新編繩比頸繩更粗，以射線沿腰部繞一圈，避開垂下的前臂。結偏左，旁邊兩個繩圈，下面兩個流蘇。
   - 繩子、結、流蘇共用一套程式（[cord_geometry.py](../../../../tools/cord_geometry.py)）。
3. **頭身合併（[工具](../../../../tools/merge_character.py)、[報告](pass5/merge-report.json)）**
   - 頭盔、身體、繩子、內襯等 59 個零件合成**單一物件**，保留 23 個材質。
   - 頭盔之後會跟著頭部骨骼一起動，所以沒有把頂點硬焊到身體上。
   - 改用射線檢查縫隙：從四周與上方各打 3000 條射線，射向頸內與衣領內側的目標點，目標點都在軀幹內部。
     - 衣領一帶第一輪找到 8 處可以直接看到的縫，位置在肩上、頸甲外擴處。
     - 因此在頸部內襯外再加一圈貼合軀幹內側、頂部封閉的深色內層。之後頸內射線全部被擋住；衣領一帶只剩 2 條能從頸甲下方的正常開口看進去，**能穿過去看到背景的為 0**。

**檢查**：完整版 808,090 面（新繩約 6.3 萬面），檢視版 539,763 面，都是單一物件；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass5/mesh-inspection.json)、[檢視版](pass5/preview-inspection.json)）。互動檢視器隨後改用 pass 6 模型。

**下載**：[body-v2-pass5.glb](pass5/body-v2-pass5.glb)（94 MB，完整版）· [body-v2-pass5-preview.glb](pass5/body-v2-pass5-preview.glb)（60 MB）

**仍待處理**

- **繩子是程式產生的。** 編繩、結與流蘇的形狀依原圖重建，但沒有手工雕刻的細部。
- **繩子底下的胸甲是推測的。** 壓平後的胸甲表面沿用生成貼圖。
- **還沒做骨架。** 骨架、權重與 LOD 依你的指示，等細節確認後再進行。

```sh
python tools/neck_cleanup.py --model docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb --output docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb
python tools/neck_cords.py --model docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb --output .tmp/cords.glb
python tools/waist_cord.py --model .tmp/cords.glb --output .tmp/cords-waist.glb
python tools/merge_character.py --model .tmp/cords-waist.glb --output docs/experiments/future-sanada/body-v2/pass5/body-v2-pass5.glb
python tools/package_body_v2.py --model .tmp/cords-waist.glb --directory docs/experiments/future-sanada/body-v2/pass5 --name body-v2-pass5-preview --join
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass5
```

## 前一階段：頸部清理（pass 4）

移除生成的頭部時，連帶截斷了頸部的繩子，留下兩段**懸在半空的流蘇尖**；舊頭部的頸口也空著，背後的頸甲（しころ）與衣領之間露出一道**黑縫**。上排是 pass 3，下排是本輪（1000²、24 samples）。

| | 正面 | 側面 | 背面 | 背面白模 |
| --- | --- | --- | --- | --- |
| pass 3 | ![](pass4/before/neck-front.png) | ![](pass4/before/neck-side.png) | ![](pass4/before/neck-back.png) | ![](pass4/before/clay-neck-back.png) |
| 本輪 | ![](pass4/renders/neck-front.png) | ![](pass4/renders/neck-side.png) | ![](pass4/renders/neck-back.png) | ![](pass4/renders/clay-neck-back.png) |

| 正面 | 斜側 | 側面 | 背面 | 白模 |
| --- | --- | --- | --- | --- |
| ![](pass4/renders/front.png) | ![](pass4/renders/three-quarter.png) | ![](pass4/renders/side.png) | ![](pass4/renders/back.png) | ![](pass4/renders/clay.png) |

**做法（[工具](../../../../tools/neck_cleanup.py)、[報告](pass4/neck-report.json)）**

1. **移除懸空碎片。** 生成的網格本來就有許多獨立零件，例如鉚釘、流蘇、繩結。因此不以「是否相連」判斷，而是看每塊與其他所有表面的最近距離：
   - 距離超過 6 mm 的視為懸空，共移除 13 塊、936 個頂點。
   - 其中包括兩段流蘇尖（分別離最近表面 6.5 cm 與 4.5 cm），以及頭盔內看不到的殘片。
2. **頸部內襯。** 在頭盔下方加一段深色布質內襯，形狀是從頸部中心向外量出來的：
   - 每個角度、每個高度各發一條射線，找到頸甲、衣領或面罩的內側，內襯就放在內側往內 4 mm 處，再平滑。
   - 原本試過固定橢圓，但後頸開口最寬，橢圓放太深擋不住，因此改用量測。

**檢查**：完整版 742,910 面，檢視版 474,114 面；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass4/mesh-inspection.json)、[檢視版](pass4/preview-inspection.json)）。互動檢視器隨後改用 pass 5 模型。

**下載**：[body-v2-pass4.glb](pass4/body-v2-pass4.glb)（93 MB，完整版）· [body-v2-pass4-preview.glb](pass4/body-v2-pass4-preview.glb)（59 MB）

**仍待處理**

- **頭與身體尚未焊接。** 兩者仍是分開的零件，目前只是靠內襯擋住縫隙。
- **還不能進遊戲。** 骨架、權重、動作與 LOD 都還沒做。

```sh
python tools/neck_cleanup.py --model docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb --output docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb
python tools/package_body_v2.py --model docs/experiments/future-sanada/body-v2/pass4/body-v2-pass4.glb --directory docs/experiments/future-sanada/body-v2/pass4 --name body-v2-pass4-preview
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass4
```

## 前一階段：手甲、手套、腿甲與能量槽（pass 3）

背甲與裙甲完成後，接著處理四肢。上排是 pass 2，下排是本輪；鏡位與燈光相同（1000²、24 samples）。第三欄是**去掉燈光的原色**：金屬金在暗攝影棚只反射暗環境，有燈光的圖會讓金色指節看起來偏暗。

| | 右手 | 左手 | 左手原色 | 左前臂 | 膝甲 | 左脛甲近拍 |
| --- | --- | --- | --- | --- | --- | --- |
| pass 2 | ![](pass3/before/hand-r-front.png) | ![](pass3/before/hand-l-front.png) | ![](pass3/before/albedo-hand-l.png) | ![](pass3/before/forearm-l.png) | ![](pass3/before/knees.png) | ![](pass3/before/seam-shin-l.png) |
| 本輪 | ![](pass3/renders/hand-r-front.png) | ![](pass3/renders/hand-l-front.png) | ![](pass3/renders/albedo-hand-l.png) | ![](pass3/renders/forearm-l.png) | ![](pass3/renders/knees.png) | ![](pass3/renders/seam-shin-l.png) |

[正面](pass3/renders/front.png) · [斜側](pass3/renders/three-quarter.png) · [背面](pass3/renders/back.png) · [右手原色](pass3/renders/albedo-hand-r.png) · [左手白模](pass3/renders/clay-hand-l-out.png)

**做法**

1. **四肢套用原圖投影。** 胸甲與前裙甲用的投影，延伸到袖甲、手甲、手套、膝甲、脛甲與靴子。各區只投正面，因為只有軀幹有背面來源圖。
   - 手套有了原圖的金色指節、紅色手背甲與金框，以及機械質感的黑色手套紋理。
   - 手指形狀沿用 TRELLIS 生成，白模可見五指與放鬆姿勢都還算完整，本輪沒有更動幾何。
2. **能量槽改成實體發光條。** 原圖的橘色能量槽只有 1–3 px 寬，比投影對齊的誤差（光流中位數約 20 px）還細。
   - 直接把發光畫進貼圖時，會把金邊和漆面高光誤判成光，變成到處散落的光點；這個試算已棄用。
   - 改為在原圖找出 8 條槽的中心線（[座標](pass3/energy-seams.json)、[尋找工具](../../../../tools/find_energy_seams.py)）：左右前臂、左胸側、兩個膝甲鏡片、兩條脛甲。
   - 以光流反推，再從正面射線投到身體表面，鋪上圓頂狀的發光條，下方加一道暗色槽（[工具](../../../../tools/energy_seam_strips.py)、[報告](pass3/energy-seam-report.json)）。
   - 發光以 glTF emissive＋`KHR_materials_emissive_strength` 匯出。

**檢查**：完整版 743,438 面，檢視版 473,718 面；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass3/mesh-inspection.json)、[檢視版](pass3/preview-inspection.json)）。互動檢視器隨後改用 pass 4 模型。

**下載**：[body-v2-pass3.glb](pass3/body-v2-pass3.glb)（93 MB，完整版）· [body-v2-pass3-preview.glb](pass3/body-v2-pass3-preview.glb)（59 MB）

**仍待處理**

- **能量槽偏白。** 在 Cycles／AgX 下，發光強度 ≥ 3 都會顯示成接近白色的核心；原圖本身也是白芯，只是外圍的橘色光暈沒有後製泛光。
- **手部背面沒有原圖。** 手掌與手背後側仍是生成貼圖。
- **頸部與骨架尚未處理。** 頸部還沒焊接，也還沒綁骨架。

```sh
python tools/project_reference.py --output docs/experiments/future-sanada/body-v2/pass3 --output-glb .tmp/v4/projected.glb
python tools/back_plate_shell.py --model .tmp/v4/projected.glb --output docs/experiments/future-sanada/body-v2/pass3 --name body-v2-shell.glb
python tools/find_energy_seams.py
python tools/energy_seam_strips.py --model <上一步的 body-v2-shell.glb> --output docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb
python tools/render_albedo.py --model docs/experiments/future-sanada/body-v2/pass3/body-v2-pass3.glb --output hand.png --target 0.376,-0.16,0.89 --span .35
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass3
```

## 前一階段：背甲與裙甲精修（pass 2）

背甲上下與前後裙甲仍有問題，本輪改為針對這兩處修整。上排是前一版，下排是本輪；鏡位與燈光相同（1000²、24 samples）。

| | 背甲上半 | 背甲下半／腰帶 | 前裙甲 | 後裙甲 |
| --- | --- | --- | --- | --- |
| 前一版 | ![](pass2/before/back-upper.png) | ![](pass2/before/back-lower.png) | ![](pass2/before/skirt-front.png) | ![](pass2/before/skirt-back.png) |
| 本輪 | ![](pass2/renders/back-upper.png) | ![](pass2/renders/back-lower.png) | ![](pass2/renders/skirt-front.png) | ![](pass2/renders/skirt-back.png) |

| 背甲白模：前一版 | 背甲白模：本輪 | 本輪正面 | 本輪背面 |
| --- | --- | --- | --- |
| ![](pass2/before/clay-back-upper.png) | ![](pass2/renders/clay-back-upper.png) | ![](pass2/renders/front.png) | ![](pass2/renders/back.png) |

**做法**

1. **把原圖投影回模型（前面）。** TRELLIS 的貼圖原本就是從同一張插畫生成，只是較糊。先以輪廓對齊原圖（重疊度 IoU 0.856），再用光流修正局部偏移（中位數約 20 px）。可見性以 z-buffer 判斷，再把原圖直接投到胸甲、腰帶與前裙甲（[投影工具](../../../../tools/project_reference.py)）。
   - 前裙甲因此有了原圖的金色波紋、黑色綴繩與鱗狀內襯。
   - 立體繩結與流蘇的位置和畫面不同，所以保留原本的紅色，不投影。
2. **背面來源圖。** 原圖沒有背面，因此用正面乾淨的部位組成[背面來源圖](pass2/back-reference.png)（[產生工具](../../../../tools/build_back_reference.py)）：
   - 背甲：取避開流蘇的五片胸前橫片，左右鏡像、依片距 37 px 往上延伸。
   - 中央裙板：繩結改以同一塊裙板的橫片補上。
3. **背甲外殼（[工具](../../../../tools/back_plate_shell.py)）。** 生成的背甲是封閉網格，但薄殼上有貫穿的洞，補洞處理不到。
   - 改在背甲表面加一層外殼：形狀由每格一條射線量出的實際表面決定，只有洞裡改用穩健多項式補平。
   - 依背面來源圖的橫片縫隙做出逐片重疊的高低差，邊緣沉入身體 5 mm，不會看到方框。
   - 貼圖直接用清晰的來源圖。生成的背甲仍保留在下面，沒有刪除。
4. **後裙甲不投影。** 試過兩種投影：直接投會讓綴繩重複一層，只取低頻色會變得髒亂並拖出金色條紋。
   - 去掉燈光檢查原色後，發現生成的後裙甲其實是乾淨的紅板加金邊，偏白是背光照在漆面造成的。
   - 因此只用保邊的雙邊濾波去除斑點。
5. **其他。**
   - 在胸甲與裙甲範圍補上 313 個小破洞（3–48 條邊）。
   - 非金屬部分的粗糙度至少 0.52，清漆減為原來的 0.66 倍，減少漆面泛白。

**檢查**：完整版 742,091 面，檢視版 472,372 面；兩者都沒有近零面積三角形，所有 primitive 都有法線（[完整版](pass2/mesh-inspection.json)、[檢視版](pass2/preview-inspection.json)）。互動檢視器隨後改用 pass 3 模型。參數見[投影報告](pass2/projection-report.json)、[背甲外殼報告](pass2/back-plate-report.json)、[對齊參數](pass2/alignment.json)。

**下載**：[body-v2-pass2.glb](pass2/body-v2-pass2.glb)（92 MB，完整版）· [body-v2-pass2-preview.glb](pass2/body-v2-pass2-preview.glb)（58 MB，身體減面 45%）

**仍待處理**

- **後裙甲仍偏亮。** 這是漆面在背光下的反光，原色沒有問題。
- **背面是推測。** 背甲的橫片沿用胸前的設計。
- **立體細節不一定對位。** 前裙甲投上的綴繩，未必每一列都對準模型上的凸起。
- **手部與頸部尚未處理。** 手部還沒精修，頸部也還沒焊接。

```sh
# 在 repo 根目錄，Blender 4.3 bpy＋NumPy＋SciPy＋OpenCV 4.10（CPU）
python tools/fit_reference_silhouette.py --vertices <生成身體頂點.npy>
python tools/build_back_reference.py
python tools/project_reference.py
python tools/back_plate_shell.py
python tools/package_body_v2.py --model docs/experiments/future-sanada/body-v2/pass2/body-v2-pass2.glb --directory docs/experiments/future-sanada/body-v2/pass2 --name body-v2-pass2-preview
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2 --pass2
```

## 先看全身（第一版）

| 修整前：既有頭部＋原 1024 生成身體 | 本輪：1536 重新生成＋漆金材質＋同一顆頭 |
| --- | --- |
| ![修整前正面](before/front.png) | ![本輪正面](refined/front.png) |
| ![修整前斜側](before/three-quarter.png) | ![本輪斜側](refined/three-quarter.png) |
| ![修整前背面](before/back.png) | ![本輪背面](refined/back.png) |

| 部位 | 修整前 | 本輪 |
| --- | --- | --- |
| 頭頸接合 | ![](before/neck.png) | ![](refined/neck.png) |
| 胸甲、腰繩 | ![](before/torso.png) | ![](refined/torso.png) |
| 膝脛、靴 | ![](before/legs.png) | ![](refined/legs.png) |
| 手、前臂 | ![](before/hands.png) | ![](refined/hands.png) |
| 背甲 | ![](before/back-detail.png) | ![](refined/back-detail.png) |

[側面](refined/side.png) · [白模](refined/clay.png) · [胸前白模](refined/clay-torso.png) · [修整前白模](before/clay.png)

兩欄使用同一支 [render_body_v2.py](../../../../tools/render_body_v2.py)、相同鏡位與燈光（Blender 4.3／Cycles CPU、1000²、24 samples、降噪）。「修整前」是頭部研究留下的[靜態接合 GLB](../head-study/fitting/static-fit.glb)。

## 做了什麼

1. **重新生成，比較兩個 seed。** 相同參考圖，`1536_cascade`，seed 1615 與 7 各生成一次（原版為 `1024_cascade`）。原網格由 593 萬面提升到約 1,200 萬面，胸甲橫片、綴繩、膝蓋和脛甲的分隔都更明確。選用 **seed 7**：漆色較紅、胸前繩結與比例較接近參考圖。見 [兩個 seed 的原始輸出](selection/seeds-1615-vs-7.png)（上排 1615、下排 7，未修正材質）。
2. **改用封閉重網格匯出。** 原始網格本身有約 44.9 萬條邊界邊，甲片上會出現黑色裂縫。從快取的原資料重新匯出，開啟 TRELLIS.2 官方範例使用的 `remesh=True`（未重新推論），裂縫消失；代價是細小邊緣稍微變軟。見 [重網格前後對照](selection/remesh-cracks.png)（上：原匯出，下：重網格；右側為白模）。
3. **材質拆分（[trellis_body_materials.py](../../../../tools/trellis_body_materials.py)）。** 生成貼圖把赤漆設成約 0.51 的金屬度，因此整套像銅。依色相、明度與原金屬度把每個貼圖像素分成三類：
   - 赤漆：金屬度 0.51 → 0.016，粗糙度 0.44，色相拉回參考圖的約 4°，再加一層由遮罩控制的淡清漆。
   - 鍍金邊：生成時被畫成銅色的亮邊改為參考圖的老黃銅，保留金屬感。
   - 黑色內甲：低金屬、偏粗糙。

   參考圖的金色只出現在邊緣，背甲與小腿後側卻生成成整片銅板。用形態學開運算找出這些寬面積，改回赤漆，約占貼圖 0.6%。
4. **接回完成的頭部。** 頭部研究的檢視版頭部（37 個網格，含 Rocketbox 眼眶與六文錢）以對稱、修剪式 ICP 對齊生成身體自己的頭盔：縮放 0.2497，鹿角寬度 0.397 對 0.395，與身體的頭盔吻合。在銳利匯出上量測後，換算到重網格的座標系（[換算工具](../../../../tools/transfer_head_fit.py)、[參數](head-fit.json)）。舊頭部依區域及距離刪除，不使用方盒裁切，以免削掉衣領與肩甲頂部。

## 數據

| 項目 | 原版（1024） | 本輪（1536、seed 7） |
| --- | ---: | ---: |
| 原網格三角面 | 5,931,928 | 12,224,520 |
| 身體匯出三角面 | 148,107 | 566,543（重網格） |
| 全身（含頭部）三角面 | 見[接合檢查](../head-study/fitting/mesh-inspection.json) | 718,116 |
| 赤漆平均金屬度 | ~0.7 | 0.016 |
| 近零面積三角形 | 5 | 0 |

推論使用 Modal **H100 80GB**。Seed 7：載入 88.4 秒、推論 153.9 秒、儲存原資料 41.4 秒；重網格匯出 57.3 秒（另一次僅匯出的呼叫，總計 66.3 秒）。Seed 1615：載入 92.1 秒、推論 139.4 秒。不含容器啟動與下載。材質、接合與渲染全在本機 CPU。見 [seed 7 生成紀錄](generation.json) 與 [seed 1615 生成紀錄](generation-seed-1615.json)。

## 下載與檢查

| 檔案 | 用途 | 三角面 | 貼圖 |
| --- | --- | ---: | --- |
| [body-v2.glb](refined/body-v2.glb)（91 MB） | 完整版，後續修整基底 | 718,116 | 身體 4096² 色彩、2048² 金屬／粗糙、1024² 清漆遮罩 |
| [body-v2-preview.glb](refined/body-v2-preview.glb)（57 MB） | 身體減面 45%，檢視器使用 | 448,280 | ≤ 2048² |
| [互動檢視器 ZIP](viewer.zip)（70 MB） | 已改用 pass 9 模型；解壓後開啟 index.html | 698,349 | 內嵌 |

GitHub 檔案頁按 **Download raw file**。Blender 可直接匯入 GLB；`.blend` 太大，未放入 Git，可依下方指令重建。

- 幾何：[完整版](refined/mesh-inspection.json)、[檢視版](refined/preview-inspection.json)。0 個近零面積三角形，所有 primitive 都有法線，貼圖內嵌，清漆以 `KHR_materials_clearcoat` 匯出。
- 處理參數：[修整報告](refined/refinement-report.json)、[檢視版報告](refined/preview-report.json)、[渲染紀錄](refined/render-report.json)。
- 檢視器：[瀏覽器驗證](viewer-verification.json)、[桌面](viewer-1280.png)、[手機尺寸](viewer-390.png)。Chromium 軟體 WebGL，本機 HTTP 載入後切斷網路操作，無錯誤、無外部請求、無水平溢出。不是實機效能測試。

## 仍待處理

- **背面是單圖推測。** 背甲仍有幾塊暗斑和金色斑點。
- **手部未另行精修。** 手是 TRELLIS 原生，五指可辨認，但指縫和手背甲仍較糊。
- **頭身仍是搭接。** 頭部與身體是兩組零件，頸部未焊接；目前只做目視檢查，尚未做穿插計算，也未測動態。
- **材質為自動分類。** 依顏色自動判斷，少數邊界像素會判錯，未手繪磨損。
- **尚未進遊戲。** 還沒有骨架、權重、動作、LOD，也沒有替換線上遊戲。

## 重現

在 repo 根目錄執行。生成結果與原資料存於 Modal Volume `yukimura-trellis2-cache/results/future-sanada-body-v2/seed-{1615,7}/`，**未加入 Git**。

```sh
# 生成（GPU）：兩個 seed，原資料在匯出前保存
python tools/run_trellis.py --body-study --seeds 1615,7 --include-source
# 從快取原資料做封閉重網格匯出（GPU，不重新推論）
python tools/run_trellis.py --body-study --seeds 7 --export-only --remesh
# 只下載，不開 GPU
python tools/run_trellis.py --body-study --seeds 7 --download-only

# Blender 4.3 bpy＋NumPy 1.26＋SciPy 1.13（CPU）
python tools/fit_trellis_head_v2.py --body .tmp/body-v2/seed-7/body-high.glb --output .tmp/fit-high.json
python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-7/body-high.glb --no-head --output .tmp/v2-high   # 只為取得銳利匯出的座標系
python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-7/body-remesh.glb --no-head --output .tmp/v2-remesh
python tools/transfer_head_fit.py --fit .tmp/fit-high.json --source-report .tmp/v2-high/refinement-report.json --target-report .tmp/v2-remesh/refinement-report.json --output docs/experiments/future-sanada/body-v2/head-fit.json
python tools/refine_trellis_body_v2.py --body .tmp/body-v2/seed-7/body-remesh.glb
python tools/package_body_v2.py
python tools/render_body_v2.py --model docs/experiments/future-sanada/body-v2/refined/body-v2.glb --output docs/experiments/future-sanada/body-v2/refined --size 1000 --samples 24 --views front,three-quarter,side,back,clay,neck,torso,hands,legs,back-detail,clay-torso
python tools/inspect_trellis_glb.py --model docs/experiments/future-sanada/body-v2/refined/body-v2.glb --report docs/experiments/future-sanada/body-v2/refined/mesh-inspection.json
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/body-v2 --body-v2
CHROMIUM_PATH=<chromium> node tools/check_trellis_head_viewer.mjs --body-v2
```

`run_trellis.py` 也接受環境變數 `modal`／`modal_secret` 作為 Modal token。不要把金鑰寫進程式或 Git。生成使用與頭部研究相同的 Modal image 及 TRELLIS.2 commit `75fbf0183001ed9876c8dbb35de6b68552ee08bd`。

來源與授權沿用[上層說明](../README.md#來源與授權)。眼眶來源見[頭部研究](../head-study/README.md)與 [Rocketbox MIT 授權](../head-study/ROCKETBOX-LICENSE.txt)。檢視器 ZIP 內含 TRELLIS、Rocketbox 及 Babylon.js 授權。
