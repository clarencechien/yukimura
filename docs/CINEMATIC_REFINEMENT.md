# 第一人稱試幀：模型與材質精修

這份衍生場景沿用前一版的三個相機位置，讓幾何、材質和光照改善可以直接比較。所有新增細節都是 Blender 網格及材質節點，沒有生成式修圖；這次專門輸出第 1／240 幀。

## 可見變更

- 護臂改為實際長度 34 cm，避免上一版把整段金屬拉伸成長筒。每臂 7 排、7 列的搭接甲片，另有捲邊、鉚釘、交叉繫繩、細線、掉漆與袖口褶皺。
- 依每個姿勢的槍軸建立雙手位置；四指分開彎曲，加入對握拇指、皮革縫線與六文錢手甲。手腕與護臂連接點在三個姿勢都接受幾何檢查。
- 家康現有高模的胸甲、肩甲與前裙甲，沿表面射線定位增加金屬邊飾、鉚釘和繫帶。
- 城樓增加陶瓦、瓦當、木梁、斗拱式支撐、欄杆、窗格與積雪；石牆改用不同大小的不規則石塊。造型屬大坂城意象的虛構場景，並非測繪復原。
- 修正大旗六文錢位於背面而被遮蔽的問題，加入雙面家紋和旗邊縫線。
- 碎石、稻草、碎木與箭矢集中分布於局部，雪面混合髒污與低矮雪堆。減少整齊排列和均勻散布的程序感。
- 軍勢使用四個從既有動畫取樣的共用網格，並變化位置、朝向、體型；不是替每名士兵建立昂貴的新骨架。
- 漆甲、皮革、布料、金屬、木頭與陶瓦各自有粗糙度及表面變化。調整冷暖光、降低遠景霧密度，以保留建築細節。

## 重建

沿用已驗證的 `tools/setup_cinema.sh` 環境；無新增依賴或網路需求。

```bash
# 必須先有上一版的 assets/cinema/first-person-lookdev.blend。
# 若需要重建基礎場景，依 docs/CINEMATIC_TEST.md 操作。
/workspace/yukimura-tools/render-env/bin/python tools/refine_first_person.py -- --width 1280 --samples 20 --frames 1,240
/workspace/yukimura-tools/render-env/bin/python tools/refine_first_person.py -- --width 3840 --samples 32 --frames 1,240 --save-scene
/workspace/yukimura-tools/render-env/bin/python tools/verify_cinema_refinement.py
python3 tools/cinema_refinement_review.py
```

輸出場景：`assets/cinema/first-person-refined.blend`。原圖、實測耗時、驗證紀錄和前後對照頁：`renders/first-person-refined/`。原始來源模型與前一版 Blender 場景保留。

## 評估範圍

兩張正式 3840×2160、RGB 16-bit PNG 已完成並開啟檢查。第 1 幀含降噪／寫檔 419.41 秒，第 240 幀 515.60 秒；新增細節網格共 978,358 三角面（未計修改器產生的額外面）。保存的場景重新開啟通過，6 張圖片已打包，沒有缺失外部圖片；三個姿勢的雙手連接點誤差都小於 0.00001 m。

前後對照頁已經以 Chromium 實際開啟：四張原版／精修 4K 圖載入成功，方向鍵可控制分隔線，390 px 手機寬度沒有水平溢出，也沒有 JavaScript 錯誤。`gallery-check.json` 保存驗證結果。遊戲 `src`、`public` 和 `assets/source` 的差異檢查通過。

這次改善細節密度、物件比例與材質辨識度，並不代表已達到設定插畫或 3A 電影的完成品質。手部仍是程序建模，角色臉部與布料需要更細的造型設計；三個姿勢仍不構成完整 10 秒動畫。

新增幾何以離線渲染為目標，沒有直接塞入網頁遊戲。遊戲版本仍需分離可共用部件、烘焙法線／粗糙度、製作 LOD，並實測手機效能。

渲染使用本機 4 CPU 執行緒、Cycles、AgX 和 OpenImageDenoise。16-bit PNG 是套用顯示轉換後的輸出，並非線性 HDR EXR。這次沒有使用 Modal GPU，沒有 GPU 時間或費用的實測數據。
