---
name: Per-Trade Detail Log
overview: simulate() per-trade log tutacak, en iyi parametre seti için işlem bazlı tablo ve kâr/zarar özeti backtestlog.txt'e yazılacak.
todos:
  - id: trade-log-simulate
    content: simulate() fonksiyonuna trade_log=False parametresi ve initial_entry takibi ekle, liq/kâr çıkışında trades listesine kayıt yap
    status: completed
  - id: trade-log-print
    content: run_optimize() içinde en iyi parametre seti için simulate(trade_log=True) çağır, işlem detay tablosunu ve kâr/zarar özetini log() ile yaz
    status: completed
isProject: false
---

# Per-Trade Detay Logu Planı

## Eklenecek Çıktı Formatı

En iyi parametre seti seçildikten sonra `simulate()` ikinci kez çalıştırılacak,
bu sefer işlem günlüğü de tutulacak. Çıktı:

```
  ── İŞLEM DETAYI (En İyi Parametre Seti) ──────────────────────────────
  #   Giriş Fx   Avg  Toplam$   Çıkış Fx  Sonuç     İşlem PnL  Kümülatif
  1    0.8821    1    $40.00    0.8744     KÂR         +$3.50    +$3.50
  2    0.9105    3   $190.00    0.8720     KÂR        +$16.62   +$20.12
  3    1.0230    5   $527.50    ---        LİKİDASYON -$65.94   -$45.82
  ...
  ── ÖZET ──────────────────────────────────────────────────────────────
  Toplam kâr   (10 kazanan) : +$658.20
  Toplam zarar  (3 likidasyon) : -$197.70
  Net PnL                    : +$460.50
```

## Değişiklikler — `[backtest.py](backtest.py)`

### 1. `simulate()` trade_log parametresi

`simulate()`'e `trade_log=False` opsiyonel parametresi eklenecek. `True` iken her kapanan işlemi bir sözlük olarak listeye ekler ve bunu sonuç dict'ine dahil eder:

```python
def simulate(klines, params, step_size=0.1, tick_size=0.0001, trade_log=False):
    trades = []  # yalnızca trade_log=True iken doldurulur
    ...
    if liq_hit:
        if trade_log:
            trades.append({
                "type": "LİKİDASYON",
                "entry": initial_entry,       # pozisyon açılış fiyatı
                "avg_orders": order_count,
                "total_usd": total_usd_spent,
                "pnl": -margin_lost,
            })
    ...
    if profit_hit:
        if trade_log:
            trades.append({
                "type": "KÂR",
                "entry": initial_entry,
                "avg_orders": order_count,
                "total_usd": total_usd_spent,
                "pnl": pnl,
            })
    ...
    result["trades"] = trades  # yalnızca trade_log=True iken dolu
```

`initial_entry` her pozisyon açıldığında kaydedilecek yeni bir değişken.

### 2. `run_optimize()` içinde detay yazdırma

En iyi parametre seti belirlendikten sonra `simulate(..., trade_log=True)` çağrılacak ve tablo + özet basılacak:

```python
best_p, best_r = results[0]
detail = simulate(klines, best_p, trade_log=True)
# → detail["trades"] üzerinde döngü
```
