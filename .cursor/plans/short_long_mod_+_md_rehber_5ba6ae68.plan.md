---
name: Short/Long Mod + MD Rehber
overview: bot.py'ye tek bir `mode` parametresi ekleyerek botu LONG veya SHORT olarak çalıştırma desteği kazandırmak ve geliştirme önerilerini bir MD dosyasına kaydetmek.
todos:
  - id: md-file
    content: gelistirme_onerileri.md dosyasını oluştur
    status: completed
  - id: mode-param
    content: bot.py'ye mode = 'long' / 'short' parametresi ekle
    status: completed
  - id: order-side
    content: place_futures_order fonksiyonunu mode'a göre BUY/SELL yapacak şekilde güncelle
    status: completed
  - id: price-watcher-logic
    content: price_watcher içindeki 4 mantık noktasını (giriş, likidasyon, DCA, kâr hedefi) mode'a göre güncelle
    status: completed
  - id: rsi-logic
    content: wait_for_rsi_and_restart içindeki RSI koşulunu mode'a göre güncelle
    status: completed
  - id: log-messages
    content: Log mesajlarını mode'a göre düzenle (averaging down/up)
    status: completed
isProject: false
---

# Short/Long Mod ve Geliştirme Rehberi

## Genel Yaklaşım

`mode = "long"` veya `mode = "short"` şeklinde tek bir parametre ekleniyor. Bu parametre, fiyat yönüne bağlı tüm karar noktalarını kontrol ediyor.

## Long vs Short: Neyin Değişeceği

LONG (mevcut hali) ve SHORT için mantık tam tersidir:

| Konu | LONG | SHORT |
|---|---|---|
| Giriş emri | `side="BUY"` | `side="SELL"` |
| Giriş koşulu | `price <= target_entry_price` | `price >= target_entry_price` |
| RSI koşulu | `rsi <= target_rsi` (aşırı satım) | `rsi >= target_rsi` (aşırı alım) |
| DCA tetik | Fiyat düştükçe (`entry - price`) | Fiyat yüktükçe (`price - entry`) |
| DCA adı | "Averaging down" | "Averaging up" |
| Kâr hedefi fiyatı | `entry * (1 + kar/kaldirac)` | `entry * (1 - kar/kaldirac)` |
| Kâr kapanma | `price >= target_price` | `price <= target_price` |
| Likidasyon kontrolü | `price <= liq_price` | `price >= liq_price` |
| Pozisyon kapatma | Zaten doğru (`positionAmt > 0 → SELL`) | Zaten doğru (`positionAmt < 0 → BUY`) |

`close_position()` fonksiyonu zaten her iki yönü destekliyor, değişmeyecek.

## [bot.py](c:\Users\CEYHUN\Desktop\bot\bot.py) İçin Değişiklikler

### 1. Strateji Ayarlarına `mode` eklenir:
```python
mode = "long"   # "long" veya "short"
```

### 2. `place_futures_order` — emir yönü `mode`'a göre:
```python
side = "BUY" if mode == "long" else "SELL"
```

### 3. `price_watcher` içindeki 4 mantık noktası güncellenir:

**Giriş koşulu:**
```python
# long: price <= target_entry_price
# short: price >= target_entry_price
entry_condition = price <= target_entry_price if mode == "long" else price >= target_entry_price
```

**Likidasyon kontrolü:**
```python
# long: price <= liq_price
# short: price >= liq_price
liq_hit = price <= liq_price if mode == "long" else price >= liq_price
```

**DCA kayıp hesabı:**
```python
# long: entry düştükçe zarar
# short: entry yükseldikçe zarar
if mode == "long":
    loss_percent = ((entry_price - price) / entry_price) * leverage
else:
    loss_percent = ((price - entry_price) / entry_price) * leverage
```

**Kâr hedefi:**
```python
if mode == "long":
    target_price = round_step(entry_price * (1 + target_profit_percent / leverage), tick_size)
    profit_hit = price >= target_price
else:
    target_price = round_step(entry_price * (1 - target_profit_percent / leverage), tick_size)
    profit_hit = price <= target_price
```

### 4. `wait_for_rsi_and_restart` içindeki RSI koşulu:
```python
# long: rsi <= target_rsi
# short: rsi >= target_rsi
rsi_condition = rsi <= target_rsi if mode == "long" else rsi >= target_rsi
```

### 5. Log mesajları mode'a göre güncellenir:
"Averaging down" → "Averaging up" (short modda)

## Ayrıca Yapılacak

- `gelistirme_onerileri.md` dosyası oluşturulur (önerilerin kalıcı kaydı)
