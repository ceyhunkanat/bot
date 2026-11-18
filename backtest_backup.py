"""
Binance Futures Backtesting + Parametre Optimizasyonu
=====================================================
Bot'tan bağımsız çalışır. Gerçek para riske atılmaz.

Kullanım:
    python3 backtest.py                              # Varsayılan sembol/ayarlarla çalıştır
    python3 backtest.py --mode short                 # Short mod
    python3 backtest.py --symbol BTCUSDT --mode long
    python3 backtest.py --interval 15m --days 60 --mode long

Sembol değiştirmek için dosyanın başındaki SYMBOL sabitini düzenle:
    SYMBOL = "BTCUSDT"  ← buradan değiştir (--symbol argümanı yoksa bu kullanılır)

RSI Arama Alanı (otomatik seçilir):
    Long  → [20, 25, 30, 35, 40, 45]  (aşırı satım bölgesi)
    Short → [55, 60, 65, 70, 75, 80]  (aşırı alım bölgesi)

Sonuçlar hem terminale hem de backtestlog.txt dosyasına yazılır.
"""

import argparse
import math
import itertools
import requests
from datetime import datetime, timedelta


# ─── Sabit Parametreler (Optimize Edilmez) ──────────────────────────────────
SYMBOL      = "APEUSDT"   # ← buradan değiştir
LEVERAGE    = 8
INITIAL_USD = 40
MAX_ORDERS  = 5

# ─── Moda Özel RSI Arama Alanı ──────────────────────────────────────────────
RSI_GRID = {
    "long":  [20, 25, 30, 35, 40, 45],   # aşırı satım bölgesi
    "short": [55, 60, 65, 70, 75, 80],   # aşırı alım bölgesi
}

# ─── Diğer Optimizasyon Parametreleri ───────────────────────────────────────
OPTIMIZE_GRID = {
    "loss_trigger_percent":  [0.50, 0.55, 0.60, 0.65, 0.70, 0.75],
    "target_profit_percent": [0.30, 0.40, 0.50, 0.60, 0.70],
    "order_multiplier":      [1.2, 1.3, 1.4, 1.5],
}


# ─── Log Dosyası ─────────────────────────────────────────────────────────────
LOG_FILE = "backtestlog.txt"

_log_fh = None

def log_open(symbol, interval, days, mode):
    global _log_fh
    _log_fh = open(LOG_FILE, "a", encoding="utf-8")
    header = (
        f"\n{'#' * 60}\n"
        f"# Backtest Başlangıcı : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"# Sembol: {symbol} | Aralık: {interval} | Süre: {days} gün | Mod: {mode.upper()}\n"
        f"{'#' * 60}\n"
    )
    _log_fh.write(header)
    _log_fh.flush()

def log_close():
    global _log_fh
    if _log_fh:
        _log_fh.write("\n")
        _log_fh.close()
        _log_fh = None

def log(text=""):
    print(text)
    if _log_fh:
        _log_fh.write(text + "\n")
        _log_fh.flush()


# ─── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────

def round_step(value, step):
    precision = int(round(-math.log10(step)))
    return round(math.floor(value / step) * step, precision)


def calculate_qty(usdt_amount, price, step_size=0.1):
    if price <= 0:
        return 0
    return round_step(usdt_amount / price, step_size)


def compute_rsi_series(closes, period=14):
    """Tüm kapanış serisine ait RSI değerlerini tek geçişte (O(n)) döndürür."""
    rsis = [50.0] * len(closes)
    if len(closes) <= period:
        return rsis

    deltas = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]
    gains  = [max(d, 0) for d in deltas]
    losses = [-min(d, 0) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsis[i + 1] = 100 - (100 / (1 + rs))

    return rsis


def fetch_klines(symbol, interval, days):
    end_ms   = int(datetime.utcnow().timestamp() * 1000)
    start_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    url      = "https://fapi.binance.com/fapi/v1/klines"
    klines   = []

    log(f"  {symbol} için {days} günlük {interval} veri çekiliyor...")

    while start_ms < end_ms:
        resp = requests.get(url, params={
            "symbol": symbol, "interval": interval,
            "startTime": start_ms, "endTime": end_ms, "limit": 1000,
        }, timeout=10)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        klines.extend(batch)
        start_ms = batch[-1][0] + 1
        if len(batch) < 1000:
            break

    log(f"  {len(klines)} mum yüklendi.\n")
    return klines


# ─── Simülasyon Motoru ───────────────────────────────────────────────────────

def simulate(klines, params, step_size=0.1, tick_size=0.0001):
    """
    OHLC tabanlı simülasyon:
      - Giriş       : kapanış fiyatında (RSI kapanış mumuna göre hesaplanır)
      - Likidasyon  : LONG → mum dibi (LOW), SHORT → mum tepesi (HIGH)
      - DCA tetikle : LONG → mum dibi (LOW), SHORT → mum tepesi (HIGH)
      - Kâr hedefi  : LONG → mum tepesi (HIGH), SHORT → mum dibi (LOW)
    Bu sıra, her mum içindeki en kötü senaryonun (likidasyon/DCA) en iyi
    senaryodan (kâr) önce değerlendirilmesini sağlar.
    """
    order_multiplier  = params["order_multiplier"]
    target_profit_pct = params["target_profit_percent"]
    loss_trigger_pct  = params["loss_trigger_percent"]
    target_rsi        = params["target_rsi"]
    mode              = params["mode"]

    closes = [float(k[4]) for k in klines]
    highs  = [float(k[2]) for k in klines]
    lows   = [float(k[3]) for k in klines]
    rsis   = compute_rsi_series(closes)

    total_pnl       = 0.0
    total_trades    = 0
    winning_trades  = 0
    liquidations    = 0
    max_drawdown    = 0.0

    in_position     = False
    order_count     = 0
    entry_price     = 0.0
    position_qty    = 0.0
    total_usd_spent = 0.0
    last_usd        = INITIAL_USD
    liq_price       = 0.0

    for i in range(len(closes)):
        close = closes[i]
        high  = highs[i]
        low   = lows[i]
        rsi   = rsis[i]

        # ─── Pozisyon Yok: Giriş Koşulu (sadece RSI) ────────────────────────
        if not in_position:
            rsi_ok = rsi <= target_rsi if mode == "long" else rsi >= target_rsi
            if rsi_ok:
                qty = calculate_qty(INITIAL_USD, close, step_size)
                if qty <= 0:
                    continue
                in_position     = True
                order_count     = 1
                entry_price     = close
                position_qty    = qty
                total_usd_spent = INITIAL_USD
                last_usd        = INITIAL_USD
                liq_price       = (
                    entry_price * (1 - 1 / LEVERAGE) if mode == "long"
                    else entry_price * (1 + 1 / LEVERAGE)
                )
            continue

        # LONG: en kötü fiyat → LOW | SHORT: en kötü fiyat → HIGH
        adverse_price = low  if mode == "long" else high
        # LONG: en iyi fiyat → HIGH | SHORT: en iyi fiyat → LOW
        best_price    = high if mode == "long" else low

        # ─── Likidasyon Kontrolü (mum dibi/tepesi ile) ───────────────────────
        liq_hit = (adverse_price <= liq_price) if mode == "long" else (adverse_price >= liq_price)
        if liq_hit:
            # total_usd_spent = pozisyon büyüklüğü; gerçek marjin = pozisyon / kaldıraç
            margin_lost  = total_usd_spent / LEVERAGE
            total_pnl   += -margin_lost
            max_drawdown  = min(max_drawdown, -margin_lost)
            liquidations += 1
            total_trades += 1
            in_position   = False
            order_count   = 0
            continue

        # ─── DCA Kontrolü (mum dibi/tepesi ile, birden fazla tetik mümkün) ────
        # Bir mum içinde birden fazla DCA eşiği geçilebilir (hızlı düşüş/yükseliş).
        # Her DCA sonrası yeni entry_price'a göre koşul yeniden değerlendirilir.
        while order_count < MAX_ORDERS:
            loss_pct = (
                ((entry_price - adverse_price) / entry_price) * LEVERAGE if mode == "long"
                else ((adverse_price - entry_price) / entry_price) * LEVERAGE
            )
            if loss_pct < loss_trigger_pct:
                break
            # DCA emri mum kapanışında gerçekleşir (muhafazakâr)
            dca_price = close
            new_usd   = last_usd * order_multiplier
            qty       = calculate_qty(new_usd, dca_price, step_size)
            if qty <= 0:
                break
            total_cost      = total_usd_spent + new_usd
            total_qty       = position_qty + qty
            entry_price     = total_cost / total_qty
            position_qty    = total_qty
            total_usd_spent = total_cost
            last_usd        = new_usd
            order_count    += 1
            liq_price       = (
                entry_price * (1 - 1 / LEVERAGE) if mode == "long"
                else entry_price * (1 + 1 / LEVERAGE)
            )

        # ─── Kâr Hedefi Kontrolü (mum tepesi/dibi ile) ───────────────────────
        if mode == "long":
            target_price = round_step(entry_price * (1 + target_profit_pct / LEVERAGE), tick_size)
            profit_hit   = best_price >= target_price
        else:
            target_price = round_step(entry_price * (1 - target_profit_pct / LEVERAGE), tick_size)
            profit_hit   = best_price <= target_price

        if profit_hit:
            exit_price = target_price
            pnl = (
                position_qty * (exit_price - entry_price) if mode == "long"
                else position_qty * (entry_price - exit_price)
            )
            total_pnl      += pnl
            max_drawdown    = min(max_drawdown, pnl)
            total_trades   += 1
            winning_trades += 1 if pnl > 0 else 0
            in_position     = False
            order_count     = 0
            last_usd        = INITIAL_USD

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    return {
        "total_pnl":      round(total_pnl, 2),
        "total_trades":   total_trades,
        "winning_trades": winning_trades,
        "win_rate":       round(win_rate, 1),
        "liquidations":   liquidations,
        "max_drawdown":   round(max_drawdown, 2),
    }


# ─── Parametre Optimizasyonu ─────────────────────────────────────────────────

def run_optimize(klines, mode):
    rsi_values = RSI_GRID[mode]
    keys       = ["target_rsi"] + list(OPTIMIZE_GRID.keys())
    values     = [rsi_values]   + list(OPTIMIZE_GRID.values())
    combos     = list(itertools.product(*values))

    log(f"  {len(combos)} kombinasyon test ediliyor (RSI aralığı: {rsi_values[0]}–{rsi_values[-1]})...\n")

    results = []
    for combo in combos:
        params = dict(zip(keys, combo))
        params["mode"] = mode
        result = simulate(klines, params)
        results.append((params, result))

    results.sort(key=lambda x: x[1]["total_pnl"], reverse=True)

    log("=" * 67)
    log(f"  EN İYİ 15 PARAMETRE KOMBİNASYONU — MOD: {mode.upper()} (PnL'e göre sıralı)")
    log("=" * 67)
    log(f"  {'rsi':>5} {'loss_trig':>9} {'profit':>7} {'mult':>5} | {'PnL':>8} {'işlem':>6} {'liq':>4} {'win%':>6}")
    log("-" * 67)

    for p, r in results[:15]:
        log(
            f"  {p['target_rsi']:>5} "
            f"{p['loss_trigger_percent']:>9.2f} "
            f"{p['target_profit_percent']:>7.2f} "
            f"{p['order_multiplier']:>5.1f} | "
            f"${r['total_pnl']:>7.2f} "
            f"{r['total_trades']:>6} "
            f"{r['liquidations']:>4} "
            f"{r['win_rate']:>5.1f}%"
        )

    log("=" * 67)

    if results[0][1]["total_trades"] == 0:
        log("\n  UYARI: Hiçbir kombinasyonda işlem gerçekleşmedi.")
        log("  Farklı --days veya --interval değeri deneyin.")
        return

    best_p, best_r = results[0]
    log("\n  EN İYİ PARAMETRE SETİ:")
    log(f"    target_rsi            = {best_p['target_rsi']}")
    log(f"    loss_trigger_percent  = {best_p['loss_trigger_percent']}")
    log(f"    target_profit_percent = {best_p['target_profit_percent']}")
    log(f"    order_multiplier      = {best_p['order_multiplier']}")
    log(f"\n    Tahmini PnL  : ${best_r['total_pnl']}")
    log(f"    Toplam İşlem : {best_r['total_trades']}")
    log(f"    Likidasyon   : {best_r['liquidations']}")
    log(f"    Kazanma Oranı: %{best_r['win_rate']}")


# ─── Ana Giriş ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Binance Futures Backtester")
    parser.add_argument("--symbol",   default=SYMBOL,    help="İşlem çifti (örn. APEUSDT)")
    parser.add_argument("--interval", default="5m",      help="Mum aralığı (örn. 5m, 15m, 1h)")
    parser.add_argument("--days",     default=90, type=int, help="Kaç günlük veri (varsayılan: 90)")
    parser.add_argument("--mode",     default="long",    help="long veya short")
    args = parser.parse_args()

    log_open(args.symbol, args.interval, args.days, args.mode)

    log("=" * 55)
    log("  Binance Futures Backtester")
    log(f"  Sembol   : {args.symbol}")
    log(f"  Aralık   : {args.interval}")
    log(f"  Süre     : {args.days} gün")
    log(f"  Mod      : {args.mode.upper()}")
    log(f"  Leverage : {LEVERAGE}x  |  Başlangıç: ${INITIAL_USD}  |  Max DCA: {MAX_ORDERS}")
    log("=" * 55 + "\n")

    try:
        klines = fetch_klines(args.symbol, args.interval, args.days)
    except Exception as e:
        log(f"  HATA: Veri çekilemedi — {e}")
        log_close()
        return

    run_optimize(klines, args.mode)

    log(f"\n  Sonuçlar '{LOG_FILE}' dosyasına kaydedildi.")
    log_close()


if __name__ == "__main__":
    main()
