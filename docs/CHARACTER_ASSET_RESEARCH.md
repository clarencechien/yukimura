# 寫實人物與甲冑資源試載

本次改查「已完成的人物資產」，並實際匯入 Blender、輸出 GLB 和渲染。成果在 `/review/candidates/`，目前屬於素材選型，尚未替換幸村、家康或小兵。沒有購買素材，也沒有啟動 Modal。

## 選型結果

| 資源 | 已核對的授權 | 實際用途與決定 |
| --- | --- | --- |
| [Microsoft Rocketbox / Male Adult 10](https://github.com/microsoft/Microsoft-Rocketbox/tree/0943055db6ec570bcef9f2c8b41c9e5467c808f9/Assets/Avatars/Adults/Male_Adult_10) | 官方 [MIT](https://github.com/microsoft/Microsoft-Rocketbox/blob/0943055db6ec570bcef9f2c8b41c9e5467c808f9/LICENSE.md)，保留 copyright／license；官方 README 明確記錄 2020 年改為 MIT | **已下載、試載。** 6,732 三角面，80 骨骼，175 個表情形變。可作眼皮、鼻翼、嘴唇、耳朵、手部與骨架的底材。現代衣服與髮型須換掉，並重新做武將年齡、皮膚和神態；它是較早期的寫實遊戲人物，不能稱為現代 AAA 完成品。 |
| [Cyber Samurai — KhoaMinh](https://sketchfab.com/3d-models/cyber-samurai-26ccafaddb2745ceb56ae5cfc65bfed5) | 公開鏡像附帶的[逐件授權](https://github.com/Tresjs/assets/blob/2e771aed0124c3af8fb2449a4c59b4ad08d0cc5f/models/gltf/cyber-samurai/license.txt)為 CC BY 4.0；允許改作／商用，須署名、連結授權、說明修改 | **已下載、試載。** glTF 原始索引約 20.9 萬三角面、5 材質、無骨架／動畫。能研究板件厚度、搭接、衣褶及多組 PBR 貼圖，但機械身體、銀色胸甲不符合大坂赤備，因此不直接採用整套造型。能改作不代表已適合本作。 |
| [PBR Kabuto — LeahLindner](https://sketchfab.com/3d-models/pbr-kabuto-samurai-helmet-13b3ab49b6bd4247be36b54ba1a56d8a) | [隨附逐件授權](https://github.com/emilien3/ProjetInfographie/blob/4bee48c017413ac4d190df5a6eda935937b45abb/object/pbr_kabuto_samurai_helmet/license.txt)：CC BY-NC-ND 4.0 | **排除遊戲改裝。** 非商用且不得分享改作，不能因別人的程式 repository 開放就視為可改的遊戲素材。未納入輸出。 |
| [Quill — Samurai / Nick Ladd](https://sketchfab.com/3d-models/quill-samurai-c863df6299f14646ba3b63a3de4bb5f2) | [隨附授權](https://github.com/Opengundumstyle/samurai-3d-model/blob/main/license.txt)：Sketchfab Editorial | **排除遊戲素材。** Editorial 不是一般遊戲商用授權。未納入輸出。 |
| [MB-Lab](https://github.com/animate1978/MB-Lab/blob/master/license.txt) | 程式 GPL；資料及預設輸出 AGPL，並非 CC0 | 本作已有 MPFB CC0 人體，這次不額外引入另一套基本人體生成器及不同的授權要求。 |

Cyber Samurai 的原始 Sketchfab 頁面目前無法從環境開啟；授權依據是可存取的公開鏡像內逐件 `license.txt`，不是主站當下的重新確認。兩個可試載候選均固定 repository commit，原始下載檔逐一驗證 Git blob SHA-1，並記錄 SHA-256；詳見 `assets/research/character-candidates/sources.json`。

## 實際改動和驗證範圍

- 修正 Rocketbox FBX 內指向作者 Windows 磁碟的貼圖路徑；沿用原本 skin weights、UV、normal 與 specular 資料。沒有把 specular 圖冒充 metallic／roughness 圖。
- 兩個模型等比例縮放到 1.85 m 檢視高度。預覽貼圖長邊上限 1,024 px；沒有增加面數或用 AI 補圖。
- 原始 FBX 保留全部 175 表情；可編輯研究 `.blend` 也保留完整表情。網頁 GLB 僅保留選定的眉頭、眨眼、張口目標；它不是已完成的戰鬥動畫包。
- 實際匯出面數、貼圖尺寸、骨骼／表情和檔案大小寫入 `public/review/candidates/validation.json`。glTF 匯入重建多邊形後再匯出，退化面處理可能使三角面數與原始索引略有差異。
- Blender 圖片：Cycles CPU、32 samples、去噪、1,000 × 1,200，中性攝影棚照明。這些是下載模型的實際 3D 渲染，不是生成式插畫，也不是已上線武將的改裝成果。
- GPU／手機效能尚不能由離線渲染推論。Cyber Samurai 仍無骨架、無 LOD；要投入戰鬥必須減面、重拓撲、拆件綁骨、碰撞與動作測試。

## 下一個可共用製作單位

1. **先完成一個武將頭部。** 以 Rocketbox 的頭臉與表情拓撲為候選，重塑成熟臉型、眼眶、顴骨、鬍鬚；移除現代髮片，做頭盔遮擋與頸部接縫。用同一近景相機比較現有模型，通過後再接戰鬥骨架。
2. **以身體、內襯、甲片三層重建肩臂。** 武士的厚實來自三角肌、前臂和衣甲體積；先前要求的兩倍手腕是誇張風格，寫實版本應把量感移回前臂與籠手，保留腕部可彎曲空間。
3. **鎧甲採實物結構與人工完成的表面品質。** 用年代合適的當世具足參考重做胴、袖、草摺、籠手的比例和連接。Cyber Samurai 可參照表面品質，不能当成 1614 年史實造型；目前未找到已核實授權、風格又合適的完整免費武士甲。
4. **幸村、家康、小兵共用身體拓撲、骨架和基本甲片。** 主將使用獨立頭部、頭盔／前立與材質變體；小兵從同一完成資產降 LOD。赤漆、黑金不是只換整體色調，應有獨立的漆面、裸金屬、布、皮革遮罩。

驗收先看無頭盔臉部、側面輪廓、抬臂、握槍四個角度，再做烘焙及手機 LOD。不能把增加面數、繩索數量或大面積噪點當作完成寫實雕刻。

## 重建

```bash
python3 tools/fetch_character_candidates.py
/workspace/yukimura-tools/render-env/bin/python tools/build_character_candidates.py
```

原檔及可編輯 `.blend` 在忽略目錄 `.tmp/character-candidates/`，避免把大份來源貼圖重複塞進 Git。公開候選 GLB、圖片、來源清單與完整授權隨比較頁一起保存。不要把 `.tmp` 中其他 repository 的腳本拿來執行；本次僅下載模型資料與授權。

網路範圍：Sketchfab、Fab、CGTrader、BlenderKit、OpenGameArt、Smithsonian、Met API 等主站請求被環境代理回覆 403。因此本次不是完整 marketplace 比價，也沒有虛構價格／可下載狀態。GitHub 的模型資料與逐件授權可存取；所有「已下載」敘述均指此已驗證來源。
