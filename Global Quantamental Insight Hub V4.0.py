import yfinance as yf
import datetime, pytz
import pandas as pd

# --- تنظیمات سیستمی (بدون تغییر) ---
PY_INTERVAL = "1d" 
TV_INTERVAL = "D"

melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"
APP_TITLE = "Asia Intelligence Pro Dashboard V4.8 (Expanded)"

# لیست دارایی‌ها (۱۵ اصلی + ۱۱ مورد جدید با دقت بالا)
assets = {
    # --- بخش اول: دارایی‌های اصلی قبلی ---
    'CHINA50': {'ticker': 'XIN9.FGI', 'tv_symbol': 'CAPITALCOM:CN50'},
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'TVC:SILVER'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'NSDQ100': {'ticker': 'NQ=F', 'tv_symbol': 'CAPITALCOM:US100'},
    'SP500': {'ticker': 'ES=F', 'tv_symbol': 'CAPITALCOM:US500'},
    'DOWJONES': {'ticker': 'YM=F', 'tv_symbol': 'CAPITALCOM:US30'},
    'RTY2000': {'ticker': 'RTY=F', 'tv_symbol': 'OANDA:US2000USD'},
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'},
    'HKG50': {'ticker': '^HSI', 'tv_symbol': 'OANDA:HK33HKD'},
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'OANDA:JP225USD'},
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'OANDA:DE30EUR'},
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'OANDA:UK100GBP'},
    
    # --- بخش دوم: دارایی‌های جدید درخواستی (منطبق با eToro/TradingView) ---
    'TESLA': {'ticker': 'TSLA', 'tv_symbol': 'NASDAQ:TSLA'},
    'APPLE': {'ticker': 'AAPL', 'tv_symbol': 'NASDAQ:AAPL'},
    'NVIDIA': {'ticker': 'NVDA', 'tv_symbol': 'NASDAQ:NVDA'},
    'AMAZON': {'ticker': 'AMZN', 'tv_symbol': 'NASDAQ:AMZN'},
    'META': {'ticker': 'META', 'tv_symbol': 'NASDAQ:META'},
    'BROADCOM': {'ticker': 'AVGO', 'tv_symbol': 'NASDAQ:AVGO'},
    'ALPHABET': {'ticker': 'GOOG', 'tv_symbol': 'NASDAQ:GOOG'},
    'MICROSOFT': {'ticker': 'MSFT', 'tv_symbol': 'NASDAQ:MSFT'},
    'ALIBABA': {'ticker': 'BABA', 'tv_symbol': 'NYSE:BABA'},
    'VISA': {'ticker': 'V', 'tv_symbol': 'NYSE:V'},
    'COPPER': {'ticker': 'HG=F', 'tv_symbol': 'COMEX:HG1!'}
}

def generate_dashboard():
    print(f"🚀 Updating {APP_TITLE} with New Assets...")
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    
    cards_html = ""
    
    for name, info in assets.items():
        try:
            # دانلود دیتا (حفظ دقیق منطق قبلی)
            data = yf.download(info['ticker'], period="60d", interval=PY_INTERVAL, progress=False, auto_adjust=True)
            if data.empty or len(data) < 20: continue

            curr_p = data['Close'].iloc[-1].item()
            prev_p = data['Close'].iloc[-2].item()
            change = ((curr_p - prev_p) / prev_p) * 100
            
            atr = (data['High'] - data['Low']).tail(14).mean().item()
            volatility = ((data['High'].max().item() - data['Low'].min().item()) / curr_p) * 100
            
            trend = "LONG" if change >= 0 else "SHORT"
            sl = curr_p - (atr * 1.5) if trend == "LONG" else curr_p + (atr * 1.5)
            tp = curr_p + (atr * 3.0) if trend == "LONG" else curr_p - (atr * 3.0)
            
            status = f"IMMEDIATE {trend}" if volatility < 12 else f"CONDITIONAL {trend}"
            status_class = "status-immediate" if "IMMEDIATE" in status and trend == "LONG" else \
                           "status-short" if "IMMEDIATE" in status else "status-wait"

            color = "#10b981" if change >= 0 else "#ef4444"

            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header"><span>{name}</span><span style="color:{color}">{change:+.2f}%</span></div>
                <div class="asset-price" style="color:{color}">{curr_p:,.2f}</div>
                <div class="entry-box {status_class}">{status}</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>SL (ATR):</span><span class="val sl-val">{sl:,.2f}</span></div>
                    <div class="stat-item"><span>TP (3x):</span><span class="val tp-val">{tp:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"❌ Error in {name}: {e}")

    # قالب‌بندی HTML (بدون تغییر در استایل‌ها)
    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a1224; color:white; font-family: 'Segoe UI', Tahoma, Arial; margin:0; padding:15px; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:12px; margin-bottom:20px; }}
            .asset-card {{ background:#1c2541; padding:15px; border-radius:12px; border:1px solid #2d3748; cursor:pointer; transition: transform 0.2s, border-color 0.2s; }}
            .asset-card:hover {{ transform: translateY(-3px); border-color:#4a90e2; background:#242f50; }}
            .asset-header {{ display:flex; justify-content:space-between; font-size:12px; font-weight:600; color:#a0aec0; margin-bottom:10px; }}
            .asset-price {{ font-size:18px; font-weight:bold; margin-bottom:12px; font-family: 'Consolas', monospace; }}
            .entry-box {{ font-size:10px; padding:6px; border-radius:6px; text-align:center; margin-bottom:12px; font-weight:bold; letter-spacing:0.5px; }}
            .status-immediate {{ background:rgba(16,185,129,0.15); color:#10b981; border:1px solid #10b981; }}
            .status-short {{ background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid #ef4444; }}
            .status-wait {{ background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid #f59e0b; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; border-top:1px solid #2d3748; padding-top:10px; }}
            .stat-item {{ display:flex; flex-direction:column; gap:2px; }}
            .stat-item span {{ font-size:10px; color:#718096; }}
            .stat-item .val {{ font-size:12px; font-weight:bold; font-family: 'Consolas', monospace; }}
            .sl-val {{ color:#fc8181; }}
            .tp-val {{ color:#68d391; }}
            .chart-box {{ height:600px; background:#1c2541; border-radius:15px; border:1px solid #2d3748; overflow:hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
        </style>
    </head>
    <body>
        <h3 style="text-align:center; color:#4a90e2; margin-bottom:5px; letter-spacing:1px;">{APP_TITLE}</h3>
        <div style="text-align:center; font-size:11px; color:#718096; margin-bottom:20px;">Melbourne: {now_time} | Sync Interval: {PY_INTERVAL}</div>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_chart_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(s) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": s, "interval": "{TV_INTERVAL}", 
                    "timezone": "Australia/Melbourne", "theme": "dark", "style": "1", 
                    "container_id": "tv_chart_container", "locale": "en", "hide_side_toolbar": false
                }});
            }}
            changeChart('NASDAQ:TSLA'); // پیش‌فرض روی تسلا لود شود
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ Dashboard updated with {len(assets)} assets.")

if __name__ == "__main__": generate_dashboard()
