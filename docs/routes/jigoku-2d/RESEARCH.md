# 研究與來源核對

調查日期：2026-10-15（Asia/Taipei）。本環境沒有可用的一般搜尋引擎工具；以官方網站及上游 GitHub 直接讀取文件。以下列出實際讀到的內容與受阻範圍，不能當作已完成全面歷史研究。

## 已取得正文

| 來源 | 本次讀到的內容 | 對這條路線的用途 |
| --- | --- | --- |
| [Flare game README](https://github.com/flareteam/flare-game/blob/af6eee6d339ac98011864bfe89da837fe7769c28/README) | 2D 暗黑動作 RPG、PNG／OGG、Tiled 地圖；引擎 GPLv3+，美術／資料 CC-BY-SA 3.0；art_src 是 Blender 等原始素材 | 證明有可研究的完整開源案例，不能把其素材當 CC0 |
| [Flare 舊 art_src 說明](https://github.com/flareteam/flare-game/blob/af6eee6d339ac98011864bfe89da837fe7769c28/art_src/README.md) | 舊資料可能需 Blender 2.7 或更早；新版 HD 源檔另有 repository | 避免用過時工具當現代流程 |
| [Flare HD Blender 來源](https://github.com/flareteam/flare-game-art-src/blob/8830c68b420b631e09a459e5b0bf87c0e068a558/README.md) | 現代 Blender、EEVEE、目標原版三倍尺寸；render.sh 呼叫內嵌 Python，含 mod_data、Tiled 資料 | 最貼近 Blender → 離線高精細 sprite 的參考；本次沒有執行其渲染腳本 |
| [Flare engine](https://github.com/flareteam/flare-engine/blob/1969baeb89ebf94cf22e2bc2ed4e3d8413714d4f/README.engine.md) | SDL2 與相關擴充 | 適合參考 ARPG 管線；本次不假定原生引擎能直接取代現有手機網頁版本 |
| [Phaser 3.90 README](https://github.com/phaserjs/phaser/blob/v3.90.0/README.md) | 桌面／手機瀏覽器、WebGL／Canvas、TypeScript 與 Vite 生態 | 新路線優先候選，不需自己重寫 sprite 引擎 |
| [Phaser MultiAtlasFile](https://github.com/phaserjs/phaser/blob/v3.90.0/src/loader/filetypes/MultiAtlasFile.js)／[LightsManager](https://github.com/phaserjs/phaser/blob/v3.90.0/src/gameobjects/lights/LightsManager.js) | 多頁圖集載入、normalMap 欄位與 2D light 管理 | 可評估圖集和有限動態光，但載入多頁不等於自動按方向串流或卸載 |
| [Blender Camera RNA](https://github.com/blender/blender/blob/87cb1c358f9306cc51ecd1f164ad773a8933c1b6/source/blender/makesrna/intern/rna_camera.cc) | 相機提供 ORTHO 類型 | 固定正交投影；這是原始碼查核，不是已跑過渲染實驗 |
| [大阪城天守閣官網](https://www.osakacastle.net/english/) | 本次回傳日文首頁；提及大坂之陣落城、現存石垣／壕溝等屬德川時代以後，現天守為 1931 年重建 | 不應照搬今日大阪城外觀宣稱是 1614／1615 年完全復原 |

以上 GitHub 固定版本依本次取得的 upstream commit 或 tag 記錄；沒有下載或混用外部模型／貼圖。Flare HD 個別新增材質的授權仍須查看 CREDITS；README 提到部分 CC0 不代表整庫 CC0。

## 未取得正文，不能當作已查證引文

以下請求於本環境回覆 CONNECT 403：

- 京都國立博物館地獄草紙／繪卷館藏頁：`https://www.kyohaku.go.jp/eng/collection/meihin/emaki/`。
- 奈良國立博物館館藏頁、ColBase（日本國立博物館館藏彙整）、興福寺英文頁。
- Metropolitan Museum 的 Japan／hell 搜尋頁、Cleveland Museum 開放 API。
- Britannica 的 asura 條目、Columbia 的日本宗教教材頁。
- Blender 網站 manual 相機頁（改讀上游相機原始碼）。
- Blizzard《Diablo II: Resurrected》官方介紹頁。

因此本次沒有引用 Diablo 原版精確方向數／內部面數／解析度，也不把《Diablo IV》或《Resurrected》當作純 2D sprite 遊戲。使用者提到 Diablo，這裡取的是暗黑等角 ARPG 的構圖、場景密度、戰利品與戰鬥可讀性方向。

## 歷史、宗教與美術判斷

沿用專案既有的暫定歷史框架：幸村／信繁、大坂冬夏之陣與後世十勇士傳說；本次大阪城官網回應不足以逐條核對人物死因、裝束、六文錢或各場戰鬥。這些不能因有一個官方 URL 就標為全部確認。

美術策劃採以下界線，待可用博物館／學術來源再細化：

- 地獄與修羅道不直接當成同義詞，也不宣稱武士必然墮入任何一道。
- 六文錢取民俗渡河的意象；「六枚化為六個魂燈」是本作機制設定，並非佛教教義。
- 地獄草紙、六道繪、武者亡靈／修羅物是後續研究關鍵詞，暫不宣稱圖中任何地景逐件取自已讀原作。
- 三途河、鬼火、赤鬼、亡者軍勢作幻想素材；具體戰場、關名與守將均為原創。閻魔、地藏不預設為必須殺死的敵人。
- 幸村十勇士從修羅戰境闖入地獄、拯救亡魂，是架空敘事。家康若再現，是幸村執念形成的「金甲之影」，不是判定歷史人物死後去處。

目前三張 image gen 圖以原創日式地獄戰場為方向，未匯入博物館照片、參考照水印或第三方遊戲資產。
