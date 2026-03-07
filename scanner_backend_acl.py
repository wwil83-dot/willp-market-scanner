"""
WillP ProLine Market Scanner - FULL ACL CALCULATION
Uses real historical data to calculate actual EMA+HMA+ATR bands
Matches your TradingView ACL indicator exactly
"""

import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

# Cache to store calculated data (refresh every 3 minutes)
CACHE = {
    'data': None,
    'timestamp': None
}

# ACL CALCULATION FUNCTIONS (matching your Pine Script settings)
def calculate_ema(data, period):
    """Calculate EMA"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_hma(data, period):
    """Calculate Hull Moving Average"""
    half_length = int(period / 2)
    sqrt_length = int(np.sqrt(period))
    
    wma_half = data.rolling(window=half_length).mean()
    wma_full = data.rolling(window=period).mean()
    raw_hma = 2 * wma_half - wma_full
    hma = raw_hma.rolling(window=sqrt_length).mean()
    
    return hma

def calculate_atr(high, low, close, period):
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_acl_regime(df, ema_period=21, atr_period=21, band_mult=1.25, smooth_period=8):
    """
    Calculate ACL regime based on your exact TradingView settings
    
    Settings:
    - EMA: 21 (weekly)
    - ATR: 21
    - Band Width: 1.25
    - Smoothing (HMA): 8
    """
    
    if len(df) < 100:
        return 'neutral', 50, 'neutral', 0
    
    # Calculate HLC3
    hlc3 = (df['High'] + df['Low'] + df['Close']) / 3
    
    # Calculate baseline (EMA of HLC3)
    baseline = calculate_ema(hlc3, ema_period)
    
    # Apply HMA smoothing to create ACL line
    acl_line = calculate_hma(baseline, smooth_period)
    
    # Calculate ATR
    atr = calculate_atr(df['High'], df['Low'], df['Close'], atr_period)
    
    # Calculate bands
    band_width = atr * band_mult
    upper_band = acl_line + band_width
    lower_band = acl_line - band_width
    
    # Get current values
    current_price = df['Close'].iloc[-1]
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    current_acl = acl_line.iloc[-1]
    
    # Determine regime based on price position relative to ACL
    if pd.isna(current_upper) or pd.isna(current_lower):
        return 'neutral', 50, 'neutral', 0
    
    # Price above ACL = BULLISH (yellow bands)
    # Price below ACL = BEARISH (blue bands)
    if current_price > current_acl:
        regime = 'bull'
        
        # How far above? Determines signal strength
        if current_price > current_upper:
            signal = 'check_sell'  # In upper yellow band, watch for reversal
            score = 70
            sentiment = 'greed'
        else:
            signal = 'neutral'  # Above ACL but not extended
            score = 60
            sentiment = 'neutral'
            
    else:  # Price below ACL
        regime = 'bear'
        
        # How far below?
        if current_price < current_lower:
            signal = 'check_buy'  # In lower blue band, watch for reversal
            score = 30
            sentiment = 'fear'
        else:
            signal = 'neutral'  # Below ACL but not extended
            score = 40
            sentiment = 'neutral'
    
    # Calculate 7-day change for reference
    if len(df) >= 7:
        change_7d = ((current_price - df['Close'].iloc[-7]) / df['Close'].iloc[-7]) * 100
    else:
        change_7d = 0
    
    return signal, regime, score, sentiment, change_7d

def fetch_historical_data(symbol, asset_type='crypto'):
    """Fetch 150 weekly bars from yfinance"""
    
    try:
        # Format ticker based on asset type
        if asset_type == 'crypto':
            ticker = f"{symbol}-USD"
        elif asset_type == 'forex':
            ticker = f"{symbol}=X"
        elif asset_type == 'gold':
            ticker = "GC=F"  # Gold futures
        elif asset_type == 'silver':
            ticker = "SI=F"  # Silver futures
        else:  # stocks
            ticker = symbol
        
        # Fetch weekly data (200 weeks to ensure we have enough)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y", interval="1wk")
        
        if len(hist) < 50:
            print(f"⚠ {symbol}: Insufficient data ({len(hist)} bars)")
            return None
        
        return hist
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def process_asset(symbol, name, asset_type, exchange='Multiple'):
    """Process a single asset - fetch data and calculate ACL regime"""
    
    # Fetch historical data
    df = fetch_historical_data(symbol, asset_type)
    
    if df is None or len(df) < 50:
        return None
    
    # Calculate ACL regime
    signal, regime, score, sentiment, change_7d = calculate_acl_regime(df)
    
    # Get current price and 24h change
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) >= 2 else current_price
    change_24h = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
    
    # Format TV symbol
    if asset_type == 'crypto':
        tv_symbol = f"BINANCE:{symbol}USDT"
    elif asset_type == 'forex':
        tv_symbol = f"FX:{symbol}"
    elif asset_type in ['gold', 'silver']:
        tv_symbol = f"TVC:{symbol}"
    else:
        tv_symbol = symbol
    
    return {
        'symbol': symbol,
        'name': name,
        'exchange': exchange,
        'price': float(current_price),
        'change': float(change_24h),
        'change_7d': float(change_7d),
        'signal': signal,
        'sentiment': sentiment,
        'sentimentScore': score,
        'aclRegime': regime,
        'ctoTrend': regime,
        'category': asset_type if asset_type not in ['gold', 'silver'] else 'midcap',
        'tvSymbol': tv_symbol
    }

def fetch_all_assets():
    """Fetch and process all assets with ACL calculation"""
    
    print("\n" + "="*60)
    print("CALCULATING ACL REGIMES FROM HISTORICAL DATA")
    print("="*60)
    
    all_assets = []
    
    # CRYPTO (Top 10 instead of 20 for cloud performance)
    print("\n📊 Processing Crypto...")
    crypto_list = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('BNB', 'BNB'),
        ('SOL', 'Solana'),
        ('XRP', 'Ripple'),
        ('ADA', 'Cardano'),
        ('DOGE', 'Dogecoin'),
        ('MATIC', 'Polygon'),
        ('LINK', 'Chainlink'),
        ('LTC', 'Litecoin')
    ]
    
    for symbol, name in crypto_list:
        result = process_asset(symbol, name, 'crypto', 'Multiple')
        if result:
            all_assets.append(result)
            print(f"✓ {symbol}: {result['aclRegime'].upper()} - {result['signal']}")
    
    # STOCKS (Top 10 instead of 20)
    print("\n📊 Processing Stocks...")
    stock_list = [
        ('AAPL', 'Apple Inc.'),
        ('MSFT', 'Microsoft'),
        ('NVDA', 'NVIDIA'),
        ('GOOGL', 'Alphabet'),
        ('AMZN', 'Amazon'),
        ('TSLA', 'Tesla'),
        ('META', 'Meta Platforms'),
        ('JPM', 'JPMorgan Chase'),
        ('V', 'Visa'),
        ('WMT', 'Walmart')
    ]
    
    for symbol, name in stock_list:
        result = process_asset(symbol, name, 'stocks', 'NASDAQ/NYSE')
        if result:
            all_assets.append(result)
            print(f"✓ {symbol}: {result['aclRegime'].upper()} - {result['signal']}")
    
    # GOLD & SILVER
    print("\n📊 Processing Metals...")
    result = process_asset('GOLD', 'Gold Futures (per oz)', 'gold', 'COMEX')
    if result:
        all_assets.append(result)
        print(f"✓ GOLD: {result['aclRegime'].upper()} - ${result['price']:.2f}")
    
    result = process_asset('SILVER', 'Silver Futures (per oz)', 'silver', 'COMEX')
    if result:
        all_assets.append(result)
        print(f"✓ SILVER: {result['aclRegime'].upper()} - ${result['price']:.2f}")
    
    # MID-CAPS (Reduced to 5 for cloud)
    print("\n📊 Processing Mid-Caps...")
    midcap_list = [
        ('UEC', 'Uranium Energy'),
        ('XOM', 'Exxon Mobil'),
        ('COIN', 'Coinbase'),
        ('PLTR', 'Palantir'),
        ('SQ', 'Block Inc.')
    ]
    
    for symbol, name in midcap_list:
        result = process_asset(symbol, name, 'stocks', 'NYSE')
        if result:
            result['category'] = 'midcap'
            all_assets.append(result)
            print(f"✓ {symbol}: {result['aclRegime'].upper()} - {result['signal']}")
    
    # FOREX (Reduced to 2 for cloud)
    print("\n📊 Processing Forex...")
    forex_list = [
        ('EURUSD', 'Euro/US Dollar'),
        ('GBPUSD', 'British Pound/US Dollar')
    ]
    
    for symbol, name in forex_list:
        result = process_asset(symbol, name, 'forex', 'Forex')
        if result:
            all_assets.append(result)
            print(f"✓ {symbol}: {result['aclRegime'].upper()} - {result['signal']}")
    
    print("\n" + "="*60)
    print(f"TOTAL ASSETS PROCESSED: {len(all_assets)}")
    print("="*60 + "\n")
    
    # Group by category
    grouped = {
        'crypto': [a for a in all_assets if a['category'] == 'crypto'],
        'stocks': [a for a in all_assets if a['category'] == 'stocks'],
        'midcap': [a for a in all_assets if a['category'] == 'midcap'],
        'forex': [a for a in all_assets if a['category'] == 'forex']
    }
    
    return grouped

@app.route('/')
def index():
    return send_from_directory('.', 'market_scanner_improved.html')

@app.route('/api/markets')
def get_markets():
    global CACHE
    
    # Check cache (3 minute expiry)
    if CACHE['data'] and CACHE['timestamp']:
        elapsed = (datetime.now() - CACHE['timestamp']).total_seconds()
        if elapsed < 180:  # 3 minutes
            print(f"⚡ Using cached data ({int(elapsed)}s old)")
            return jsonify({**CACHE['data'], 'timestamp': datetime.now().isoformat(), 'cached': True})
    
    # Fetch fresh data
    try:
        data = fetch_all_assets()
        
        CACHE['data'] = data
        CACHE['timestamp'] = datetime.now()
        
        return jsonify({
            **data,
            'timestamp': datetime.now().isoformat(),
            'cached': False
        })
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 WillP ProLine Scanner - FULL ACL CALCULATION")
    print("="*60)
    print("First load: ~45-60 seconds (calculating ACL for all assets)")
    print("Subsequent loads: Instant (cached for 3 minutes)")
    print("Running on http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
