# Trading Bot — Geliştirme Önerileri

## Öncelik Sırası

| Adım | Konu | Zorluk |
|------|------|--------|
| 1 | PnL takibi + Telegram raporu | Kolay |
| 2 | Otomatik yeniden başlatma (systemd) | Kolay |
| 3 | Backtesting + Parametre Optimizasyonu | Orta |
| 4 | Dinamik pozisyon boyutu | Orta |

---

## 1. Risk Yönetimi

**Dinamik pozisyon boyutu:**
Şu an sabit `initial_usd = 40`. Bakiye büyüdükçe bu oran aynı kalıyor — bileşik büyüme yok. Bakiyenin belirli bir yüzdesine göre (`initial_usd = bakiye * 0.05` gibi) dinamik boyutlandırma yapılabilir.

---

## 2. Strateji Geliştirme

**RSI + ek filtreler:**
RSI tek başına yeterli olmayabilir. RSI + hacim analizi, RSI + trend yönü (EMA 50/200) kombinasyonları yanlış giriş sayısını azaltabilir. Örnek: "RSI ≤ 50 VE fiyat 200 EMA üzerinde".

**Short/Long mod:**
Bot artık `mode = "long"` veya `mode = "short"` parametresiyle her iki yönde çalışabilir. Bkz. `bot.py` strateji ayarları bölümü.

---

## 3. İzleme ve Gözlemlenebilirlik

**PnL takibi:**
Her pozisyon kapandığında "Bu işlemde $X kazandım, toplam bu ay $Y" özeti Telegram'a gönderilebilir. Bot şu an kâr/zarar tutarını loglamıyor.

**Günlük rapor:**
Her gece belirli bir saatte (örn. 23:00) botun o günkü işlem sayısını, kâr/zararı ve mevcut durumu Telegram'a göndermesi.

**Web dashboard (orta-uzun vade):**
Basit bir Flask veya FastAPI ile log verilerini görselleştiren küçük bir web arayüzü. Grafik, PnL eğrisi, son işlemler.

---

## 4. Altyapı Güvenilirliği

**Otomatik yeniden başlatma:**
Bot çökerse screen oturumunda kalıyor ama yeniden başlamıyor. `systemd` servisi kurulabilir:

```bash
# /etc/systemd/system/trading-bot.service
[Unit]
Description=Binance Trading Bot
After=network.target

[Service]
User=ceyhunkanat
WorkingDirectory=/home/ceyhunkanat/bot
ExecStart=/home/ceyhunkanat/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kurulum:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo journalctl -u trading-bot -f   # log takibi
```

---

## 5. Backtesting + Parametre Optimizasyonu

Bot'tan **tamamen bağımsız** ayrı bir sistem (`backtest.py`). Botu durdurmadan, gerçek para riske atmadan geçmiş veri üzerinde çalışır.

**Ne yapar:**
- Binance'ten geçmiş kline verisi çeker (sembol parametreden alınır)
- Farklı parametre kombinasyonlarını otomatik olarak dener
- Her kombinasyon için kâr/zarar, likidasyon sayısı ve başarı oranını hesaplar
- En yüksek kârı sağlayan parametre setini raporlar

**Optimize edilebilecek parametreler:**
- `loss_trigger_percent` — ne kadar düşünce DCA tetiklensin
- `target_profit_percent` — kâr hedefi
- `target_rsi` — hangi RSI seviyesinde giriş yapılsın
- `order_multiplier` — her DCA'da kaç kat artsın

**Kullanım:**
```bash
python backtest.py --symbol ARBUSDT --interval 5m --days 90
```

Bkz. `backtest.py` — hazır taslak mevcut.

---

## Notlar

- Bu döküman `gelistirme_onerileri.md` olarak bot klasöründe saklanmaktadır.
- Her öneri Agent modunda Cursor'a "şunu uygula" diyerek hayata geçirilebilir.
