# 上升與Placidus十二宮近似幾何核對

## 2026-11-02補充：獨立ERFA幾何比對

`verify_houses_erfa.py`以PyERFA 2.0.1.5／ERFA 2.0.1計算IAU 2006/2000A GAST與真黃赤交角，另以Python二分法求Placidus半弧根。它不呼叫Swiss的恆星時、黃赤交角或宮位程式；僅作驗證，不接入執行引擎。

5個合成年代（1900、1945、1979、2000、2024）×4個日內時刻×9種緯度（南北65.5度內）×8種經度，共1,440組；逐一比較上升、天頂及十二宮共14個角度。預先固定門檻1角秒，1,440組全部通過，最大差0.010114角秒。完整誤差表：`acceptance_20261102/house_erfa_comparison.json`。

這是獨立地球姿態模型及宮位幾何的交叉比對，**共用指定TT/UT1，沒有獨立驗證出生民用時間至UT1換算**。TT=UT1+69.184秒只是可重現合成輸入，不是宣稱歷史Delta T固定如此。緯度65.5度以上及全部時間域尚未涵蓋；不能據此聲稱全範圍正式驗收完成。

重現（額外依賴只供驗證）：

```sh
python -m pip install -r requirements-validation.txt
python verify_houses_erfa.py --library build/libswe.so --output acceptance_20261102/house_erfa_comparison.json
```

ERFA官方來源：https://github.com/liberfa/pyerfa 、https://github.com/liberfa/erfa/blob/master/src/gst06a.c 。SOFA模型說明：https://www.iausofa.org/current-software 。下文保留先前近似檢查的歷史範圍與結果，兩種檢查不得混為同一精度。

## 先前近似檢查（保留紀錄）

此檢查使用獨立Python三角函數及二分求根，不讀取Swiss宮位函式、恆星時或黃赤交角結果。依USNO近似GAST與平均黃赤交角，再按Placidus晝夜半弧三等分定義求宮頭。這是近似算法交叉核對，不是同精度的第三方完整命盤服務。

共享輸入：TT與UT1儒略日、地理經緯度。時間換算仍由原候選準備，沒有獨立核對UTC→UT1；不得宣稱全鏈獨立驗證。USNO近似式與平均黃赤交角有誤差，故先設30角秒候選門檻。不是宣稱正式引擎只有此精度，也不是將此近似核對器接入解讀。

測試原合成案例：上升差0.036760角秒、天頂差0.000566角秒、十二宮最大差0.079539角秒。數據見house_geometry_comparison.json。

另以4組任意時刻、5種緯度（-50、-25、0、25、50度）、4種經度，共80組幾何比較：全部低於30角秒，最大差26.206284角秒。資料見house_grid_comparison.json。TT設定為UT1+69秒是共享合成測試輸入，不是該年代真實ΔT。

檢查器保守限於約2000–2100及南北緯50度內；不支持極區，不據此推論更早年代或全緯度。超範圍拒絕，不另選宮制。候選正式引擎的日期支援不等於已完成完整日期範圍驗收。

測試總數25：前版22項，新增80組幾何格點比較（1項）、日期／緯度限制（1項）、赤道對宮與跨零度（1項）。測試入口python -m unittest discover -v。verify_houses.py重算單案例。

來源：
- 美國海軍天文台 https://aa.usno.navy.mil/faq/GAST （近似恆星時及黃赤交角）
- LibEphemeris作者技術文件 https://kerykeion.net/libephemeris/docs/reference/house-systems （Placidus半弧與座標公式）

未安裝LibEphemeris或複用其實作程式；此處依公開數學定義另寫幾何檢查。
