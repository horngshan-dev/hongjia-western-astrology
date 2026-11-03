# 西洋命盤時間模型及宮位驗收補強

2026-11-02。分支修正完成，本機驗收通過；**尚未部署Cloud Run，也未變更Sites或原GPT**。候選狀態保留。

## 完成的修正

1. UTC 2027-01-01（不含）以後、原2099支援範圍內的請求明確拒絕，code=`TIME_MODEL_OUTSIDE_VALIDATED_RANGE`，chart=null。這是防止尚未核對的遠期時間模型被包裝成精確盤，不是修正2099天文比對數值。
2. 1972後UTC→TT以歷史閏秒表再次核對；原生轉換出現不符即拒絕。1972前維持UT1近似但加明確警示及time_model欄位。
3. 原2001合成案例太陽及上升不變；`production_ready=false`保留。

## 測試結果

- 標準離線回歸：41/41 PASS（原34+新增7）。新增包含UTC界線、本地與UTC跨年差、歷史警示、閏秒前後、原生TT異常拒絕、既有數值保持及HTTP 422。
- 宮位獨立幾何比對：1,440/1,440 PASS；每組比上升、天頂及十二宮共14角度，最大差0.010113985808857251角秒，固定門檻1角秒。原始誤差表在house_erfa_comparison.json。
- PyERFA2.0.1.5／ERFA2.0.1／NumPy2.3.5只供額外驗證，未加入HTTP執行依賴。使用ERFA GAST/真黃赤交角及獨立半弧求根，沒有複用Swiss宮位實作。

## 仍保留的限制

宮位比對共享TT/UT1，是幾何驗證；不能證明所有年代的民用時間換算精確。1972前尚未重建歷史UTC／民用時制，也沒有實測EOP輸入。最高緯度65.5度，不能外推更接近極圈或極區。

先前2099年月球失敗、49/50天體比對及TT診斷原檔全部保留。原run_cross_epoch.py描述舊範圍；重現舊2099結果需用db37847的引擎基線，本分支對該輸入按新政策拒絕。不能重跑新政策後把拒絕當作舊失敗已消失。

尚需：候選部署及經MCP/GPT的端到端新契約驗收、速度／逆行獨立基準、負載與觀察期、公開分享驗收。這份本機結果不等於正式命盤已可解讀，也不等於外部親友已可安裝。

## 重現

```sh
sh build.sh
PYTHONPATH=vendor python package_source.py
PYTHONPATH=vendor python -m unittest discover -v
python -m pip install -r requirements-validation.txt
python verify_houses_erfa.py --library build/libswe.so --output acceptance_20261102/house_erfa_comparison.json
```

時間政策依據與更詳細支援範圍見../TIME_MODEL.md；宮位方法與官方參考見../HOUSE_VERIFICATION.md。
