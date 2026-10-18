# 未來赤備：真田幸村 × TRELLIS.2

目標：先用 image gen 設計未來戰士版幸村，再用 Microsoft TRELLIS.2 由單張圖重建真實 3D 網格與 PBR 材質。這是獨立角色試作，不替換目前的 Pages 遊戲。

## 目前狀態

2D 參考圖已完成。Modal 登入與 TLS 已驗證，CUDA 執行環境已完成，且通過 **NVIDIA H100 80GB** 的 TRELLIS.2 匯入、CuMesh 網格與 CUDA 光柵化檢查；**尚未產生 GLB，沒有 3D 成果圖**。

2026-10-18 再次確認：Modal SDK 已使用環境提供的 `HTTPS_PROXY`，代理依賴已安裝，TLS 憑證驗證保持開啟，沒有 `NO_PROXY` 繞過。**2,192,353 bytes 的參考圖實際上傳已成功**，先前的 blob 403 已解除。

接續執行真正的生成工作時，Modal 回傳的派送網域 `input-plane.us-east.modal.com` 在代理 CONNECT 階段遭 `403 Forbidden`；遠端 `generate` 尚未啟動，沒有角色推論或 GLB。已保留現有網路設定並把此精確網域存入草稿。需在環境設定儲存、套用並發布；儲存草稿不代表執行環境已放行。不需要另架 proxy 或重填金鑰。

[本次派送失敗紀錄](https://modal.com/apps/clarence-chien/main/ap-soshP2pEPPy8xpY8mp93il)。所需網域：

- `input-plane.us-east.modal.com`（目前的阻擋點）

- `e29e5794c3a8abd52b1549c7703408b1.r2.cloudflarestorage.com`
- `modal-blobs.s3-accelerate.amazonaws.com`

[機器狀態紀錄](status.json) · [成功的 Modal 環境建置／GPU 檢查](https://modal.com/apps/clarence-chien/main/ap-kjWiE0TfzsHTOjb0R09Blg)。環境映像為 `im-CWPfod9BzDeCjqD07JU8Ui`，GPU 檢查所在建置步驟約 74.51 秒，這不是圖片轉 3D 的耗時。

Blender 渲染工具已用既有 v22 模型做 128px／1 sample／五視角的流程檢查；這些暫存圖不是 TRELLIS 成果，所以不放在此頁。新模型的幾何檢查與互動檢視器仍要等真實 GLB 產生後才能驗證。

## 輸入設計

![未來幸村參考圖](reference.png)

赤紅漆甲、金色六文錢與鹿角盔、覆面頬、黑色機械內骨架、少量橙色能源接縫。強壯成年武士比例，四肢稍微分開，沒有披風、武器或底座，以降低遮擋與薄片黏合。輸入為 image gen 產生的 **1024 × 1536 RGBA** 圖，已確認背景透明。

## 為什麼試 TRELLIS.2

官方模型為 4B 參數的 image-to-3D 系統，使用 O-Voxel 表示形狀與表面屬性，能輸出 base color、roughness、metallic、opacity 等 PBR 資料。對甲冑的輪廓、疊片與金屬質感有實用潛力。

官方列出 512³／1024³／1536³ 的生成解析度，這指空間表示解析度，不是螢幕畫素、貼圖尺寸或模型面數。README 的 H100 約 3／17／60 秒是作者推論基準，不包含本次首次安裝、權重下載、UV、材質烘焙、檔案傳輸與 Blender 渲染。

單張圖沒有背面真值；背面與被遮住的部分是生成推測。手指、鹿角尖端、甲片細縫仍需實測。模型也不會直接提供遊戲需要的骨架、權重、動作、碰撞或 LOD。

## 重現流程

本機為 CPU 環境，推論腳本使用 Modal 的 **單一 H100**，無常駐容器、無自動重試，單次函式上限 20 分鐘。首次 CUDA 編譯在 CPU 建置環境完成，最後會用 H100 檢查匯入、CuMesh 網格與 CUDA 光柵化；這個小型檢查不載入生成權重。推論使用的權重預計快取於 Modal Volume `yukimura-trellis2-cache`，不放進 Git。

```sh
/workspace/yukimura-tools/bin/python -m pip install 'modal[api-proxy-support]==1.6.1' 'truststore==0.10.5'
/workspace/yukimura-tools/bin/python tools/run_trellis.py
# 只建置環境、不啟動 GPU 推論：加上 --build-only
```

`tools/run_trellis.py` 先載入系統憑證信任並映射環境變數，再執行 Modal CLI。

腳本讀取環境既有 `modal_token_id`／`modal_token_secret` 並映射為 SDK 使用名稱。不要把金鑰放入檔案、前端或 Git。系統信任修正保留 TLS 憑證驗證；不使用 `verify=False`。目前 workspace 的 Hugging Face 連線受網路 allowlist 阻擋；推論模型將由正式 Modal 執行環境載入。

選定 TRELLIS.2 程式提交 `75fbf0183001ed9876c8dbb35de6b68552ee08bd`，PyTorch 2.6.0 / CUDA 12.4、xformers 0.0.29.post3。計畫設定 `1024_cascade`、seed 1615、150,000 面簡化目標、2048 貼圖；實際結果以生成紀錄為準。

模型生成成功後：

```sh
/workspace/yukimura-tools/render-env/bin/python tools/render_trellis_study.py
node tools/build_trellis_viewer.mjs
```

渲染使用 Blender 4.3.0 / Cycles CPU，直接匯入 GLB 幾何與材質。檢視器沿用專案的 Babylon.js，可旋轉、縮放、顯示白模與網格。

## 來源與授權

- [Microsoft TRELLIS.2 程式與說明](https://github.com/microsoft/TRELLIS.2)
- [論文](https://arxiv.org/abs/2512.14692) · [專案展示](https://microsoft.github.io/TRELLIS.2)
- [官方模型](https://huggingface.co/microsoft/TRELLIS.2-4B) · [官方操作範例](https://github.com/microsoft/TRELLIS.2/blob/75fbf0183001ed9876c8dbb35de6b68552ee08bd/example.py)
- TRELLIS.2 模型／程式：[MIT 授權副本](TRELLIS-LICENSE.txt)。nvdiffrast／nvdiffrec 等依賴另有各自授權，見官方 README。
- 角色參考圖：本次依使用者要求由 image gen 產生；六文錢、鹿角盔與真田赤備作為識別元素，未來機甲為架空設計。
