import yfinance as yf
import datetime, pytz
import pandas as pd

# تنظیمات منطقه زمانی
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"

# لیست دارایی‌ها با نماد تست شده و زنده (آپدیت 11 آوریل)
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'TVC:SILVER'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'NSDQ100': {'ticker': 'NQ=F', 'tv_symbol': 'CME_MINI:NQ1!'},
    'SP500': {'ticker': 'ES=F', 'tv_symbol': 'CAPITALCOM:US500'},
    'DOWJONES': {'ticker': 'YM=F', 'tv_symbol': 'CAPITALCOM:US30'},
    'RTY2000': {'ticker': 'RTY=F', 'tv_symbol': 'OANDA:US2000USD'},
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'},
    'CHINA50': {'ticker': 'CN=F', 'tv_symbol': 'FX_IDC:CHINAA50'}, # نماد اصلاح شده برای قیمت ~15,000
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'OANDA:JP225USD'},
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'OANDA:DE30EUR'},
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'OANDA:UK100GBP'}
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    cards_html = ""
    
    for name, info in assets.items():
        try:
            # دریافت دیتا با مدیریت خطای پیشرفته
            ticker_obj = yf.Ticker(info['ticker'])
            data = ticker_obj.history(period="5d", interval="1h")
            
            if data.empty or len(data) < 2:
                print(f"⚠️ {name} ({info['ticker']}): دیتا در دسترس نیست. عبور از این مورد...")
                continue
            
            # استخراج قیمت با اطمینان از صحت ساختار دیتا
            price = float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2])
            change = ((price - prev_price) / prev_price) * 100
            
            high = data['High'].max()
            low = data['Low'].min()
            volatility = ((high - low) / price) * 100
            atr = (data['High'] - data['Low']).mean()
            
            trend = "Long" if change >= 0 else "Short"
            tp = price + (atr * 3) if trend == "Long" else price - (atr * 3)
            sl = price - (atr * 1.5) if trend == "Long" else price + (atr * 1.5)

            status_class = "status-immediate" if abs(change) > 0.5 else "status-conditional"
            card_color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header">
                    <span class="asset-name">{name}</span>
                    <span class="asset-change" style="color:{card_color}">{change:+.2f}%</span>
                </div>
                <div class="asset-price" style="color:{card_color}">{price:,.2f}</div>
                <div class="entry-box {status_class}">{trend} Entry</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>نوسان:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>TP:</span><span class="val" style="color:#10b981">{tp:,.2f}</span></div>
                    <div class="stat-item"><span>SL:</span><span class="val" style="color:#ef4444">{sl:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"❌ خطا در {name}: {e}")
            continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a0f1e; color:white; font-family:Tahoma; margin:0; padding:20px; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:15px; }}
            .asset-card {{ background:#161d31; padding:15px; border-radius:12px; border:1px solid #283046; cursor:pointer; }}
            .asset-price {{ font-size:22px; font-weight:bold; margin:10px 0; }}
            .entry-box {{ padding:5px; border-radius:5px; text-align:center; font-size:12px; font-weight:bold; }}
            .status-immediate {{ background:rgba(16,185,129,0.2); color:#10b981; border:1px solid #10b981; }}
            .status-conditional {{ background:rgba(245,158,11,0.2); color:#f59e0b; border:1px solid #f59e0b; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-top:10px; border-top:1px solid #283046; padding-top:10px; }}
            .stat-item {{ font-size:10px; display:flex; flex-direction:column; }}
            .chart-box {{ height:550px; margin-top:20px; border-radius:12px; overflow:hidden; border:1px solid #283046; }}
        </style>
    </head>
    <body>
        <h2 style="text-align:center; color:#3b82f6;">Asia Intelligence Pro - V3.5</h2>
        <p style="text-align:center; font-size:12px; color:#676d7d;">آخرین بروزرسانی: {now_time}</p>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(s) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": s, "interval": "60", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "locale": "en", "container_id": "tv_container"
                }});
            }}
            changeChart('FX_IDC:CHINAA50');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ عملیات موفق. CHINA50 با نماد CN=F (قیمت ~15k) آپدیت شد. زمان: {now_time}")

if __name__ == "__main__": generate_dashboard()
