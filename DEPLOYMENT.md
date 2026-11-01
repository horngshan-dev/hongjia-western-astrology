# 西洋命盤候選部署｜驗收完成

日期：2026-11-01；發布主體洪聖添。僅為候選服務，production_ready=false，尚未接入原GPT或網站。

- 服務：https://hongjia-western-api-candidate-177713424950.asia-east1.run.app
- 健康：https://hongjia-western-api-candidate-177713424950.asia-east1.run.app/health
- 完整對應源碼（免登入）：https://hongjia-western-api-candidate-177713424950.asia-east1.run.app/source
- 原始碼固定點：3876f318cbfc512c7639f7023595e129e80267d5
- Ready修訂版：hongjia-western-api-candidate-agpl-3876f31
- 映像digest：sha256:42210b013b994747ca1e688cc470043b37232d7be60f6be12dab7a4e3f48737c
- 對應源碼tar.gz SHA256：589b4e1b8af6f6022780640763107f9c3c5f9949771e02d158e07bcbd6bde8d1
- 修正版Cloud Build：1f00b43a-a000-41ec-b816-c323b8eea6b9

34項本機測試、23項雲端驗收通過。詳細雲端判定見CLOUD_VERIFICATION.json，沒有金鑰值。服務最少0、最多1個執行個體，並行1、1CPU、512Mi、請求逾時30秒。專用執行身分只新增指定secret的讀取權，未重用原正式金鑰。計算需Bearer，源碼與健康資訊不需認證。

原八字紫微正式服務仍為hongjia-bazi-api-time-1b1e0c4承接100%流量。未修改原Actions、GPT知識檔或網站。

初次建置357f89e採用/healthz，遇Google前端保留路徑404，沒有判定通過。修正版以/health與/source避免z結尾URL，重新建置並部署後才完成上述驗收。
官方限制：https://docs.cloud.google.com/run/docs/known-issues#reserved-urls

GPT追加驗收用介面為gpt-action-candidate.json，不替換原四個Actions。需新建一組候選Action，並在Builder內輸入專用金鑰；不應將金鑰貼入對話、原始碼或本文。尚未執行Builder追加或正式發布。新舊服務不同網域、不同金鑰，原認證保留。

後續仍需：地點座標的可驗證取得流程、正式回應schema與錯誤契約收斂、GPT實際工具呼叫／解讀／分享驗收、正式化判定、使用者可見源碼連結、雲端費用及平台日誌設定核對。當前使用Python內建串行HTTPServer，僅供受控候選驗收，沒有負載或全面生產安全認證。

本檔與驗收報告是部署後新增文件；正在執行的對應源碼仍以固定點3876f31及上述/source下載內容為準，不能將後續main分支文件提交誤認為已部署的新映像。
