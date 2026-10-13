# 開源手部與籠手試作

本次實際使用 MPFB／MakeHuman 的 CC0 人體網格、骨架定義與 skin weights，抽出右手及前臂，製作握槍白模和赤備籠手近照。沒有使用付費資產、付費生成服務或 Modal GPU；沒有把圖片生成結果當成 3D 渲染。

## 來源與重用

- 上游：[makehumancommunity/mpfb2](https://github.com/makehumancommunity/mpfb2)
- 固定 commit：`d0a32e57a7f915cb2f2b95410e2117648c7bbb7e`
- 原始資料、授權與 SHA-256：`assets/vendor/mpfb/`
- 隨附網格、rig 與 weights 為 CC0；程式碼本身的 GPLv3 與素材授權分開。本次直接讀取素材，沒有匯入 MPFB addon 程式碼。
- 可編輯場景：`assets/cinema/open-hand-study.blend`
- 原圖／檢視頁／驗證：`renders/open-hand/`

## 做了什麼

1. 保留原始人體網格的連續手掌、手指與 UV，沿來源 vertex index 重用權重。骨架的關節位置依原始 OBJ helper／vertex data 重新求出，沒有直接套用不同身形的 default_position。
2. 把手部轉至局部座標，保留 22 根骨骼，其中 15 根為五指的三節骨架。前臂裁切處保留權重，並讓曲面細分在骨架變形後執行。
3. 槍桿直徑為 28 mm，斜跨掌面。依各指長度求彎曲角度；拇指另做對握。辨識 MPFB 局部座標的掌面方向後修正彎曲方向。
4. 握槍姿勢使用 Blender Shrinkwrap 的 OUTSIDE 模式修正少量表面穿插。驗證記錄最低頂點淨距，不把頂點測試宣稱為完整碰撞檢測。
5. 以手臂截面擬合平順曲面，製作七片有厚度的篠式甲片、14 個穿繩孔、金屬孔緣、繫繩、袖口和布料內襯。這是設計試作，並非特定歷史文物的精確復原。
6. 沿手背表面建立六文錢手甲；皮革指套加入逐節跟隨指骨的縫線。甲片與縫線物件連到對應骨骼，便於後續重用。

## 檢視方式

- `open`：展開手白模，確認原始連續形體。
- `grip`／`palm`：握槍手背及掌面白模。
- `beauty`／`beauty-palm`：同一手部與燈光下的材質／籠手版本。
- Blender 第 1 幀為展開，第 24 幀為握槍。中間不是已完成、通過驗收的抓取動畫。

## 重建

沿用既有的 `bpy==4.3.0`、`numpy==1.26.4` 環境，沒有新增依賴。來源資料已存進專案，建模時驗證雜湊，不需每次聯網下載。

```bash
bash tools/setup_cinema.sh
/workspace/yukimura-tools/render-env/bin/python tools/open_hand_study.py -- --width 2560 --samples 48 --views open,grip,palm,beauty,beauty-palm --save
/workspace/yukimura-tools/render-env/bin/python tools/verify_open_hand.py
python3 tools/open_hand_review.py
```

## 本次輸出與驗證

五張原圖均已完成：2560 × 2048、16-bit RGBA PNG，Cycles 48 samples、CPU 四執行緒與 OIDN 降噪。單張耗時 56.69–75.45 秒，五張合計 345.06 秒。解析度、格式、檔案雜湊與檢視頁連結皆已檢查，詳細記錄見 `renders/open-hand/review.json`。

重新開啟 `.blend` 後，確認 22 根骨骼、1,809 個有權重的基底頂點、345 個依附骨骼的甲片／縫線物件，以及展開和握槍姿勢的實際變形。握槍狀態的最低頂點淨距約為 −0.000129 mm，在數值容許誤差內；這不代表全部三角面或動畫過程都沒有穿插。

最終材質圖已目視檢查：手部輪廓與甲片層次可辨，但拇指根部和皮革受壓皺褶仍偏簡化；這是後續需要雕刻與修正形變的重點。

## 後續限制

這次證明開源人體基底可以提供比管線拼接更連續的手部結構與可變形骨架；仍不是電影級掃描手或完整雕刻作品。手指接觸、關節形變、皮革細節與實際握槍動作仍可進一步修正。

接觸修正目前依賴 Blender modifier。若要放進 Babylon.js，還需把它轉成可匯出的 corrective shape keys 或調整骨架／網格，重新整理手部 UV、烘焙 PBR 材質、製作 LOD，並做 GLB 回匯及遊戲測試。本次沒有直接修改或部署遊戲資產。
