# v17：真人頭臉接入兩位主將

幸村、家康現在使用由 Microsoft Rocketbox Male Adult 10 改裝的頭臉，取代 v16 的簡化皮膚球、面甲、黑色眼條及金屬鬍鬚。遊戲仍是 Babylon.js；本次沒有付費素材或 Modal 作業。

## 造型與共用

- 共用同一頭部拓撲、UV 與 1,024² 皮膚法線。兩人有獨立膚色貼圖，分別處理短鬚、灰鬚、眼下與臉部年齡線索。
- 幸村採較窄的下顎；家康加寬下顎、調整頰部位置。這是本作的藝術改裝，不宣稱還原歷史人物真實容貌，也尚未達到插畫級完整人物雕刻。
- 取代原面甲以露出五官；保留原有赤備鹿角、六文錢、家康黑金頭盔和大型前立。新增共用的薄內襯、依臉部表面貼合的下顎繫帶，沿用既有皮革材質。
- 皮膚使用獨立材質，金屬度為零；`finishMaterials` 不對皮膚添加鍛造敲紋、布料 detail map 或漆面 clear coat。

## 骨架與遊戲整合

新頭部綁到現有 `body.head`，頸部底端漸變到 `body.spine02`。整體維持 92 骨，沒有帶入 Rocketbox 的另一套 80 骨架。額頭／顱骨和頭盔使用同一個變形骨；頸部可在頭與軀幹之間過渡。

同一頭部形體先以來源的 brow-down 形變做輕度靜態表情，再提取網格。沒有新增即時表情／口型系統。幸村原有八個戰鬥動作、家康六個動作繼續使用；家康皮膚是第五個材質區塊，仍跟其他甲冑區塊共用同一個 GPU 骨骼動畫畫格。小兵網格與動畫維持原樣。

來源頭部 1,707 個頂點；實際 GLB 頂點數可能因 UV、法線及材質拆分略有差異。預算仍維持每位主將低於 80,000 三角面、幾何加動畫 GLB 低於 6,000,000 bytes（不含外部共享 PNG）。本次新增三張共享目錄中的 1,024² PNG：一張兩位共用的皮膚法線、兩張角色膚色圖；全場實際使用 14 張模型 PNG。所有尺寸以 `public/models/manifest.json` 為準。

## 可重建來源與授權

- [官方來源與 MIT 授權](https://github.com/microsoft/Microsoft-Rocketbox/tree/0943055db6ec570bcef9f2c8b41c9e5467c808f9)。原始下載版本與每檔 SHA-256 已記錄於 `assets/research/character-candidates/sources.json`。
- 本步直接使用已提交的 `public/review/candidates/rocketbox.glb`，SHA-256：`142e74c396085ae990391803f28d178b2f41266e153f454d23ebebfe7f51e6e7`。腳本會驗證，避免候選檔被替換後默默產生不同結果。
- 修改後的 GLB、共享皮膚貼圖與可編輯 `.blend` 依 MIT 保留 Microsoft copyright；公開授權存於 `public/models/LICENSE-Rocketbox.txt`。
- 骨架、手臂仍使用先前的 MPFB CC0 資產；甲冑為本專案既有自製內容。本次未將 Cyber Samurai 的科幻甲冑加入角色。

```bash
# 既有 Blender 4.3 環境；讀取 v16 兩個 -detail.blend，不重烘整套鎧甲
npm run models:faces
# 同樣可以使用已安裝 bpy 的 Python 執行 refine_commander_faces.py
/workspace/yukimura-tools/render-env/bin/python tools/validate_face_motion.py
# Vite 開在 5180 後擷取；前版快照放 .tmp/face-v17/before/（含 shared 貼圖）
node tools/capture-faces.mjs
python3 tools/face_gallery.py
```

可編輯成品：`assets/optimized/commanders/yukimura-face.blend`、`ieyasu-face.blend`。完整 `models`／`models:rigs`／`models:physique`／`models:details` 重建路徑皆串接本步，避免重建後退回 v16。

## 驗證範圍

- `validate_face_motion.py` 對全部 14 個動作各取樣 13 幀，檢查頭部頂點有限值，以及顱骨相對頭盔使用的骨骼變換是否漂移。這是綁定與動作檢查，**不等於完整衣甲碰撞模擬**。
- `human-head.test.mjs` 檢查臉部非金屬材質、共用法線、單一骨架、頸部混合權重與頭部隨骨。既有模型、手腕、握槍與戰鬥測試繼續執行。
- Babylon.js 比較圖採相同相機、光照與 clip 時間，檢查正面、側面、全身、突刺、跑步，以及皮膚未誤用鍛造細節／漆面。機器以 Chromium SwiftShader 驗證，不能當成手機硬體 FPS。
- 家康 GPU 實例測試包含第五個皮膚區塊；Pages 測試包含新增頁面、圖片、授權與相對網址，避免再次出現圖片斷鏈。

仍可精修的部分：更具個性的武將面部雕刻、細緻髮鬚、自然肩甲關節與手腕比例、材質磨損與插畫光影。目前不宣稱已完成電影級角色，也未引入昂貴的皮膚次表面散射後處理。
