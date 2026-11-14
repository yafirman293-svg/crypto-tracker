import requests
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1570730200369598606/Lee53aJ8qRmhwBVNCnFCEyH4lOlBFGEymZMvHfpi2x1DZscoX0g6v18k_LHlH1ItZAkM"
INTERVAL = 3600  # 1 jam = 3600 detik

def fetch_top_coins(limit=50):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "true"
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_4h_data(coin_id, days=7):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "1h"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def calculate_rsi(prices, period=14):
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

def calculate_sma(prices, period=4):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def analyze_coin(coin, price_data):
    name = coin['name'].upper()
    symbol = coin['symbol'].upper()
    price = coin['current_price']
    pct = coin['price_change_percentage_24h']
    high = coin['high_24h']
    low = coin['low_24h']
    market_cap = coin.get('market_cap')
    volume = coin.get('total_volume')

    if price is None or price_data is None:
        return None

    if pct is None:
        pct = 0

    prices_4h = [p[1] for p in price_data.get('prices', [])]
    volumes_4h = [v[1] for v in price_data.get('total_volumes', [])]

    # SMA 4h & 24h
    sma_4h = calculate_sma(prices_4h, 4)
    sma_24h = calculate_sma(prices_4h, 24)

    # RSI 14
    rsi_14 = calculate_rsi(prices_4h, 14)

    # Volume ratio
    if len(volumes_4h) >= 24:
        avg_vol_24h = sum(volumes_4h[-24:]) / 24
        avg_vol_prev = sum(volumes_4h[-48:-24]) / 24 if len(volumes_4h) >= 48 else avg_vol_24h
        vol_ratio = avg_vol_24h / avg_vol_prev if avg_vol_prev > 0 else 1
    else:
        vol_ratio = 1

    # Trend
    if sma_4h and sma_24h:
        if sma_4h > sma_24h:
            trend = "🟢 BULLISH (4h > 24h)"
        else:
            trend = "🔴 BEARISH (4h < 24h)"
    else:
        trend = "🟡 NEUTRAL"

    # Signal dari RSI
    if rsi_14 is not None:
        if rsi_14 > 70:
            rsi_action = "SELL"
            rsi_signal = "🔴 OVERBOUGHT"
        elif rsi_14 < 30:
            rsi_action = "BUY"
            rsi_signal = "🟢 OVERSOLD"
        else:
            rsi_action = "HOLD"
            rsi_signal = "🟡 NEUTRAL"
    else:
        rsi_action = "HOLD"
        rsi_signal = "🟡 N/A"

    # Signal gabungan
    if rsi_action == "BUY" and vol_ratio > 1.5 and pct > 0:
        signal = "📈 BUY (RSI + Volume)"
        tp = price * 1.03
        sl = price * 0.98
    elif rsi_action == "BUY":
        signal = "📈 BUY"
        tp = price * 1.02
        sl = price * 0.99
    elif rsi_action == "SELL":
        signal = "📉 SELL"
        tp = price * 0.98
        sl = price * 1.02
    else:
        signal = "⏸️ HOLD"
        tp = price * 1.01
        sl = price * 0.99

    return {
        'name': name,
        'symbol': symbol,
        'price': price,
        'pct': pct,
        'trend': trend,
        'rsi': rsi_14,
        'rsi_signal': rsi_signal,
        'signal': signal,
        'tp': tp,
        'sl': sl,
        'market_cap': market_cap,
        'volume': volume,
        'vol_ratio': vol_ratio,
        'high': high,
        'low': low,
        'sma_4h': sma_4h,
        'sma_24h': sma_24h
    }

def send_to_discord(message):
    # Memecah pesan jika melebihi batas 2000 karakter Discord
    if len(message) > 2000:
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            requests.post(WEBHOOK_URL, json={"content": chunk}, timeout=10)
            time.sleep(1)
    else:
        requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)

def main():
    print("🚀 Trading Signal Bot + Full Analysis dimulai...")
    print(f"🔗 Webhook: {WEBHOOK_URL[-20:]}")
    print(f"⏱️  Interval: 1 jam")
    print(f"📊 Tracking 50 top coins (Full Analysis)")
    print()

    while True:
        try:
            coins = fetch_top_coins(limit=50)
            print(f"✓ Ambil {len(coins)} top coins ✅")

            major_ids = [c['id'] for c in coins[:10]]
            major_4h_data = {}
            for cid in major_ids:
                try:
                    time.sleep(2)  # Anti rate limit CoinGecko
                    data = fetch_4h_data(cid)
                    major_4h_data[cid] = data
                    print(f"✓ Ambil 4h data {cid} ({len(data.get('prices', []))} poin)")
                except Exception as e:
                    print(f"⚠️ Gagal ambil 4h data {cid}: {e}")
                    major_4h_data[cid] = None

            lines = ["📊 **Trading Signal Bot + Full Analysis** 🚀", ""]

            # Analisis top 10 dengan full indicators
            for coin in coins[:10]:
                cid = coin['id']
                result = analyze_coin(coin, major_4h_data.get(cid))
                if result is None:
                    continue

                lines.append(f"• **{result['name']} ({result['symbol']})**: ${result['price']:,.2f}")
                lines.append(f"  📊 24h: {result['pct']:+.2f}% | Cap: ${result['market_cap']:,.0f}" if result['market_cap'] else f"  📊 24h: {result['pct']:+.2f}%")
                lines.append(f"  📊 High: ${result['high']:,.2f} | Low: ${result['low']:,.2f}")
                
                sma_4h_val = f"${result['sma_4h']:,.2f}" if result['sma_4h'] else "N/A"
                sma_24h_val = f"${result['sma_24h']:,.2f}" if result['sma_24h'] else "N/A"
                lines.append(f"  📊 SMA 4h: {sma_4h_val} | SMA 24h: {sma_24h_val}")
                
                rsi_val = f"{result['rsi']:.1f}" if result['rsi'] else "N/A"
                lines.append(f"  📊 RSI(14): {rsi_val} ({result['rsi_signal']})")
                lines.append(f"  📊 Vol Ratio: {result['vol_ratio']:.2f}x")
                lines.append(f"  🎯 {result['trend']}")
                lines.append(f"  🎯 Signal: {result['signal']}")
                lines.append(f"  🎯 TP: ${result['tp']:,.2f} | SL: ${result['sl']:,.2f}")
                lines.append("")

            # Rincian singkat sisa koin
            lines.append("📋 **Ringkasan Koin Lainnya:**")
            for coin in coins[10:]:
                name = coin['name'].upper()
                symbol = coin['symbol'].upper()
                price = coin['current_price']
                pct = coin['price_change_percentage_24h']
                if price is None or pct is None:
                    continue
                change_str = f"🟢 +{pct:.2f}%" if pct > 0 else f"🔴 {pct:.2f}%"
                lines.append(f"• {symbol}: ${price:,.2f} ({change_str})")

            message = "\n".join(lines)
            send_to_discord(message)

            print(f"✅ Update terkirim ke Discord ({len(coins)} coins)")
            time.sleep(INTERVAL)

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()