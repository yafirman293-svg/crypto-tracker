python
import requests
import time
import os

Konfigurasi
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://discord.com/api/webhooks/1570730200369598606/Lee53aJ8qRmhwBVNCnFCEyH4lOlBFGEymZMvHfpi2x1DZscoX0g6v18k_LHlH1ItZAkM")
INTERVAL = 3600  # 1 jam

Ambil harga 50 coin
def fetch_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 50, "page": 1, "sparkline": "true"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

Hitung RSI (sederhana)
def get_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

Hitung SMA
def get_sma(prices, period=4):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

Analisis 1 coin
def analyze(coin, data_4h):
    name = coin['name'].upper()
    symbol = coin['symbol'].upper()
    price = coin['current_price']
    pct = coin['price_change_percentage_24h'] or 0
    high = coin['high_24h']
    low = coin['low_24h']

    if price is None:
        return None

    # Ambil data 4 jam terakhir
    prices_4h = [p[1] for p in data_4h.get('prices', [])]
    volumes_4h = [v[1] for v in data_4h.get('total_volumes', [])]

    # Hitung indikator
    sma_4h = get_sma(prices_4h, 4)
    sma_24h = get_sma(prices_4h, 24)
    rsi_14 = get_rsi(prices_4h, 14)

    # Volume ratio
    if len(volumes_4h) >= 24:
        avg_vol = sum(volumes_4h[-24:]) / 24
        prev_vol = sum(volumes_4h[-48:-24]) / 24 if len(volumes_4h) >= 48 else avg_vol
        vol_ratio = avg_vol / prev_vol if prev_vol > 0 else 1
    else:
        vol_ratio = 1

    # Trend
    if sma_4h and sma_24h:
        trend = "BULLISH" if sma_4h > sma_24h else "BEARISH"
    else:
        trend = "NEUTRAL"

    # Signal
    rsi_signal = "NEUTRAL"
    if rsi_14 is not None:
        if rsi_14 > 70:
            rsi_signal = "SELL"
        elif rsi_14 < 30:
            rsi_signal = "BUY"

    # Combine signal
    if rsi_signal == "BUY" and vol_ratio > 1.5 and pct > 0:
        signal = "BUY (RSI + Volume)"
        tp = price * 1.03
        sl = price * 0.98
    elif rsi_signal == "BUY":
        signal = "BUY"
        tp = price * 1.02
        sl = price * 0.99
    elif rsi_signal == "SELL":
        signal = "SELL"
        tp = price * 0.98
        sl = price * 1.02
    else:
        signal = "HOLD"
        tp = price * 1.01
        sl = price * 0.99

    return {
        'name': name,
        'symbol': symbol,
        'price': price,
        'pct': pct,
        'trend': trend,
        'rsi': rsi_14,
        'signal': signal,
        'tp': tp,
        'sl': sl
    }

Kirim ke Discord
def send_to_discord(message):
    requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)

Main loop
def main():
    print("🚀 Trading Bot dimulai...")
    print(f"⏱️  Interval: 1 jam")

    while True:
        try:
            # Ambil data
            coins = fetch_prices()
            print(f"✓ Ambil {len(coins)} coins")

            # Kirim ke Discord
            lines = ["📊 Trading Signal Bot 😊"]

            for coin in coins[:10]:
                result = analyze(coin, None)  # Ganti None kalau butuh 4h data
                if result is None:
                    continue
                lines.append(f"• {result['name']} ({result['symbol']}): ${result['price']:,.2f}")
                lines.append(f"  📊 24h: {result['pct']:+.2f}%")
                lines.append(f"  📈 Signal: {result['signal']}")
                lines.append(f"  🎯 TP: ${result['tp']:,.2f} | 🛑 SL: ${result['sl']:,.2f}")

            send_to_discord("\n".join(lines))
            print(f"✅ Kirim ke Discord")

            time.sleep(INTERVAL)

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(300)

if name == "main":
    main()
