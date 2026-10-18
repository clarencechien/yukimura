# 未來幸村：TRELLIS 第一代替代試作

此路線使用 Microsoft 官方 `TRELLIS-image-large` 與其原本訓練搭配的 `dinov2_vitl14_reg`，不需要 DINOv3。它與 TRELLIS.2 是兩套不同的模型；沒有把 DINOv2 硬接入第二代權重。

輸入沿用 [同一張透明背景參考圖](../reference.png)。輸出獨立放在本目錄，不替換遊戲角色。

## 實測結果

**第一代已在 NVIDIA H100 80GB 成功生成模型與貼圖**，沒有使用 DINOv3 或 HF token。

| 項目 | 實測 |
| --- | --- |
| 原始網格 | 147,032 頂點／294,104 三角面 |
| GLB | 7,822,076 bytes，已存入 Modal Volume |
| 貼圖 | 2048 × 2048 烘焙色彩 |
| 首次權重載入 | 53.47 秒 |
| 模型推論 | 4.54 秒 |
| 網格處理、UV 與貼圖匯出 | 42.13 秒 |
| 函式內總時間 | 104.20 秒（不含環境建置、容器啟動與傳輸） |
| PyTorch 峰值配置 GPU 記憶體 | 9.85 GiB（非整張 GPU 的總占用） |

[Modal 執行紀錄](https://modal.com/apps/clarence-chien/main/ap-6QJzjDmxPNyuoWuQGe1SD3) · [生成紀錄](generation.json) · [驗證狀態](status.json)

**目前還沒有本機成果圖或可下載的 repo GLB。** 遠端匯出成功，函式回傳大檔時遇到代理 403；另查詢正式 Volume API，確認 GLB 存在且大小一致，但其下載端點 `clobber.modal-storage.com` 也回傳 proxy CONNECT 403。該精確網域已加入環境草稿，需儲存並發布使其生效。`generation.json` 目前取自遠端完成 Volume commit 後印出的紀錄；GLB 本機雜湊、幾何品質、Blender 多視角與網頁檢視器都尚未驗證，不能據此宣稱造型已接近插畫。

成果位置：Volume `yukimura-trellis2-cache` 下的 `results/future-sanada-trellis1/`。其中 GLB、生成報告、原始網格 NPZ 與 Gaussian PLY 已保存。工作已停止，沒有常駐 GPU。

放行後**只下載既有成果**，不要再次支付生成費用：

```sh
/workspace/yukimura-tools/bin/python tools/run_trellis1.py --download-only
/workspace/yukimura-tools/render-env/bin/python tools/inspect_trellis_glb.py --model docs/experiments/future-sanada/trellis1/future-sanada.glb --material-profile basecolor
/workspace/yukimura-tools/render-env/bin/python tools/render_trellis_study.py --model docs/experiments/future-sanada/trellis1/future-sanada.glb --output docs/experiments/future-sanada/trellis1
node tools/build_trellis_viewer.mjs docs/experiments/future-sanada/trellis1
```

下載工具使用官方 Volume API，先寫暫存檔並比對生成報告中的 SHA-256，再保留 GLB。`--download-only` 不呼叫預檢或生成函式；目前只通過語法檢查，端到端傳輸仍受網路阻擋。

## 執行

```sh
/workspace/yukimura-tools/bin/python tools/run_trellis1.py
```

重用已驗證的 Modal CUDA 映像 `im-CWPfod9BzDeCjqD07JU8Ui`，原建置定義在 `tools/trellis_modal.py`，可用 `tools/run_trellis.py --build-only` 重建。額外安裝第一代需要的 spconv、Kaolin、Gaussian rasterizer 與 UV／烘焙工具。

先在 CPU 檢查官方 checkpoint、DINOv2 權重的公開存取與套件匯入，通過後才呼叫單一 H100。GPU 函式上限 20 分鐘、無自動重試、沒有常駐部署。網格與 Gaussian 中間成果會先存入 Modal Volume，以免貼圖匯出失敗時重新生成。

這一代匯出的是烘焙色彩貼圖；不能視為 TRELLIS.2 的金屬度／粗糙度材質預測。單圖背面仍是推測，手指、鹿角、甲片需要實際檢查，產出不含骨架與動畫。

## 來源

- [Microsoft TRELLIS](https://github.com/microsoft/TRELLIS/tree/442aa1e1afb9014e80681d3bf604e8d728a86ee7) · [模型與 pipeline 設定](https://huggingface.co/microsoft/TRELLIS-image-large)
- [Meta DINOv2](https://github.com/facebookresearch/dinov2/tree/7764ea0f912e53c92e82eb78a2a1631e92725fc8)
- [TRELLIS MIT 授權](TRELLIS-LICENSE.txt)。FlexiCubes、Kaolin、mip-splatting、nvdiffrast 等依賴具有各自授權，依上游 README／LICENSE；不是整個工具鏈都由 MIT 涵蓋。
