
import yfinance as yf
import datetime, pytz
import pandas as pd
import numpy as np

# تنظیمات منطقه زمانی ملبورن
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"
APP_TITLE = "Asia Intelligence Pro Dashboard V4.6"

# لیست کامل دارایی‌ها (بر اساس نسخه V3.4)
assets = {
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
    'CHINA50': {'ticker': 'XIN9.FGI', 'tv_symbol': 'CAPITALCOM:CN50'},
    'HKG50': {'ticker': '^HSI', 'tv_symbol': 'OANDA:HK33HKD'},
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'OANDA:JP225USD'},
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'OANDA:DE30EUR'},
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'OANDA:UK100GBP'}
}

def generate_dashboard():
    print(f"🚀 Initializing {APP_TITLE} (Restoring Assets & SL/TP)...")
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    
    # تحلیل شاخص دلار برای فیلتر بنیادی
    try:
        dxy = yf.download("DX-Y.NYB", period="2d", interval="1d", progress=False)
        dxy_change = ((dxy['Close'].iloc[-1].item() - dxy['Close'].iloc[-2].item()) / dxy['Close'].iloc[-2].item()) * 100
    except: dxy_change = 0.0

    cards_html = ""
    
    for name, info in assets.items():
        try:
            print(f"📊 Processing {name}...")
            data = yf.download(info['ticker'], period="60d", interval="1d", progress=False, auto_adjust=True)
            if data.empty or len(data) < 20: continue

            # استخراج قیمت‌ها با متد .item() برای جلوگیری از هشدارهای IDLE
            curr_p = data['Close'].iloc[-1].item()
            prev_p = data['Close'].iloc[-2].item()
            high_p = data['High'].iloc[-1].item()
            low_p = data['Low'].iloc[-1].item()
            change = ((curr_p - prev_p) / prev_p) * 100
            
            # محاسبات ATR و SL/TP (بر اساس منطق نسخه V3.4)
            atr = (data['High'] - data['Low']).tail(14).mean().item()
            volatility = ((data['High'].max().item() - data['Low'].min().item()) / curr_p) * 100
            
            # تعیین سوگیری و نقاط خروج
            trend = "LONG" if change >= 0 else "SHORT"
            sl = curr_p - (atr * 1.5) if trend == "LONG" else curr_p + (atr * 1.5)
            tp = curr_p + (atr * 3.0) if trend == "LONG" else curr_p - (atr * 3.0)
            
            # تعیین وضعیت ورود (مشابه داشبورد اول)
            status = f"IMMEDIATE {trend} ENTRY" if volatility < 12 else f"CONDITIONAL {trend} ENTRY"
            status_class = "status-immediate" if "IMMEDIATE" in status and trend == "LONG" else \
                           "status-short" if "IMMEDIATE" in status else "status-wait"

            color = "#10b981" if change >= 0 else "#ef4444"

            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header"><span>{name}</span><span style="color:{color}">{change:+.2f}%</span></div>
                <div class="asset-price" style="color:{color}">{curr_p:,.2f}</div>
                <div class="entry-box {status_class}">{status}</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>قیمت:</span><span class="val">{curr_p:,.2f}</span></div>
                    <div class="stat-item"><span>نوسان:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>SL:</span><span class="val" style="color:#ef4444">{sl:,.2f}</span></div>
                    <div class="stat-item"><span>TP:</span><span class="val" style="color:#10b981">{tp:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"❌ Error in {name}: {e}")

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a0f1e; color:white; font-family:Tahoma, Arial; margin:0; padding:15px; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:10px; margin-bottom:15px; }}
            .asset-card {{ background:#161d31; padding:12px; border-radius:10px; border:1px solid #283046; cursor:pointer; }}
            .asset-price {{ font-size:16px; font-weight:bold; margin-bottom:8px; }}
            .entry-box {{ font-size:9px; padding:4px; border-radius:4px; text-align:center; margin-bottom:8px; font-weight:bold; }}
            .status-immediate {{ background:rgba(16,185,129,0.15); color:#10b981; border:1px solid #10b981; }}
            .status-short {{ background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid #ef4444; }}
            .status-wait {{ background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid #f59e0b; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:6px; border-top:1px solid #283046; padding-top:8px; }}
            .stat-item span {{ font-size:9px; color:#676d7d; }}
            .stat-item .val {{ font-size:10px; font-weight:bold; }}
            .chart-box {{ height:600px; background:#161d31; border-radius:12px; border:1px solid #283046; overflow:hidden; }}
        </style>
    </head>
    <body>
        <h3 style="text-align:center; color:#3b82f6; margin-bottom:5px;">{APP_TITLE}</h3>
        <div style="text-align:center; font-size:10px; color:#676d7d; margin-bottom:15px;">Melbourne: {now_time}</div>
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
    print(f"✅ Dashboard Restored & Updated at {now_time}.")

if __name__ == "__main__": generate_dashboard()
