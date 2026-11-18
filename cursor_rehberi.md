# Cursor Kapsamlı Kullanım Rehberi
### Trading Bot Geliştiricisi İçin Türkçe Kılavuz

---

## İçindekiler

1. [Cursor Nedir?](#1-cursor-nedir)
2. [Arayüz Tanıtımı](#2-arayüz-tanıtımı)
3. [Çalışma Modları: Agent / Ask / Plan](#3-çalışma-modları)
4. [Chat ile Kod Değiştirme](#4-chat-ile-kod-değiştirme)
5. [@ Referans Sistemi](#5--referans-sistemi)
6. [Dosya Açma, Düzenleme, Gezinme](#6-dosya-açma-düzenleme-gezinme)
7. [Klavye Kısayolları](#7-klavye-kısayolları)
8. [Terminal Kullanımı](#8-terminal-kullanımı)
9. [SSH ile Uzak Sunucuya Bağlanma](#9-ssh-ile-uzak-sunucuya-bağlanma)
10. [Cursor Settings — Tüm Ayarlar](#10-cursor-settings--tüm-ayarlar)
11. [Gizli Dosya ve .env Yönetimi](#11-gizli-dosya-ve-env-yönetimi)
12. [Trading Bot Geliştirmede Cursor Kullanımı](#12-trading-bot-geliştirmede-cursor-kullanımı)
13. [Sık Yapılan Hatalar ve Çözümleri](#13-sık-yapılan-hatalar-ve-çözümleri)

---

## 1. Cursor Nedir?

Cursor, yapay zeka destekli bir kod editörüdür. Temelinde Visual Studio Code (VSCode) bulunur — yani VSCode'u daha önce kullandıysan arayüz sana tanıdık gelecektir. Farkı ise entegre yapay zeka asistanıdır: kodunu okur, yazar, düzenler ve sorularını yanıtlar.

**Cursor'un Yapabileceği Şeyler:**
- Dosyaları senin yerine okuyup analiz etmek
- Kod hatalarını tespit edip düzeltmek
- Yeni özellikler eklemek
- Kod mantığını sade Türkçe ile açıklamak
- Terminal komutlarını çalıştırmak
- Uzak sunucuya (VM) SSH ile bağlanmak

**Cursor'un Yapamayacağı Şeyler:**
- Binance hesabına doğrudan erişmek
- Gerçek zamanlı piyasa kararı vermek
- İnternet'ten bağımsız çalışmak (API key gerektirir)

---

## 2. Arayüz Tanıtımı

```
┌─────────────────────────────────────────────────────┐
│  [Menü Çubuğu: File / Edit / View / ...]            │
├───────────┬─────────────────────────┬───────────────┤
│           │                         │               │
│  SOL PANEL│    DÜZENLEYICI (Editor) │  SAĞ PANEL   │
│           │                         │  (isteğe      │
│  Dosya    │   bot.py kodun burada   │   bağlı)      │
│  Gezgini  │   görünür ve düzenlenir │               │
│           │                         │               │
│  Arama    ├─────────────────────────┤               │
│           │   CHAT PANELİ           │               │
│  Git      │   AI ile konuştuğun yer │               │
│           │                         │               │
├───────────┴─────────────────────────┴───────────────┤
│  TERMINAL (Alt Panel)  —  SSH, python bot.py vs.    │
└─────────────────────────────────────────────────────┘
```

**Sol Panel Simgeleri (Yukarıdan Aşağıya):**
| Simge | İşlev |
|-------|--------|
| Dosya ikonu | Dosya Gezgini — projedeki tüm dosyalar |
| Büyüteç | Arama — tüm dosyalarda metin ara |
| Dal ikonu | Git — versiyon kontrolü |
| Bulmaca | Eklentiler (Extensions) |

**Alt Panel — Terminal:**
`Ctrl + `` ` (backtick) ile açılır/kapatılır. SSH bağlantısı, bot başlatma gibi tüm terminal işlemleri burada yapılır.

---

## 3. Çalışma Modları

Cursor'da yapay zeka ile üç farklı modda çalışabilirsin. Sol altta küçük yazıyla hangi modda olduğun yazar.

### Agent Modu (Varsayılan)
**Ne yapar:** Dosyaları okur, yazar, düzenler. Terminal komutları çalıştırır. En güçlü moddur.

**Ne zaman kullanılır:**
- "Bu fonksiyonu düzelt"
- "Şu özelliği ekle"
- "Kodu yeniden yaz"

**Örnek:** *"bot.py'deki WebSocket bağlantısını daha kararlı hale getir"* → Agent modu dosyayı doğrudan düzenler.

---

### Ask Modu
**Ne yapar:** Sadece okur ve açıklar. Hiçbir dosyayı değiştirmez.

**Ne zaman kullanılır:**
- "Bu kod ne yapıyor?"
- "Bu hatanın sebebi ne?"
- "Nasıl bir yaklaşım izlemeliyim?"

**Örnek:** *"price_watcher fonksiyonunun mantığını anlat"* → Güvenli okuma modu, bir şey değişmez.

---

### Plan Modu
**Ne yapar:** Büyük değişiklikler yapmadan önce plan taslağı oluşturur. Sadece okur ve öneri sunar.

**Ne zaman kullanılır:**
- Büyük bir yeniden yapılandırma yapmadan önce
- "Önce bana bir plan sun, sonra uygula"

**Örnek:** *"Botu multi-symbol destekleyecek şekilde yeniden tasarla, önce plan yap"*

---

### Modlar Arasında Geçiş
Chat panelinin **sol alt köşesinde** "Ask", "Agent" veya "Plan" yazar. Tıklayarak değiştirebilirsin. Ya da AI'ya söylemen yeterli — otomatik geçiş teklif eder.

---

## 4. Chat ile Kod Değiştirme

Chat panelini açmak için: `Ctrl + L`

### Yeni Sohbet Başlatmak
`Ctrl + Shift + L` veya chat panelindeki `+` butonu ile yeni sohbet açılır. Her sohbet bağımsız bir bağlamdır.

### İyi Prompt Yazma Teknikleri

**Kötü prompt:**
> "kodu düzelt"

**İyi prompt:**
> "@bot.py dosyasındaki `price_watcher` fonksiyonunda WebSocket bağlantısı her 15 dakikada bir kopuyor. ping_interval ve ping_timeout değerlerini optimize et, ayrıca recv() üzerine 30 saniyelik timeout ekle."

**İyi promptun özellikleri:**
- Hangi dosya/fonksiyon? → `@bot.py`
- Sorun ne? → "her 15 dakikada kopuyor"
- Ne yapılsın? → "optimize et, timeout ekle"

### Kod Değişikliğini Kabul/Reddetme
AI bir değişiklik önerdiğinde editörde yeşil/kırmızı diff (fark) gösterir:
- **Accept (Kabul Et):** Değişikliği uygular
- **Reject (Reddet):** Eski hale döner
- **Accept All / Reject All:** Tüm değişiklikleri toplu kabul/ret

---

## 5. @ Referans Sistemi

Chat'te `@` yazınca bir menü açılır. Bu, AI'ya neyle ilgili konuşmak istediğini söylemenin en doğrudan yoludur.

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `@dosya_adı` | Belirli bir dosyayı bağlama ekle | `@bot.py` |
| `@klasör` | Tüm klasörü bağlama ekle | `@bot/` |
| `@web` | İnternet araması yap | `@web binance websocket api docs` |
| `@git` | Git geçmişini referans al | `@git son commit` |
| `@terminal` | Terminal çıktısını referans al | `@terminal` |
| `#dosya` | Dosyayı direkt ekle (@ gibi) | `#bot.py` |

**Pratik Kullanım:**

```
@bot.py deki log_event fonksiyonu her çağrıldığında dosyayı açıp
kapatıyor. Bunu daha verimli hale getirebilir misin?
```

```
@log.txt dosyasındaki son 50 satırı incele ve WebSocket hatalarını özetle.
```

---

## 6. Dosya Açma, Düzenleme, Gezinme

### Dosya Açma
| Yöntem | Açıklama |
|--------|----------|
| `Ctrl + P` | Hızlı dosya aç — dosya adını yazmaya başla |
| Sol panelden tıkla | Dosya gezgininden çift tıkla |
| `Ctrl + Shift + E` | Dosya gezginini aç/kapat |

### Editörde Gezinme
| Kısayol | İşlev |
|---------|-------|
| `Ctrl + G` | Belirli bir satıra git (satır numarası yaz) |
| `Ctrl + F` | Dosya içinde ara |
| `Ctrl + H` | Dosya içinde bul ve değiştir |
| `Ctrl + Shift + F` | Tüm projede ara |
| `Ctrl + Home` | Dosyanın başına git |
| `Ctrl + End` | Dosyanın sonuna git |
| `Alt + ↑/↓` | Satırı yukarı/aşağı taşı |

### Sekme Yönetimi
| Kısayol | İşlev |
|---------|-------|
| `Ctrl + W` | Mevcut sekmeyi kapat |
| `Ctrl + Tab` | Sekmeler arasında geç |
| `Ctrl + \` | Editörü böl (yan yana iki dosya) |

---

## 7. Klavye Kısayolları

### En Çok Kullanılanlar
| Kısayol | İşlev |
|---------|-------|
| `Ctrl + L` | Chat panelini aç |
| `Ctrl + K` | Satır içi düzenleme (inline edit) |
| `Ctrl + S` | Kaydet |
| `Ctrl + Z` | Geri al |
| `Ctrl + Shift + Z` | İleri al |
| `Ctrl + /` | Satırı yorum satırına çevir |
| `Ctrl + D` | Aynı kelimeyi seç (çoklu seçim) |
| `Ctrl + Shift + P` | Komut paleti aç |
| `` Ctrl + ` `` | Terminal aç/kapat |
| `Ctrl + B` | Sol paneli gizle/göster |
| `F11` | Tam ekran |

### Çoklu İmleç (Çok Kullanışlı!)
| Kısayol | İşlev |
|---------|-------|
| `Alt + Click` | İstediğin yere ek imleç ekle |
| `Ctrl + Alt + ↑/↓` | Yukarı/aşağı satıra ek imleç |
| `Ctrl + Shift + L` | Aynı kelimenin hepsini seç |

### Satır İçi AI (Inline Edit)
Düzenlemek istediğin kodu seç → `Ctrl + K` → ne yapılsın yaz → Enter.

Örnek: `calculate_qty` fonksiyonunu seç → `Ctrl + K` → "step_size None ise hata logla" → Enter

---

## 8. Terminal Kullanımı

### Terminal Açma
- `` Ctrl + ` `` ile aç/kapat
- Menüden: View → Terminal
- Birden fazla terminal: `+` butonuna tıkla

### Yeni Terminal Türleri
Terminalin sağ üst köşesindeki `∨` butonuna tıklayarak terminal tipi seçilebilir:
- **PowerShell** (Windows varsayılanı)
- **Command Prompt**
- **Git Bash**

### Terminalde AI Kullanımı
Terminal içindeyken `Ctrl + K` ile AI'ya terminal komutu yazdırabilirsin:

Örnek: `Ctrl + K` → "SSH ile 34.89.x.x adresine ceyhun kullanıcısıyla bağlan" → AI uygun komutu yazar.

---

## 9. SSH ile Uzak Sunucuya Bağlanma

Google Cloud VM'ine Cursor'dan doğrudan bağlanarak dosyaları **VM'in üzerinde** düzenleyebilirsin. Dosyaları indirip atmana gerek kalmaz.

### Kurulum

**Adım 1:** Sol panelde en alttaki `><` simgesine tıkla (Remote Explorer)

**Adım 2:** "Connect to Host" seç → SSH adresini yaz:
```
ceyhun@34.89.x.x
```

**Adım 3:** SSH key veya şifre ile bağlan.

**Adım 4:** Bağlandıktan sonra "Open Folder" ile VM'deki bot klasörünü aç:
```
/home/ceyhun/bot/
```

Artık `bot.py` dosyasını **doğrudan VM'de** düzenleyebilirsin. Kaydettiğinde anında VM'e uygulanır.

### SSH Config Dosyası (Kolaylık için)
Windows'ta `C:\Users\CEYHUN\.ssh\config` dosyasını aç (yoksa oluştur):

```
Host my-bot-vm
    HostName 34.89.x.x
    User ceyhun
    IdentityFile C:\Users\CEYHUN\.ssh\id_rsa
```

Kaydettikten sonra Cursor'da "Connect to Host" listesinde `my-bot-vm` görünür, IP yazmana gerek kalmaz.

### SCP ile Dosya Gönderme (Alternatif)
Düzenlediğin dosyayı terminalden VM'e göndermek için:
```powershell
scp "C:\Users\CEYHUN\Desktop\bot\bot.py" ceyhun@34.89.x.x:/home/ceyhun/bot/bot.py
```

---

## 10. Cursor Settings — Tüm Ayarlar

Ayarlar paneline erişim: `Ctrl + Shift + J` veya sol alttaki dişli simgesi → "Cursor Settings"

> Not: Cursor'un iki ayrı ayar paneli var:
> - **Cursor Settings** (`Ctrl+Shift+J`): AI ve Cursor'a özel ayarlar
> - **VS Code Settings** (`Ctrl+,`): Editör görünümü, font, tema vb.

---

### 10.1 Cursor Settings Paneli

#### GENEL (General)

| Ayar | Açıklama |
|------|----------|
| **Account** | Hesap bilgilerin, abonelik planın ve kullanım istatistiklerin |
| **Usage** | Aylık ne kadar AI isteği kullandığın |

---

#### MODELLER (Models)

| Ayar | Açıklama |
|------|----------|
| **Model seçimi** | Chat ve inline edit için hangi AI modelinin kullanılacağı. Seçenekler: Claude Sonnet (varsayılan, dengeli), Claude Opus (en güçlü, yavaş), GPT-4o, Cursor'un kendi modeli vb. |
| **Enable Claude 3.7 Thinking** | Claude'un adım adım düşünerek cevap vermesi. Karmaşık sorunlarda daha doğru sonuç verir, biraz daha yavaştır. |
| **Long Context** | Çok büyük dosyaları ve uzun sohbet geçmişini okuyabilme kapasitesi. Etkinleştirilmesi önerilir. |

**Öneri:** Trading bot gibi kritik kod için **Claude Sonnet** veya **Claude Opus** kullan.

---

#### ÖZELLİKLER (Features)

**Codebase Indexing (Kod Tabanı İndeksleme)**
| Ayar | Açıklama |
|------|----------|
| **Enable codebase indexing** | Tüm projeyi tarayıp AI'nın proje hakkında genel bilgi sahibi olmasını sağlar. `@codebase` komutu bunu kullanır. Trading bot gibi küçük projelerde her zaman açık olmalı. |
| **Index new folders automatically** | Yeni klasör eklenince otomatik indeksle |

**Autocomplete (Otomatik Tamamlama)**
| Ayar | Açıklama |
|------|----------|
| **Enable autocomplete** | Yazarken AI'nın devamını önermesi. Tab tuşuyla kabul edilir. |
| **Enable partial accepts** | `Ctrl + →` ile önerinin sadece bir bölümünü kabul et |
| **Trigger automatically** | Durmadan otomatik öneri mi, yoksa manuel tetikleme mi |
| **Autocomplete on brackets** | Parantez açınca otomatik öneri |

**Chat**
| Ayar | Açıklama |
|------|----------|
| **Always search the web** | Her soruda web araması yap (güncel API dokümantasyonu gibi şeyler için faydalı) |
| **Add chat contents to context** | Önceki sohbet içeriğini yeni sorularda referans al |
| **Show suggested files** | Chat'e otomatik ilgili dosyaları ekle |

**Editor**
| Ayar | Açıklama |
|------|----------|
| **Cursor Tab** | Tab tuşu otomatik tamamlama için kullanılsın mı |
| **Show inline diffs** | Değişiklikler editörde yeşil/kırmızı ile gösterilsin mi |
| **Auto-apply edits** | AI önerilerini otomatik uygula (dikkatli kullan!) |

---

#### GİZLİLİK (Privacy)

| Ayar | Açıklama |
|------|----------|
| **Privacy Mode** | **ÖNEMLİ!** Açıkken kodun Cursor'un sunucularına gönderilmez, AI model sağlayıcısına doğrudan gider. API key, .env gibi hassas dosyaların olduğu projelerde bu **AÇIK** olmalı. |
| **Telemetry** | Cursor'a anonim kullanım verisi gönderilsin mi |

> **Uyarı:** Trading bot'unda API_KEY ve API_SECRET bulunduğu için **Privacy Mode AÇIK** bırakmanı şiddetle tavsiye ederim.

---

#### KURALLAR (Rules)

| Ayar | Açıklama |
|------|----------|
| **User Rules** | AI'nın her zaman uyması gereken genel kurallar. Örnek: "Her zaman Türkçe konuş", "Kod yazarken önce mevcut dosyayı oku" |
| **Project Rules (.cursorrules)** | Proje klasörüne `.cursorrules` dosyası ekleyerek o projeye özel kurallar belirle |

**Örnek User Rules:**
```
- Her zaman Türkçe yanıt ver
- Kod değişikliği yapmadan önce mevcut dosyayı oku
- Değişiklik açıklamalarını kod içine yorum olarak ekleme
- Python kodlarında type hint kullan
```

**Örnek .cursorrules (bot klasörüne eklenebilir):**
```
Bu proje bir Binance Futures trading botudur.
- Dil: Python 3.10+
- Asenkron (asyncio) mimari kullanılıyor
- Binance Futures API (python-binance kütüphanesi)
- Tüm önemli işlemler log_event() ile loglanmalı
- Emir göndermeden önce her zaman pozisyon kontrolü yap
- API key ve secret asla kod içinde olmamalı, .env'den okunmalı
```

---

#### BAĞLANTI (Beta / Experimental)

| Ayar | Açıklama |
|------|----------|
| **MCP (Model Context Protocol)** | Cursor'u dış araçlara bağla: Notion, Figma, veritabanı, kendi API'in vb. |
| **Background Agents** | Arka planda çalışan AI ajanları (beta) |
| **Shadow Workspace** | AI değişiklikleri arka planda test eder, sonra sunar (beta) |

---

### 10.2 VS Code Settings (Editör Ayarları)

`Ctrl + ,` ile açılır. Trading bot geliştirmede önemli ayarlar:

| Ayar | Tavsiye | Açıklama |
|------|---------|----------|
| **Font Size** | 14 | Göz yorgunluğu için uygun boyut |
| **Font Family** | `'Cascadia Code', Consolas, monospace` | Programlama fontu |
| **Tab Size** | 4 | Python standardı 4 boşluk |
| **Word Wrap** | `on` | Uzun satırlar ekrana sığsın |
| **Minimap** | Kapalı olabilir | Sağdaki küçük kod haritası |
| **Auto Save** | `afterDelay` | 1000ms sonra otomatik kaydet |
| **Format on Save** | Açık | Kaydettiğinde kodu otomatik düzenle |
| **Python Interpreter** | VM'deki python yolunu seç | SSH bağlıyken VM'deki Python kullanılır |
| **Theme** | Dark+ veya One Dark Pro | Gece çalışmak için koyu tema |

---

## 11. Gizli Dosya ve .env Yönetimi

### .env Dosyası Nedir?
API key, şifre gibi hassas bilgileri kodun içine yazmak yerine `.env` dosyasında tutmak güvenlidir.

### Mevcut Durum (bot.py)
```python
load_dotenv()
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
```
VM'deki `.env` dosyasının içeriği:
```
API_KEY=buraya_binance_api_key
API_SECRET=buraya_binance_api_secret
```

### Telegram Token da .env'e Alınmalı
Şu an `telegram_notify.py` içinde token açık yazıyor. Güvenli versiyon:

**telegram_notify.py için .env'e eklenecek:**
```
TELEGRAM_BOT_TOKEN=7743011677:AAH...
TELEGRAM_CHAT_ID=1678024978
```

### .gitignore ile Güvende Tut
Eğer ileride Git kullanırsan `.gitignore` dosyasına şunları ekle:
```
.env
log.txt
log_old.txt
__pycache__/
*.pyc
```

### Cursor'da .env Dosyasını Görmek
Sol panelde `.env` dosyasına tıklayarak açabilirsin. Cursor bunu düz metin olarak gösterir. AI'ya `.env` içeriğini göstermemeye dikkat et — bunun yerine "API key .env'de saklanıyor" diyebilirsin.

---

## 12. Trading Bot Geliştirmede Cursor Kullanımı

### İş Akışı Önerisi

```
1. SSH ile VM'ye bağlan (Remote Explorer)
2. bot.py'yi Cursor'da doğrudan aç
3. Log'ları izle: terminal'de → ssh → screen -r
4. Hata görürsen Chat'te @bot.py @log.txt ile analiz et
5. Düzeltmeyi Agent modunda uygula
6. Screen'i yeniden başlat
```

### Faydalı Chat Komutları

**Log analizi:**
```
@log.txt Son 50 satırdaki hataları gruplandır ve olası nedenleri açıkla.
```

**Parametre optimizasyonu:**
```
@bot.py Mevcut ayarlarla 5 DCA senaryosunda maksimum zarar ne kadar olur? Hesapla.
```

**Yeni özellik:**
```
@bot.py Pozisyon açık olduğunda her 5 dakikada bir PnL bilgisini Telegram'a gönder.
```

**Hata ayıklama:**
```
@bot.py place_futures_order fonksiyonu bazen None dönüyor ama neden başarısız 
olduğu loglanmıyor. Detaylı hata loglama ekle.
```

### Screen Oturumu ile Çalışma
VM'de botu screen içinde çalıştırırsın. Cursor terminalinden yönetmek için:

```bash
# VM'ye bağlan
ssh ceyhun@34.89.x.x

# Aktif screen'leri listele
screen -ls

# Bot screen'ine bağlan
screen -r bot_screen_adi

# Botu durdur
Ctrl + C

# Botu yeniden başlat
python bot.py

# Screen'den çık (bot çalışmaya devam eder)
Ctrl + A, sonra D
```

---

## 13. Sık Yapılan Hatalar ve Çözümleri

### Hata 1: "AI dosyamı görmüyor"
**Neden:** Dosya chat'e eklenmemiş.
**Çözüm:** Chat'e `@bot.py` yaz veya dosyayı sürükle chat'e bırak.

---

### Hata 2: "AI hep aynı yanlış şeyi öneriyor"
**Neden:** Önceki sohbette yanlış bağlam oluşmuş.
**Çözüm:** `Ctrl + Shift + L` ile yeni sohbet aç. Her oturum için temiz başlangıç.

---

### Hata 3: "Değişiklik yapıldı ama VM'de görünmüyor"
**Neden:** Dosya local'de düzenlendi, VM'e gönderilmedi.
**Çözüm:** Ya SSH Remote ile doğrudan VM'de çalış, ya da `scp` ile gönder.

---

### Hata 4: "Cursor çok yavaş"
**Neden:** Büyük dosyalar veya çok fazla indeksleme.
**Çözüm:** Settings → Features → Codebase Indexing → Gereksiz klasörleri hariç tut.

---

### Hata 5: "AI kodu değiştirdi ama bir şey bozuldu"
**Neden:** AI önerisi test edilmeden kabul edildi.
**Çözüm:**
1. `Ctrl + Z` ile geri al
2. Daha sonra: Git kullan (`git commit` her çalışan sürümü kaydet)
3. AI'ya "önce mevcut dosyayı oku" diyerek başla

---

### Hata 6: ".env dosyası okunmuyor"
**Neden:** `python-dotenv` yüklü değil veya .env yanlış konumda.
**Çözüm:**
```bash
pip install python-dotenv
# .env dosyası bot.py ile aynı klasörde olmalı
```

---

### Hata 7: "Telegram mesajı gelmiyor"
**Neden:** Token veya chat_id yanlış, ya da hata loglara düşmüyor.
**Çözüm:** Log seviyesini kontrol et. Sadece `error`, `critical`, `warning` Telegram'a gönderilir. `info` gönderilmez.

---

## Hızlı Başvuru Kartı

```
┌──────────────────────────────────────────────────┐
│  EN ÇOK KULLANILAN KISAYOLLAR                    │
├──────────────────────────────────────────────────┤
│  Ctrl + L        → Chat panelini aç              │
│  Ctrl + K        → Seçili kodu inline düzenle    │
│  Ctrl + P        → Dosya hızlı aç                │
│  Ctrl + Shift+P  → Komut paleti                  │
│  Ctrl + `        → Terminal aç/kapat             │
│  Ctrl + Shift+J  → Cursor Settings               │
│  Ctrl + ,        → VS Code Settings              │
│  Ctrl + Z        → Geri al                       │
│  Ctrl + S        → Kaydet                        │
├──────────────────────────────────────────────────┤
│  CHAT REFERANSLARI                               │
├──────────────────────────────────────────────────┤
│  @bot.py         → Dosyayı bağlama ekle          │
│  @log.txt        → Log dosyasını ekle            │
│  @web            → Web araması yap               │
│  @terminal       → Terminal çıktısını ekle       │
├──────────────────────────────────────────────────┤
│  MODLAR                                          │
├──────────────────────────────────────────────────┤
│  Agent → Kod yaz/değiştir (varsayılan)           │
│  Ask   → Sadece sor/öğren (değişiklik yok)       │
│  Plan  → Büyük değişiklik öncesi plan yap        │
└──────────────────────────────────────────────────┘
```

---

*Bu döküman Cursor v0.50+ için hazırlanmıştır. Cursor sürekli güncellenmektedir; bazı ayarlar zamanla değişebilir.*
