import yfinance as yf
import datetime, pytz
import pandas as pd
import numpy as np

# --- تنظیمات هوشمند ---
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"
APP_TITLE = "Global Quantamental Insight Hub V4.2"

# لیست دارایی‌ها با نمادهای تست شده و پایدار TradingView
assets = {
    'CHINA50': {'ticker': 'XIN9.FGI', 'tv_symbol': 'CAPITALCOM:CN50'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'NSDQ100': {'ticker': 'NQ=F', 'tv_symbol': 'CAPITALCOM:US100'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'},
    'SP500': {'ticker': 'ES=F', 'tv_symbol': 'CAPITALCOM:US500'}
}

def get_fundamental_bias(ticker, dxy_change):
    """محاسبه سوگیری بنیادی بر اساس همبستگی معکوس با دلار"""
    is_inverse = any(x in ticker for x in ['GC=F', 'NQ=F', 'ES=F', 'XIN9'])
    if is_inverse:
        return "BULLISH" if dxy_change < 0 else "BEARISH"
    return "BULLISH" if dxy_change > 0 else "BEARISH"

def generate_dashboard():
    print(f"🚀 Initializing {APP_TITLE}...")
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    
    # ۱. تحلیل شاخص دلار برای فیلتر بنیادی
    try:
        dxy = yf.download("DX-Y.NYB", period="5d", interval="1d", progress=False)
        # رفع خطای Series با تبدیل به مقدار عددی قطعی
        dxy_last = float(dxy['Close'].iloc[-1])
        dxy_prev = float(dxy['Close'].iloc[-2])
        dxy_change = ((dxy_last - dxy_prev) / dxy_prev) * 100
        print(f"✅ Fundamental Factor (DXY): {dxy_change:+.2f}%")
    except Exception as e:
        print(f"⚠️ Warning: DXY analysis skipped due to data lag. Error: {e}")
        dxy_change = 0.0

    cards_html = ""
    
    # ۲. پردازش دارایی‌ها و تولید کارت‌ها
    for name, info in assets.items():
        try:
            print(f"📊 Analyzing {name} (Daily)...")
            data = yf.download(info['ticker'], period="60d", interval="1d", progress=False, auto_adjust=True)
            
            if data.empty or len(data) < 20: continue

            # استخراج قیمت‌ها و رفع خطاهای Ambiguity
            prices = data['Close'].values.flatten().astype(float)
            curr_p = float(prices[-1])
            prev_p = float(prices[-2])
            change = ((curr_p - prev_p) / prev_p) * 100
            
            # محاسبات GARCH-Lite برای نوسان
            returns = np.diff(np.log(prices))
            volatility = float(np.std(returns) * np.sqrt(252) * 100)
            
            # روند تکنیکال (SMA 20)
            sma_20 = float(data['Close'].rolling(window=20).mean().iloc[-1])
            tech_trend = "BULLISH" if curr_p > sma_20 else "BEARISH"
            
            # ترکیب بنیاد و تکنیکال (Quantamental Logic)
            f_bias = get_fundamental_bias(info['ticker'], dxy_change)
            status = f"IMMEDIATE {tech_trend}" if f_bias == tech_trend else "CONTRARIAN SETUP"
            status_class = "status-immediate" if (f_bias == tech_trend and tech_trend == "BULLISH") else \
                           "status-short" if (f_bias == tech_trend and tech_trend == "BEARISH") else "status-wait"

            color = "#10b981" if change >= 0 else "#ef4444"

            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header"><span>{name}</span><span style="color:{color}">{change:+.2f}%</span></div>
                <div class="asset-price" style="color:{color}">{curr_p:,.2f}</div>
                <div class="entry-box {status_class}">{status}</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>نوسان:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>Target:</span><span class="val" style="color:#10b981">{curr_p*1.02:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")

    # ۳. تزریق به قالب HTML
    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a101e; color:white; font-family:Arial; padding:15px; margin:0; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:12px; margin-bottom:15px; }}
            .asset-card {{ background:#161d31; padding:12px; border-radius:10px; border:1px solid #283046; cursor:pointer; }}
            .entry-box {{ font-size:9px; padding:4px; border-radius:4px; text-align:center; margin:8px 0; font-weight:bold; }}
            .status-immediate {{ background:#10b98133; color:#10b981; border:1px solid #10b981; }}
            .status-short {{ background:#ef444433; color:#ef4444; border:1px solid #ef4444; }}
            .status-wait {{ background:#f59e0b33; color:#f59e0b; border:1px solid #f59e0b; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:5px; border-top:1px solid #283046; padding-top:8px; font-size:9px; }}
            .chart-box {{ height:600px; background:#161d31; border-radius:12px; border:1px solid #283046; overflow:hidden; }}
        </style>
    </head>
    <body>
        <h3 style="text-align:center; color:#3b82f6;">{APP_TITLE}</h3>
        <div style="text-align:center; font-size:10px; color:#676d7d; margin-bottom:15px;">Melbourne Sync: {now_time}</div>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_chart_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(s) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": s, "interval": "D", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "container_id": "tv_chart_container", "locale": "en"
                }});
            }}
            changeChart('CAPITALCOM:CN50');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ Dashboard updated successfully at {now_time}.")

if __name__ == "__main__":
    generate_dashboard()
