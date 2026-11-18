---
name: backtest Refactor
overview: backtest.py'den DEFAULT_PARAMS kaldırılacak, target_entry_price devre dışı bırakılacak, RSI hesabı O(n)'e indirilecek ve varsayılan mod optimizasyon olacak.
todos:
  - id: remove-default-params
    content: DEFAULT_PARAMS ve run_single() fonksiyonunu kaldır, FIXED_PARAMS sabitlerine dönüştür
    status: completed
  - id: remove-entry-price
    content: target_entry_price'ı simulate() ve OPTIMIZE_GRID'den kaldır, giriş koşulunu sadece RSI yap
    status: completed
  - id: fix-rsi-perf
    content: compute_rsi() O(n²) yerine tüm seriyi tek geçişte hesaplayan compute_rsi_series() yaz
    status: completed
  - id: simplify-main
    content: "--optimize flag'ini kaldır, main() sadece --symbol/--interval/--days/--mode alsın"
    status: completed
isProject: false
---

# backtest.py Yeniden Yapılandırma Planı

## Mevcut Sorunlar

1. **Hiç trade yok:** `target_entry_price = 5.0` sabit değeri APEUSDT için hiçbir zaman sağlanmıyor. Sonuç: 0 trade, boş rapor.
2. **Çok yavaş:** `compute_rsi()` her mum için sıfırdan hesaplanıyor (O(n²)). 25.920 mum = dakikalarca bekleme.
3. **Karmaşık yapı:** `DEFAULT_PARAMS` ve `OPTIMIZE_GRID` iki ayrı kavram kafa karışıklığı yaratıyor.

## Yapılacak Değişiklikler

### `[backtest.py](backtest.py)` — Komple Refactor

**Kaldırılacaklar:**
- `DEFAULT_PARAMS` sözlüğü tamamen kaldırılacak.
- `--optimize` flag'i kaldırılacak; optimizasyon artık **varsayılan ve tek** çalışma modu.
- `run_single()` fonksiyonu kaldırılacak.

**Eklenecek/Değiştirilecek Sabit Parametreler (dosya başında):**
```python
# Sabit Parametreler — Optimize edilmez
LEVERAGE     = 8
INITIAL_USD  = 40
MAX_ORDERS   = 5
```

**`OPTIMIZE_GRID` korunacak, `target_entry_price` kaldırılacak:**
```python
OPTIMIZE_GRID = {
    "loss_trigger_percent":  [0.10, 0.15, 0.20, 0.25, 0.30],
    "target_profit_percent": [0.20, 0.30, 0.40, 0.50],
    "target_rsi":            [40, 45, 50, 55, 60],
    "order_multiplier":      [1.2, 1.3, 1.5],
}
```

- `target_entry_price` tamamen kaldırılacak. Giriş koşulu **sadece RSI** ile belirlenecek:
  ```python
  # Eski (sorunlu):
  rsi_ok and price <= target_entry_price
  # Yeni:
  rsi_ok  # sadece RSI yeterli
  ```

**`compute_rsi()` O(n²) → O(n) düzeltmesi:**

Şu an her mum için tüm geçmiş veriden sıfırdan hesaplanıyor. Bunun yerine RSI değerleri `simulate()` başında tek seferde hesaplanacak:
```python
def compute_rsi_series(closes, period=14):
    # Tüm mumlara ait RSI listesini tek geçişte döndürür
    rsis = [50.0] * len(closes)
    # ... EMA tabanlı tek geçiş hesabı
    return rsis

def simulate(klines, params, ...):
    closes = [float(k[4]) for k in klines]
    rsis   = compute_rsi_series(closes)   # tek seferlik
    for i in range(...):
        rsi = rsis[i]   # O(1) erişim
        ...
```

**`run_optimize()` sadeleştirilecek:**
- Her kombinasyon test edilecek, sonuçlar PnL'e göre sıralanacak.
- En iyi 10 kombinasyon terminale ve `backtestlog.txt`'e yazılacak.

**`main()` sadeleştirilecek:**
```python
# Sadece bu argümanlar kalacak:
--symbol   (varsayılan: APEUSDT)
--interval (varsayılan: 5m)
--days     (varsayılan: 90)
--mode     (varsayılan: long)
```
