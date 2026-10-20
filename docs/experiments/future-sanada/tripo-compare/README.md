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

## 狀態

TRELLIS 端的算圖在 [trellis/](trellis/)。Tripo 端等 API 金鑰：環境變數 `tripo` 目前是 client ID（`tcli_…`），API 需要 secret key（`tsk_…`）。
