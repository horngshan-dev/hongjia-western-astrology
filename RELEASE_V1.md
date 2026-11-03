# 西洋本命盤 V1.0.0｜小規模服務發布範圍

發布者：洪聖添。2026-11-03。

本版本不更動既有Swiss Ephemeris 2.10.03 / Moshier / tropical / Placidus計算。預設仍為candidate；部署者明確設定WESTERN_RELEASE_STAGE=stable時，HTTP成功回傳status=calculated、production_ready=true、release_version=1.0.0、release_scope=small_scale_natal_service。輸入錯誤與不支援範圍仍回422及chart=null，不提升成成功。

已具備位置跨年代抽樣、1440組宮位幾何、79組速度及76組非停滯區方向比對證據（先前PR #1–#3）；共享TT/UT1、停滯中心不確定、遠期UTC原始失敗證據全部保留。本輪新增本機HTTP 120次合成請求（最多4個同時連線）全部成功，回傳時間逐次匹配；格式錯誤400、模擬引擎故障503後恢復正常。另12次實際Sites MCP請求，四批、每批3個工具呼叫，均成功且輸入回傳時間一致。這些不是高負載、長期可用性或全部日期精度保證。

部署維持並行1、執行個體上限1、CPU1、512Mi、30秒逾時，不改身分、API憑證或八字紫微服務。適用小規模本命盤，無SLA、無流年推運。

支援限制：原1900起範圍，UTC 2027-01-01及以後拒絕；1972年前民用時間作UT1近似並保留警示；無實測EOP。未知出生時間不代填；DST重複時間須選fold；極區Placidus不可用即拒絕。極近停滯的retrograde布林值只代表引擎該瞬時速度符號，不能宣稱已精確認證停滯時刻。

正式服務標記只指上述範圍的工程發布狀態，不是科學驗證占星詮釋或預測效果。公開目錄審查、外部親友安裝及頭貼為獨立工作，不由本版本宣告完成。

正式部署後須確認health、原2001合成盤數值、未知時間與遠期拒絕、MCP狀態及公開對應源碼。任何失敗保持原revision流量，或回復到hongjia-western-api-candidate-agpl-163e841。服務URL名稱保留candidate以免既有Actions/MCP失效，實際發布狀態以回傳欄位為準。
