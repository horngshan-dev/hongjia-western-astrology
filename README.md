# 洪家城隍爺｜西洋命盤開源候選服務

> 2026-11-02候選分支更新（尚未部署）：時間模型上限改為UTC 2027-01-01不含，並揭露1972年前UT1近似；詳見[TIME_MODEL.md](TIME_MODEL.md)。新增1,440組ERFA宮位幾何交叉比對，詳見[HOUSE_VERIFICATION.md](HOUSE_VERIFICATION.md)。原2099年月球失敗仍保留。以下部署版本描述為先前基線，不能視為本分支已上線。

發布主體：洪聖添。版本0.5.2，日期2026-11-01。新專案程式採AGPL-3.0-only；第三方授權與原始通知保留。本包是可重建、本機驗證的候選服務，已建立獨立公開GitHub儲存庫，已部署獨立候選服務，尚未接入GPT／網站。

## 本包公開範圍

包含新增的時間輸入處理、Swiss ctypes接線、HTTP包裝、候選OpenAPI、來源打包、測試、合成資料與驗證紀錄。包含Swiss官方固定commit所需22個完整原始檔案及授權；包含tzdata2026.3時區資料（Git儲存以third_party/tzdata-source.tar.gz保存，build.sh會還原vendor/tzdata）與Apache2.0／IANA通知。不使用pyswisseph、Kerykeion或LibEphemeris作為執行依賴。

沒有複製原八字紫微私人儲存庫、原GPT指令、七份知識檔、私人施工圖、個人出生資料、API金鑰或雲端憑證。測試出生資料及座標均為合成參考案例。此安排是工程範圍描述，不是對未來整合作品法律邊界的保證。

## 離線建置與測試

需Python3.12、C編譯器、Linux系統數學庫。Python標準庫屬系統依賴，不含Python本體。無需pip下載、也無需NASA連線：已內含固定時區資料和十份NASA/JPL合成案例原始回應。

```sh
sh build.sh
PYTHONPATH=vendor python package_source.py
PYTHONPATH=vendor python -m unittest discover -v
```

測試會重算幾何與本機HTTP結果。原生共享狀態以單程序串行HTTPServer處理，未做負載驗收。不得直接把本機測試伺服器暴露為正式網際網路服務。

## 啟動本機候選

自行以安全方式設定專用WESTERN_API_KEY環境變數（至少32字元隨機值），然後：

```sh
PYTHONPATH=vendor python service.py
```

只監聽127.0.0.1:8080。GET /health與/license；GET /source不需認證，提供本次建置的完整對應源碼；POST /v1/astrology/natal需專用Bearer金鑰。勿重用原正式八字紫微金鑰。所有計算結果production_ready=false，並帶source_url。生產接入時需以實際公開來源URL取代相對連結，並在GPT／網站使用者可見處持續呈現，不能僅藏在工具JSON。

服務不將請求本文寫入日誌或資料庫；這不是對作業系統、反向代理或未來雲端平台日誌的保證。HTTP非TLS，只限本機；正式服務另需TLS入口、速率與資源限制、逾時與隱私驗收。

## 驗證範圍

十顆星在2001-06-15T04:34:56Z已與NASA/JPL DE441日期黃道地心視位置比較通過，月球門檻5角秒、其他天體2角秒。資料在horizons_evidence。上升與十二宮另有80組近似幾何核對，門檻30角秒、最大26.206284角秒；共用TT/UT1輸入，不是全流程高精度認證，詳見HOUSE_VERIFICATION.md。未推論全日期範圍已驗收。

## 發布前仍需完成

確定實際AGPL適用整合範圍；核對完整對應源碼可重建及來源下載版本一致；公開儲存庫與實際服務版本固定；回應schema與GPT Action驗收；部署、身份驗證與個資處理；在親友使用流程提供顯著源碼取得方式。使用者選擇免費開源不代表雲端算力、儲存或流量永遠免費。

官方來源：
- https://www.gnu.org/licenses/agpl-3.0.en.html
- https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation
- https://www.astro.com/swisseph/swephinfo_e.htm

公開源碼：https://github.com/horngshan-dev/hongjia-western-astrology

Dockerfile已通過候選雲端建置，已完成容器建置、獨立候選服務與專用金鑰設定，34項本機及23項雲端檢查通過；詳細狀態見DEPLOYMENT.md。

Cloud Run保留路徑修正：健康檢查/health、源碼下載/source，避免以z結尾的URL。見 https://docs.cloud.google.com/run/docs/known-issues#reserved-urls 。本機新增路徑回歸後34項測試通過；候選雲端修復驗收另行記錄。

候選部署已通過驗收，並非GPT功能正式上線。健康與源碼入口、固定版本及驗收結果見[DEPLOYMENT.md](DEPLOYMENT.md)。
