# 手部與鎧甲精修：skill 與替代方法調查

## 結論

優先採用「有解剖結構的人體基礎網格 + 依實物構造建模 + 參考圖驗收」，再處理雕刻與材質。Skill 可以改善流程，但不等同於精細模型、藝術家雕刻或解剖資料。此次僅查詢與閱讀來源，沒有安裝外部 skill、addon，或執行付費服務。

目前 cloud skill catalog 只有 `cloud-environment-onboarding:setup`，executor catalog 沒有其他 skill。以下為外部候選，尚未在這個環境驗證執行。

## 候選評估

### blender-game-skills / blender-image-to-3d — 最適合做主要流程

- [SKILL.md](https://github.com/majidmanzarpour/blender-game-skills/blob/main/skills/blender-image-to-3d/SKILL.md)
- 閱讀到的最新 commit：`f0ef29385a03de139957e6f700b801cdc00b7e29`，MIT。
- 包含參考相機校準、白模與輪廓比對、尺寸檢查、烘焙、GLB/FBX 匯出和重新匯入驗證腳本。
- 要求先確認比例與形體，再做細節；這比只看原版／新版是否更華麗，更能檢查是否接近設定圖。
- README 表示 Blender 4.2+，只聲明在 Claude Code 測試；目前 Blender 4.3 符合其版本要求，但 Codex／本環境執行仍待驗證。
- 它仍由 agent 編寫 bpy 建模，不包含精細手部資產，也不是影像轉 3D 的生成模型。輪廓 IoU 不能取代對關節、拇指對握與掌部體積的解剖檢查。

### arjun988/blender-skills — 可挑選部分做輔助

- [repository](https://github.com/arjun988/blender-skills)
- 閱讀到的最新 commit：`8f778d2405a214b508d4c7d80742be8e43acdd52`，MIT。
- 已閱讀 `character-artist`、`sculpting`、`hard-surface`、`painterly-style`。
- 有用內容：比例先行、變形區拓撲、甲片製造邏輯、部件分離、分層雕刻、法線烘焙。
- 限制：多為一般指南，沒有解剖手部模型；`painterly-style` 很簡短。部分雕刻建議需校正，例如 Multires 與保留基礎拓撲的描述、非 Blender 標準筆刷命名。不能把「AAA」標籤當成實際品質保證。

### MPFB / MakeHuman — 最值得先試的免費模型基底

- [官方 repository](https://github.com/makehumancommunity/mpfb2)
- [官方授權說明](https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md)
- 閱讀到的最新 commit：`d0a32e57a7f915cb2f2b95410e2117648c7bbb7e`。
- README 要求 Blender 4.2+。已確認 repository 含 `src/mpfb/data/3dobjs/base.obj`，及 standard rig 的手腕、掌骨、雙手各五指三節骨架定義。
- 程式碼 GPLv3；隨附網格、rig、材質等資產為 CC0，官方授權說明表示不主張生成輸出權利。外加的第三方素材仍須看其個別授權。
- 建議提取可共用的前臂與手部，以實際槍桿直徑調整指骨，再由手部表面製作手套，補上厚度、縫線及受壓褶皺。
- 它是人體基底，不是完成的電影級手部；仍需調整關節形狀、掌部肌肉、指節比例與握姿。這次尚未匯入或渲染該模型。

### Blender MCP — 操作與回饋工具

- [官方專案 README](https://github.com/ahujasid/blender-mcp)
- 閱讀到的最新 commit：`7a0373ec9199183cb460068c4f96aed9c579fb4f`。
- 提供 live Blender Python、視窗截圖、資產搜尋／匯入及外部 3D 生成整合。
- 我們目前已可直接執行 bpy。MCP 的增益主要在互動檢視與資產取得，單獨安裝不會修正手部解剖或甲片結構。

### 其他路線

- **授權清楚的專業手部／鎧甲資產或掃描**：若付費可以接受，通常比從零生成更快取得可信形體。手部要看是否有可變形拓撲、指骨及握拳範例；掃描本身不代表可動畫。未選定或購買任何付費資產。
- **博物館實物參考**：[Met Open Access](https://github.com/metmuseum/openaccess) 可用於找鎧甲結構資料。資料集 CC0 不等於每張館藏圖片都是 CC0；應逐件確認圖片標示，並記錄年代，避免把後期鎧甲直接當成 1614 年史實。
- **Hunyuan3D／Rodin 類生成模型**：[Hunyuan3D 2.0](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) 將形狀與紋理生成分開，也能替既有模型生成紋理。可作為甲冑概念或表面製作的實驗，但不能預設輸出符合手指解剖、關節拓撲或精確握槍接觸。下載權重、授權、GPU 成本需按所選版本確認；本次未執行。

## 現有模型為何仍有玩具感

`tools/refine_first_person.py` 的手掌以橢球、手指以掃掠管線建立，雖然已分指並對齊槍軸，仍欠缺掌骨、指關節、拇指根部及受壓形變的連續結構。

`tools/hero_highpoly.py` 的大量細節來自 SIMPLE 細分、倒角與程序位移。這增加了網格密度和表面起伏，不能等同於以解剖與實物構造為依據的雕刻。

鎧甲需要改善甲片搭接、開孔、繩索真正穿過孔洞的路徑、內襯和不同材質的接觸。漆面磨損應跟隨碰撞與摩擦位置；大面積隨機噪聲、同樣的亮邊或過粗繩線容易顯得像玩具。相關修正不需要先擴充 Modal 算力。

## 建議的下一個小型驗證

1. 只處理一隻握槍手與一套籠手；保留現有戰場，先避免整場重渲染的成本。
2. 匯入 MPFB 人手基底，檢查正面、側面、掌面比例。保留五指骨架，加入握槍姿勢及必要的 corrective shape keys。
3. 先驗收白模：拇指能對握、手指節數及彎曲方向正確、指腹貼住槍桿、無明顯穿插或懸空。白模不通過就不加更多微細節。
4. 依選定實物參考製作籠手／手甲：甲片厚度、搭接、孔洞、繫繩和內襯分離；尺寸未有依據的部分明確標為推定。
5. 由真實接觸位置安排磨損，製作皮革粗糙度、布料織紋、漆面與裸露金屬材質；以中性燈光檢查，再套回赤紅插畫美術方向。
6. 輸出固定相機的白模、材質近景、握姿對照及遊戲尺寸縮圖；通過後再做低模、法線／粗糙度烘焙、GLB 回匯與 Babylon.js 檢查。

## 查詢範圍與限制

已讀取可用 skill catalog、上述 GitHub 官方／作者 repository 及相關授權／骨架文件。`skills.sh`、MakeHuman 靜態文件站、Blender 文件站、Poly Haven 與 ambientCG 網站在目前環境回傳網路規則 403，因此沒有宣稱完整搜尋所有 marketplace，也沒有驗證這些網站的下載流程。可讀取的 GitHub 來源已提供足夠資訊比較候選；本次沒有變更網路政策或環境設定。
