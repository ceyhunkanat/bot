import os
import asyncio
import json
import math
import time
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from binance.um_futures import UMFutures
import websockets
import shutil

from telegram_notify import send_telegram_message

load_dotenv()
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

client = UMFutures(key=api_key, secret=api_secret, base_url="https://fapi.binance.com")

# --- Strateji Ayarları ---
mode               = "long"   # "long" veya "short"
symbol             = "ARBUSDT"
ws_symbol          = symbol.lower()
leverage           = 20
initial_usd        = 60
order_multiplier   = 1.3
target_profit_percent = 0.20
loss_trigger_percent  = 0.20
max_orders         = 5
target_entry_price = 0.5
target_rsi         = 50
interval           = "30m"
liq_wait_hours     = 1

# --- WebSocket Ayarları ---
WS_RECV_TIMEOUT  = 30    # saniye — bu sürede mesaj gelmezse bağlantıyı kes
WS_SPIKE_FILTER  = 0.05  # tek tick'te fiyat %5'ten fazla değişirse spike sayılır, atlanır

# --- Durum Değişkenleri ---
order_count        = 0
liq_triggered_flag = False
step_size          = None
tick_size          = None
total_usd          = 0
last_usd           = initial_usd
last_order_time    = 0
MIN_ORDER_INTERVAL = 0.05

# --- Pozisyon Önbelleği ---
_pos_cache    = {}
_pos_cache_ts = 0.0
POS_CACHE_TTL = 2   # saniye — REST çağrısını bu sıklıkta yapar; emir sonrası zorla yenilenir

# --- Likidasyon Tespit Eşiği ---
LIQ_DETECT_BUFFER = 0.03  # %3 — pozisyon kapanınca fiyat liq'e bu kadar yakınsa likidasyon sayılır

TELEGRAM_LOG_LEVELS = ["error", "critical", "warning"]


async def log_event(message, price=None, level="info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price_info = f" @ Fiyat: {price}" if price is not None else ""
    log_line = f"[{timestamp}] [{level.upper()}] {message}{price_info}\n"
    print(log_line.strip())

    log_file = "log.txt"
    if os.path.exists(log_file) and os.path.getsize(log_file) > 1_048_576:
        shutil.copy(log_file, "log_old.txt")
        open(log_file, "w").close()

    with open(log_file, "a") as f:
        f.write(log_line)

    if level in TELEGRAM_LOG_LEVELS:
        await send_telegram_message(log_line.strip())


async def get_rsi(symbol=symbol, interval=interval, period=14):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={period + 50}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                closes = [float(c[4]) for c in data]

                if len(closes) <= period:
                    return 50

                deltas = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]
                gains  = [max(d, 0) for d in deltas]
                losses = [-min(d, 0) for d in deltas]

                avg_gain = sum(gains[:period]) / period
                avg_loss = sum(losses[:period]) / period

                for i in range(period, len(deltas)):
                    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (avg_loss * (period - 1) + losses[i]) / period

                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                return 100 - (100 / (1 + rs))
    except Exception as e:
        await log_event(f"RSI alınamadı: {e}", level="error")
        return 50


async def get_symbol_precision(symbol):
    global step_size, tick_size
    try:
        info = client.exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                for f in s["filters"]:
                    if f["filterType"] == "LOT_SIZE":
                        step_size = float(f["stepSize"])
                    elif f["filterType"] == "PRICE_FILTER":
                        tick_size = float(f["tickSize"])
                break
        if not step_size or not tick_size:
            raise ValueError("Sembol hassasiyet verileri eksik.")
        await log_event(
            f"step_size: {step_size}, tick_size: {tick_size}, symbol: {symbol}, "
            f"kaldirac: {leverage}, yatirim: {initial_usd}, carpan: {order_multiplier}, "
            f"karhedef: {target_profit_percent}, zararhedef: {loss_trigger_percent}, "
            f"max_orders: {max_orders}, tetik: {target_entry_price}, rsi: {target_rsi}, '{interval}",
            level="critical"
        )
    except Exception as e:
        await log_event(f"Sembol hassasiyeti alınamadı: {e}", level="critical")
        raise SystemExit("Bot durduruldu. step_size ve tick_size alınamadı.")


def round_step(value, step):
    precision = int(round(-math.log10(step)))
    return round(math.floor(value / step) * step, precision)


def calculate_qty(usdt_amount, price):
    if not step_size or price <= 0:
        return 0
    return round_step(usdt_amount / price, step_size)


def set_leverage():
    try:
        res = client.change_leverage(symbol=symbol, leverage=leverage)
        print(f"Kaldıraç {res['leverage']}x olarak ayarlandı.")
    except Exception as e:
        print(f"Kaldıraç ayarlanamadı: {e}")


def set_margin_type():
    try:
        client.change_margin_type(symbol=symbol, marginType="ISOLATED")
        print(f"Marjin tipi '{symbol}' için 'ISOLATED' olarak ayarlandı.")
    except Exception as e:
        if "No need to change margin type" in str(e):
            print("Marjin tipi zaten 'ISOLATED' olarak ayarlı.")
        else:
            print(f"Marjin tipi ayarlanamadı: {e}")


async def place_futures_order(qty, price):
    side = "BUY" if mode == "long" else "SELL"
    try:
        order = client.new_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty
        )
        return order
    except Exception as e:
        await log_event(f"Emir gönderilemedi: {e}", price, level="error")
        return None


async def get_position_info(retries=5, delay=0.25):
    for attempt in range(retries):
        try:
            info = client.get_position_risk(symbol=symbol)
            if isinstance(info, list):
                if len(info) > 0:
                    return info[0]
                # Boş liste = pozisyon yok (Binance bu sembolde pozisyon olmadığında [] döndürür)
                return {"positionAmt": "0", "entryPrice": "0", "liquidationPrice": "0"}
        except Exception as e:
            await log_event(f"Pozisyon bilgisi alınamadı (deneme {attempt + 1}): {e}")
        await asyncio.sleep(delay)
    return {}


async def close_position():
    global order_count
    try:
        data = await get_position_info()
        position_amt = float(data.get("positionAmt", 0))
        if abs(position_amt) > 0:
            precision = int(round(-math.log10(step_size)))
            qty = round(math.ceil(abs(position_amt) / step_size) * step_size, precision)
            client.new_order(
                symbol=symbol,
                side="SELL" if position_amt > 0 else "BUY",
                type="MARKET",
                quantity=qty,
                reduceOnly=True
            )
            await log_event(f"Pozisyon kapatıldı: {qty} {symbol}", level="critical")
        order_count = 0
    except Exception as e:
        await log_event(f"Pozisyon kapatma hatası: {repr(e)}", level="critical")


async def get_cached_position(force=False):
    """Pozisyon bilgisini önbellekten döndürür.
    TTL dolmuşsa veya force=True ise REST'ten yeniler.
    Emir gönderildikten sonra force=True ile çağrılmalıdır.
    """
    global _pos_cache, _pos_cache_ts
    now = time.time()
    if force or (now - _pos_cache_ts) >= POS_CACHE_TTL:
        data = await get_position_info()
        if data:
            _pos_cache    = data
            _pos_cache_ts = now
    return _pos_cache



async def price_watcher():
    global order_count, liq_triggered_flag, last_order_time, total_usd, last_usd

    uri = f"wss://fstream.binance.com/market/ws/{ws_symbol}@markPrice@1s"
    set_leverage()
    set_margin_type()

    last_valid_price = 0.0
    last_known_liq   = 0.0   # pozisyon kapatılınca liq_price sıfırlanır; son bilinen değeri korur
    reconnect_delay  = 1

    while True:
        try:
            async with websockets.connect(
                uri,
                ping_interval=None
            ) as websocket:
                await log_event("WebSocket bağlantısı kuruldu.")
                reconnect_delay  = 1
                last_valid_price = 0.0   # reconnect'te spike filtresi sıfırlanır
                # Yeni bağlantıda pozisyon önbelleğini sıfırla — ilk tick'te taze veri çekilsin
                global _pos_cache, _pos_cache_ts
                _pos_cache    = {}
                _pos_cache_ts = 0.0

                while True:
                    try:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=WS_RECV_TIMEOUT)
                    except asyncio.TimeoutError:
                        await log_event(
                            f"WebSocket'ten {WS_RECV_TIMEOUT} saniyedir veri gelmedi, yeniden bağlanılıyor...",
                            level="warning"
                        )
                        break

                    data  = json.loads(msg)
                    price = float(data.get("p") or 0)   # markPrice stream'inde fiyat alanı "p"

                    if price <= 0:
                        continue

                    # ─── Spike Filtresi ──────────────────────────────────────
                    # İlk geçerli tick'te referans kur; sonraki her tick'te
                    # bir öncekinden %5'ten fazla sapan değerleri atla.
                    if last_valid_price > 0:
                        spike = abs(price - last_valid_price) / last_valid_price
                        if spike > WS_SPIKE_FILTER:
                            await log_event(
                                f"Fiyat spike'ı atlandı: {last_valid_price:.6f} → {price:.6f} "
                                f"(%{spike * 100:.1f})",
                                level="warning"
                            )
                            continue
                    last_valid_price = price

                    position_data = await get_cached_position()
                    position_amt = float(position_data.get("positionAmt", 0))
                    entry_price  = float(position_data.get("entryPrice", 0))
                    liq_price    = float(position_data.get("liquidationPrice", 0))

                    # Pozisyon açıkken son bilinen liq fiyatını güncelle
                    if position_amt != 0 and liq_price > 0:
                        last_known_liq = liq_price

                    if position_amt == 0 and order_count > 0:
                        # Pozisyon kapanmış — liq mı, manuel mi?
                        # liq_price artık 0 olabileceğinden son bilinen değeri kullan
                        check_liq = last_known_liq if last_known_liq > 0 else liq_price
                        near_liq = check_liq > 0 and (
                            price <= check_liq * (1 + LIQ_DETECT_BUFFER) if mode == "long"
                            else price >= check_liq * (1 - LIQ_DETECT_BUFFER)
                        )
                        if near_liq:
                            liq_triggered_flag = True
                            await log_event(
                                f"Likidasyon tespit edildi (fiyat liq'e yakındı). "
                                f"Fiyat: {price}, Liq: {check_liq}",
                                price, level="critical"
                            )
                        else:
                            await log_event("Pozisyon manuel kapatılmış görünüyor. Bot sonlandırılıyor.", price, level="critical")
                            order_count     = 0
                            total_usd       = 0
                            last_usd        = initial_usd
                            last_order_time = 0
                        return
                    elif position_amt == 0:
                        entry_condition = price <= target_entry_price if mode == "long" else price >= target_entry_price
                        if entry_condition:
                            qty = calculate_qty(initial_usd, price)
                            if qty > 0:
                                order = await place_futures_order(qty, price)
                                if order:
                                    await asyncio.sleep(0.1)
                                    order_count = 1
                                    total_usd = initial_usd
                                    await get_cached_position(force=True)
                                    await log_event(f"İlk emir gönderildi ({mode.upper()}): {qty} adet {symbol}", price, level="critical")
                            else:
                                await log_event("İlk emir için miktar hesaplanamadı.", price)
                        await asyncio.sleep(1)
                        continue

                    if mode == "long":
                        liq_hit = liq_price > 0 and price <= liq_price
                    else:
                        liq_hit = liq_price > 0 and price >= liq_price

                    if liq_hit:
                        await log_event(f"Likidasyon gerçekleşti! Fiyat: {price}, Liq: {liq_price}", price, level="critical")
                        liq_triggered_flag = True
                        return

                    if mode == "long":
                        loss_percent = ((entry_price - price) / entry_price) * leverage
                    else:
                        loss_percent = ((price - entry_price) / entry_price) * leverage

                    current_time = time.time()

                    if (
                        loss_percent >= loss_trigger_percent
                        and order_count < max_orders
                        and current_time - last_order_time >= MIN_ORDER_INTERVAL
                    ):
                        new_usd = last_usd * order_multiplier
                        qty = calculate_qty(new_usd, price)
                        if qty > 0:
                            order = await place_futures_order(qty, price)
                            if order:
                                order_count += 1
                                total_usd += new_usd
                                last_usd = new_usd
                                last_order_time = current_time
                                avg_label = "Averaging down" if mode == "long" else "Averaging up"
                                await log_event(
                                    f"{avg_label} #{order_count} yapıldı. "
                                    f"Yeni alım: {qty}, Toplam Yatırım: {total_usd}",
                                    price, level="critical"
                                )
                                position_data = await get_cached_position(force=True)
                                entry_price = float(position_data.get("entryPrice", 0))
                                liq_price   = float(position_data.get("liquidationPrice", 0))
                                await log_event(f"Yeni giriş fiyatı güncellendi: {entry_price}, Liq: {liq_price}", price, level="critical")
                        else:
                            await log_event("Hesaplanan miktar sıfır (qty == 0).", price, level="error")

                    if mode == "long":
                        target_price = round_step(entry_price * (1 + target_profit_percent / leverage), tick_size)
                        profit_hit = price >= target_price
                    else:
                        target_price = round_step(entry_price * (1 - target_profit_percent / leverage), tick_size)
                        profit_hit = price <= target_price

                    if profit_hit:
                        await log_event("Kâr hedefine ulaşıldı. Pozisyon kapatılıyor...", price, level="critical")
                        await close_position()
                        return

                    await asyncio.sleep(0.1)

        except websockets.ConnectionClosedError as e:
            await log_event(f"WebSocket bağlantısı kapatıldı: {e}. {reconnect_delay} saniye sonra yeniden bağlanılıyor...")
        except Exception as e:
            await log_event(f"WebSocket genel hatası: {e}. {reconnect_delay} saniye sonra yeniden denenecek...")

        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, 60)


async def wait_for_rsi_and_restart():
    global order_count, total_usd, last_usd, last_order_time, liq_triggered_flag

    liq_wait_done = False

    while True:
        position_data = await get_position_info()
        position_amt  = float(position_data.get("positionAmt", 0))

        if position_amt == 0:
            if liq_triggered_flag and not liq_wait_done:
                await log_event(f"Likidasyon sonrası {liq_wait_hours} saat bekleme başlatıldı.", level="critical")
                await asyncio.sleep(liq_wait_hours * 3600)
                liq_wait_done = True
                liq_triggered_flag = False
                await log_event(f"{liq_wait_hours} saatlik bekleme tamamlandı. RSI izleme başlıyor.", level="critical")

            rsi = await get_rsi()
            await log_event(f"RSI kontrolü: {rsi:.2f}")

            rsi_condition = rsi <= target_rsi if mode == "long" else rsi >= target_rsi
            rsi_label = f"altına indi ({rsi:.2f} ≤ {target_rsi})" if mode == "long" else f"üstüne çıktı ({rsi:.2f} ≥ {target_rsi})"

            if rsi_condition:
                await log_event(f"RSI {rsi_label}. Bot yeniden başlatılıyor.", level="critical")

                order_count        = 0
                total_usd          = 0
                last_usd           = initial_usd
                last_order_time    = 0
                liq_triggered_flag = False
                liq_wait_done      = False

                await price_watcher()

        await asyncio.sleep(30)


async def main():
    global order_count

    await get_symbol_precision(symbol)

    if step_size is None:
        await log_event("step_size alınamadı, bot başlatılamıyor.")
        return

    position_info = await get_position_info()
    position_amt  = float(position_info.get("positionAmt", 0))

    if position_amt != 0:
        order_count = 1
        await log_event(
            f"{symbol} sembolünde zaten açık pozisyon var. "
            f"order_count=1 olarak ayarlandı, DCA hakkı korundu. Bot izlemeye geçiyor.",
            level="warning"
        )
        await price_watcher()

    await wait_for_rsi_and_restart()


if __name__ == "__main__":
    asyncio.run(main())
