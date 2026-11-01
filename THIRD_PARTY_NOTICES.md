# 第三方與來源通知

- Swiss Ephemeris，Astrodienst AG：固定commit 94621aba9f3ff9c32cb721eac0380c30dbb153fe。選擇AGPL免費路線。原授權、版權通知與AGPL全文於third_party/swisseph保留；Git blob清單見source_manifest.json。未修改其源碼。此處為必要來源標示，非作者背書。
- tzdata2026.3，IANA2026c：執行時資料位於vendor/tzdata；原LICENSE與LICENSE_APACHE位於third_party/tzdata-notices。保留原始版權與Apache2.0及IANA資料通知。
- Python與系統C數學庫：外部系統依賴，不在本包分發。
- NASA/JPL Horizons API 1.2 DE441：horizons_evidence含合成案例查詢輸出，非本專案作者創作；原來源與科學說明保留，不將NASA原始回應改標為本專案所有。其回應不是執行引擎。
- USNO近似GAST及Placidus公開數學定義用於另寫的近似幾何檢查，來源在HOUSE_VERIFICATION.md；未使用LibEphemeris實作。

新撰專案程式採AGPL-3.0-only，完整條款見根目錄LICENSE。第三方作品權利仍依各自原始通知。
