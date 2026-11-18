# bot.py — Kaldıraç Analizi Notu

## Sonuç: bot.py'de değişiklik GEREKMİYOR

`initial_usd = 40`, marjin değil **pozisyon büyüklüğünü** ifade ediyor.
Gerçek marjin = 40 / 8 = **$5** (Binance tarafından otomatik hesaplanır).

## bot.py Kâr/Zarar Mantığı — Doğrulama

| Hesap | Formül | Sonuç | Doğru mu? |
|---|---|---|---|
| İlk emir miktarı | `initial_usd / price` | $40'lık pozisyon | ✓ |
| Kâr hedef fiyatı | `entry × (1 + target_profit_pct / leverage)` | Marjine göre %30 kâr | ✓ |
| DCA tetik yüzdesi | `(fiyat_hareketi / entry) × leverage` | Marjinin %20'si kayıpla tetik | ✓ |
| Likidasyon fiyatı | Binance API'den okunuyor (`liquidationPrice`) | Exchange hesaplıyor | ✓ |
| Gerçekleşen PnL | Binance API'den okunuyor | Exchange hesaplıyor | ✓ |

## backtest.py'de Yapılan Düzeltmeler

`backtest.py`, `bot.py`'nin kendi hesapladığı kısımları simüle ediyor.
Aşağıdaki tutarsızlıklar giderildi:

1. `calculate_qty` → `usdt_amount / price` (LEVERAGE çarpımı yok, bot.py ile aynı) ✓
2. Likidasyon kaybı → `-total_usd_spent / LEVERAGE` (marjin kaybı, pozisyon büyüklüğü değil) ✓
