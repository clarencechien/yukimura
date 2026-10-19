# 未來赤備：拆件生成＋既有骨架組裝

計劃見 [PLAN.md](PLAN.md)。每個階段的對照圖放在這裡，通過後才進下一階段。

## 第 0 階段：圖像模型 A/B

同一張原圖、同一段提示（正面、正交、A 姿勢、灰底、平光，保留全部造型細節，[提示全文](images/prompts.json)），請兩個模型各畫一張。工具：[gen_image.py](../../../../tools/part_pipeline/gen_image.py)。

![](stage0-ab.jpg)

左：原圖。中：`google/gemini-3-pro-image`（Nano Banana Pro）。右：`openai/gpt-image-2.5-flare`。

| | Nano Banana Pro | GPT Image 2.5 Flare |
| --- | --- | --- |
| 與原圖造型一致 | 較高：體型厚實、袖與膝甲的形狀接近原圖 | 較瘦，部分甲片重新設計（袖變長、膝甲變小） |
| A 姿勢、對稱 | 手臂角度較小（約 25°），對稱良好 | 標準 A 姿勢、最對稱 |
| 解析度 | 1696 × 2528 | 1024 × 1536 |
| 費用 | 0.140 美元 | 0.055 美元 |

兩張都已去掉原圖的光暈與暗背景，水平甲片、六文錢、鹿角、能量槽都保留。

**建議：用 Nano Banana Pro。** 它最忠於原圖，解析度也高，而且據評測多參考圖（之後畫側面、背面、單件都要以正面為參考）較穩。缺點是單價較高：以剩餘約 7.8 美元計，約可畫 55 張，本計劃預估需要 20–25 張。

[原圖檔](images/)：`ab-front-gemini-3-pro-image.png`、`ab-front-gpt-image-2.5-flare.png`。
