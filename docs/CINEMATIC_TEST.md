# 第一人稱影片試幀

這是 10 秒影片的三個構圖／材質試拍點，不是已完成的動畫，也不是遊戲即時畫面的錄影。沿用 `assets/source/samurai-kit.blend` 的雕刻手部、長槍與黑金家康；另外建立第一人稱赤紅護臂和袖口，連接鏡頭外的肩膀。軍隊使用共用網格，場景為離線試拍用的程序雪地、城樓、防柵、旗幟、餘燼和霧。

- 第 1 幀：近景持槍，檢查赤紅漆甲、手套與槍身。
- 第 120 幀：向本陣推進，檢查武器與軍勢的構圖。
- 第 240 幀：面對黑金家康，檢查人物尺度與景深。

鏡頭使用 22／25 mm、AgX 調色、Cycles CPU 光線追蹤及 OpenImageDenoise。4K 輸出為 3840×2160、RGB 16-bit PNG、32 samples、4 CPU 執行緒。原始手部高模及家康高模的面數、逐張實測耗時、場景準備時間記錄於 `renders/first-person/render-3840.json`；不把未出鏡的幸村整身高模計入第一人稱面數。程序材質並非新烘焙的 8K 人物貼圖。

## 開啟及重建

可直接開啟 `assets/cinema/first-person-lookdev.blend`，使用相機視角並跳到 1／120／240 幀。相關圖片已打包，不依賴外部 HDRI 或圖片服務。`scene-check.json` 記錄重新開啟場景、檢查缺失貼圖與三個相機位置的結果。

```bash
bash tools/setup_cinema.sh
/workspace/yukimura-tools/render-env/bin/python tools/render_first_person.py -- --width 960 --samples 12 --frames 1,120,240
/workspace/yukimura-tools/render-env/bin/python tools/render_first_person.py -- --width 3840 --samples 32 --frames 1,120,240 --save-scene
python3 tools/cinema_review.py
```

最後一個命令檢查三張 PNG 的實際解析度與位元深度，產生 `renders/first-person/index.html` 檢視頁及含檔案雜湊、耗時的 `review.json`。需要先完成三張 4K 渲染。

腳本只讀取遊戲來源模型，不覆寫它，也不修改或部署網頁遊戲。Python 3.11.17、官方 `bpy==4.3.0` 與 `numpy==1.26.4` 安裝於 workspace 內；保留 TLS 驗證。此環境的系統 Blender 4.3.2 未編入 OpenImageDenoise，試渲染確認後改用官方 bpy。`download.blender.org` 被目前網路規則阻擋，官方 PyPI 套件可正常安裝，無須改動允許網域。

## 本次驗證與限制

三張 3840×2160、RGB 16-bit PNG 已完成並逐張開啟檢查；檔頭規格及 SHA-256 記錄於 `review.json`。CPU 實測含降噪和寫檔：第 1 幀 408.37 秒、第 120 幀 458.80 秒、第 240 幀 518.09 秒，場景準備 9.47 秒。同一台機器渲染 240 張相似複雜度畫面的線性估算約 30.78 小時，並非完整影片的實測耗時。場景重新開啟通過，三個鏡頭位置不同，沒有缺失外部圖片；遊戲來源模型、`src` 及 `public` 未被這次製作改動。

先以 960×540 試拍，修正未入鏡的手部、懸空袖口、雪泥方格邊界、過亮泥面和穿插地表的薄片積水；重新建立連續材質混合與第一人稱護臂。再渲染完整 4K 試幀，沒有生成式修圖或放大補細節。

這次沒有完成 240 幀的動作設計、連續步態、布料模擬、動態風雪或 motion blur。三個時間點之間只有構圖／姿勢插值，不應直接把這份場景的整段時間線當成完成的影片。手部解剖、握槍接觸、兵士和城樓造型仍可精修，不能把 4K 解析度或百萬面數當成已達 3A 宣傳片品質的證據。

Modal 使用既有環境綁定測試連線，35 秒逾時，未執行遠端渲染或付費 GPU 工作。逐幀耗時是這台 CPU 的結果；若估算 24 fps、240 幀，須註明只是相似複雜度下的線性估算，不是 Modal 報價，也不含動態模糊等新增效果。
