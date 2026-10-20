# 未來赤備：Tripo 與 TRELLIS.2 1536 比較

同一張參考圖（[reference.png](../reference.png)，SHA-256 `c84b2864…`，與 body v2 的 TRELLIS.2 輸入完全相同），分別交給 Tripo API 與 TRELLIS.2 1536 cascade，比較未經任何後製的原始輸出。

## 比較方式

| | TRELLIS.2 | Tripo |
| --- | --- | --- |
| 模型 | `microsoft/TRELLIS.2-4B`，1536 cascade，seed 7 | 見下方三種設定 |
| 輸出 | body v2 的原始封閉重網格匯出（`body-remesh.glb`，未經 pass 2–9 精修） | API 回傳的 GLB，未修改 |
| 算圖 | 同一支 [render_body_v2.py](../../../../tools/render_body_v2.py)、同一組攝影機與燈光 | 同左 |

Tripo 的三種設定（[tripo_generate.py](../../../../tools/tripo_generate.py)）：

| 名稱 | 設定 | 用途 |
| --- | --- | --- |
| `ultra` | `v3.1-20260211`、Ultra 幾何（`geometry_quality=detailed`）、PBR、`texture_quality=detailed` | 和 TRELLIS 比最高品質 |
| `parts` | `v3.1-20260211`、`generate_parts=true`（只有幾何，Tripo 不允許與貼圖同開） | 看它能否自動拆件，方便綁骨 |
| `game` | `P2-20260801` 低面數、上限 45,000 面、PBR | 看能否直接符合遊戲武將上限（9 萬面、7 MB） |

## 結果

Tripo 原始輸出在 [tripo/](tripo/)（每種設定一個 GLB、Tripo 的預覽圖與任務紀錄）。Tripo 匯出時正面朝 +X，算圖前轉成和 TRELLIS 相同的 −Y 朝前，其餘未改動。

**全身**（左起：正面、斜側、側面、背面、白模；上：TRELLIS.2 1536，中：Tripo ultra，下：Tripo game）

![](compare-full.jpg)

**近拍**（左起：胸部、胸部白模、手、腿、背）

![](compare-detail.jpg)

**Tripo 自動拆件**（`parts`，每個顏色是一件；共 11 件：頭盔、胴＋草摺、左右袖、左右臂、左右大腿、左右小腿與靴等）

![](compare-parts.jpg)

| | TRELLIS.2 1536 | Tripo ultra | Tripo game（P2） | Tripo parts |
| --- | ---: | ---: | ---: | ---: |
| 三角面 | 571,463 | 1,884,017 | 46,449 | 1,491,486（11 件） |
| 檔案 | 73.5 MB | 69.6 MB | 15.0 MB | 41.2 MB |
| 貼圖 | 2 張 4096² | 3 張 4096²（PBR） | 3 張 4096²（PBR） | 無 |
| 生成時間 | 約 4 分鐘推論＋1.5 分鐘載入（H100） | 2 分鐘 | 2 分鐘 | 1 分鐘 |
| 費用 | Modal GPU 時間 | 60 點（0.6 美元） | 120 點（1.2 美元） | 40 點（0.4 美元） |

## 360 度轉台影片

[turntable-trellis-vs-tripo-1080p.mp4](turntable-trellis-vs-tripo-1080p.mp4)：1920×1080、30 fps、24 秒。左 TRELLIS.2 1536，右 Tripo v3.1 Ultra；前 12 秒全身轉一圈，後 12 秒上半身近拍轉一圈。兩邊都縮放到 2 m 高、在同一組固定燈光下原地旋轉，所以每個角度的光線完全相同。

在 Modal L4 GPU 上以 Blender 4.3 Cycles 算圖（96 samples、OptiX 降噪，每格約 5 秒，1,440 格分 12 台平行），本機以 ffmpeg 合成。重現：

```sh
python tools/run_trellis.py --turntable --left .tmp/body-v2/seed-7/body-remesh.glb --right .tmp/tripo-ultra-ny.glb --output .tmp/turntable
tools/turntable_compose.sh .tmp/turntable docs/experiments/future-sanada/tripo-compare/turntable-trellis-vs-tripo-1080p.mp4 "TRELLIS.2 1536" "Tripo v3.1 Ultra"
```

（`.tmp/tripo-ultra-ny.glb` 是 Tripo ultra 轉成 −Y 朝前的副本。）

## 差別

- **甲片幾何**：Tripo 的胴、草摺、袖都是水平、等距、邊緣銳利的甲片，綴繩是立體的；TRELLIS 的甲片邊緣軟、有凹凸，白模上可見表面起伏。這正是 body v2 花了 pass 2–9 想修的部分。
- **繩結與流蘇**：Tripo 的頸前繩結、腰繩結、流蘇都是乾淨的立體造型；TRELLIS 的繩子糊在身上。
- **背面**：原圖沒有背面。Tripo 推出一個合理的背甲（水平甲片、綴繩、背後的繩）；TRELLIS 的背面是一塊暗褐色的平板。
- **貼圖**：Tripo 的赤漆與金邊乾淨、接近原圖；TRELLIS 偏暗、偏褐，有雜斑。
- **對稱與比例**：Tripo 左右對稱、站姿端正；TRELLIS 略側轉，承襲原圖的 3/4 視角。
- **遊戲版**：Tripo game 只有 46,449 面，就已低於遊戲武將上限（9 萬面），外觀仍保有大部分細節，背甲則簡化成平滑的紅板。檔案 15 MB 仍超過 7 MB，主要是三張 4K 貼圖；縮成 1–2K 即可達標。
- **拆件**：Tripo 能直接把角色分成頭盔、胴、袖、手臂、腿、靴等 11 件幾何，可以每件綁一根骨頭；但拆件模式不能同時產生貼圖，要另外把 ultra 的貼圖轉印過去。
- **TRELLIS 的優勢**：開源（MIT）、可自架，沒有額度與使用條款限制；Tripo 是付費服務。

**結論**：同一張圖，Tripo ultra 的原始輸出就已經優於 TRELLIS.2 1536 加上 body v2 九輪精修的結果；遊戲版也只需要縮小貼圖。若要繼續做這個角色，建議改走 Tripo：以 ultra 作為影片版，以 game 作為遊戲版，再用 Tripo 的自動綁骨或拆件結果綁到遊戲骨架。
