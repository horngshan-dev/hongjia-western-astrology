# 候選時間模型 v0.2.0

本文件及程式修正在獨立候選分支，尚未部署到既有Cloud Run。`production_ready=false`維持。原2099年月球UTC比對的失敗證據保留，不以修改門檻或刪除案例宣告通過。

## 支援政策

- 先用固定tzdata將當地民用時間轉為具有UTC標記的時間線位置；DST缺口拒絕，重複時刻須明確fold。
- 原1900–2099的外層範圍檢查保留；新增時間模型上限為UTC **2027-01-01 00:00:00（不含）**。2027–2099回覆`TIME_MODEL_OUTSIDE_VALIDATED_RANGE`、`chart=null`，不建立推估命盤。
- 上限依已核對的IERS Bulletin C72（2026-07-06）固定：2026年12月底不加閏秒。這是候選服務保守政策，不是宣稱2027之後不能做天文計算，也不是聲稱截止日前所有日期都已逐日驗收。
- 1972起：用固定歷史閏秒表（初始TAI−UTC=10秒，2017起37秒）獨立檢查原生函式回傳TT；偏差超過1毫秒即回`TIME_STANDARD_CONVERSION_UNVERIFIED`。避免原生程式靜默把UTC當UT1。
- 1972以前：沿用Swiss將民用時間近似當UT1的行為，但明列`pre_1972_civil_as_ut1_approximation`及警示；**沒有重建1961–1971歷史UTC頻率調整，也沒有重建更早民用時制**。此類結果不是精確歷史UTC命盤。
- UT1仍依Swiss Delta T模型推得，沒有匯入實測IERS EOP。新增ERFA宮位幾何比對共享TT/UT1輸入，不能消除此時間模型限制。
- 新`time_model`欄位揭露上述政策、UT1模型與閏秒來源；既有警示與時間精度欄位保留。

上限的擴充需核對新Bulletin C、測試邊界及TT一致性，再發新版；不隨系統當日時間自動擴張。

## 驗證

新增回歸覆蓋遠期拒絕、UTC與本地跨年邊界、歷史警示、2016/2017閏秒轉換、原生TT錯置拒絕、既有2001數值保持及HTTP 422合約。未知時間不猜填、極圈不默換宮制的舊測試保留。

官方來源：
- https://datacenter.iers.org/data/html/bulletinc-072.html
- https://maia.usno.navy.mil/products/leap-second
- https://www.astro.com/swisseph/swephprg.htm
- 固定原始碼`third_party/swisseph/swedate.c`的`swe_utc_to_jd`說明與UT1回退條件。
