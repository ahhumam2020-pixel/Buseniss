import yfinance as yf
import datetime, pytz
import pandas as pd
import os

# تنظیمات منطقه زمانی ملبورن
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"

# لیست دارایی‌ها با نماد اصلاح شده و تست شده برای چین
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
    'CHINA50': {'ticker': 'XIN9.F', 'tv_symbol': 'FX_IDC:CHINAA50'}, # نماد طلایی: مطابقت کامل با قیمت 15,000 ایتورو
    'HKG50': {'ticker': '^HSI', 'tv_symbol': 'OANDA:HK33HKD'}, # شاخص Hang Seng هنگ‌کنگ — مطابقت با قیمت ~25,932 ایتورو
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'OANDA:JP225USD'},
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'OANDA:DE30EUR'},
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'OANDA:UK100GBP'}
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    cards_html = ""
    
    for name, info in assets.items():
        try:
            # دانلود با تنظیمات بهینه برای جلوگیری از خطای NoneType
            data = yf.download(info['ticker'], period="5d", interval="1h", progress=False, auto_adjust=True)
            
            # بررسی دقیق سلامت دیتا قبل از هرگونه پردازش
            if data is None or data.empty or len(data) < 2:
                print(f"⚠️ دیتای لایو برای {name} (Ticker: {info['ticker']}) در دسترس نیست.")
                continue
            
            # استخراج قیمت‌ها با مدیریت ساختار چندستونی یاهو
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    close_prices = data['Close'][info['ticker']].values.flatten()
                    high_prices = data['High'][info['ticker']].values.flatten()
                    low_prices = data['Low'][info['ticker']].values.flatten()
                else:
                    close_prices = data['Close'].values.flatten()
                    high_prices = data['High'].values.flatten()
                    low_prices = data['Low'].values.flatten()
            except KeyError:
                print(f"❌ ستون Close برای {name} یافت نشد.")
                continue

            price = float(close_prices[-1])
            prev_price = float(close_prices[-2])
            change = ((price - prev_price) / prev_price) * 100
            
            atr = (high_prices - low_prices).mean()
            volatility = ((high_prices.max() - low_prices.min()) / price) * 100
            
            trend_direction = "Long" if change >= 0 else "Short"
            
            if trend_direction == "Long":
                stop_loss = price - (atr * 1.5)
                take_profit = price + (atr * 3.0)
            else:
                stop_loss = price + (atr * 1.5)
                take_profit = price - (atr * 3.0)

            # تعیین وضعیت ورود
            if volatility < 8:
                entry_status = f"Immediate {trend_direction} Entry"
                status_class = "status-immediate" if trend_direction == "Long" else "status-short-immediate"
            elif 8 <= volatility < 15:
                entry_status = f"Conditional {trend_direction} Entry"
                status_class = "status-conditional"
            else:
                entry_status = "No Immediate Setup"
                status_class = "status-none"
            
            card_color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header">
                    <span class="asset-name">{name}</span>
                    <span class="asset-change" style="color:{card_color}">{change:+.2f}%</span>
                </div>
                <div class="asset-price" style="color:{card_color}">{price:,.2f}</div>
                <div class="entry-box {status_class}">{entry_status}</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>نوسان:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>قیمت:</span><span class="val">{price:,.2f}</span></div>
                    <div class="stat-item"><span>TP:</span><span class="val" style="color:#10b981">{take_profit:,.2f}</span></div>
                    <div class="stat-item"><span>SL:</span><span class="val" style="color:#ef4444">{stop_loss:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"❌ خطای سیستمی در {name}: {e}")
            continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a0f1e; color:white; font-family:Tahoma, Arial; margin:0; padding:15px; }}
            .header {{ text-align:center; margin-bottom:15px; border-bottom:1px solid #1e293b; padding-bottom:10px; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(185px, 1fr)); gap:12px; margin-bottom:15px; }}
            .asset-card {{ background:#161d31; padding:12px; border-radius:10px; cursor:pointer; border:1px solid #283046; transition:0.2s; }}
            .asset-card:hover {{ border-color:#3b82f6; background:#1e2746; }}
            .asset-header {{ display:flex; justify-content:space-between; font-size:11px; font-weight:bold; margin-bottom:4px; }}
            .asset-name {{ color:#b4b7bd; }}
            .asset-price {{ font-size:18px; font-weight:bold; margin-bottom:8px; text-align:left; }}
            .entry-box {{ font-size:9px; padding:4px; border-radius:4px; text-align:center; margin-bottom:8px; font-weight:bold; text-transform: uppercase; }}
            .status-immediate {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }}
            .status-short-immediate {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }}
            .status-conditional {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }}
            .status-none {{ background: rgba(107, 114, 128, 0.2); color: #9ca3af; border: 1px solid #4b5563; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:6px; border-top:1px solid #283046; padding-top:8px; }}
            .stat-item {{ display:flex; flex-direction:column; font-size:9px; }}
            .stat-item span {{ color:#676d7d; }}
            .stat-item .val {{ color:#d0d2d6; font-weight:bold; }}
            .chart-box {{ height:600px; background:#161d31; border-radius:12px; border:1px solid #283046; overflow:hidden; }}
        </style>
    </head><meta http-equiv="refresh" content="1800">
    <body>
        <div class="header">
            <h3 style="margin:0; color:#3b82f6;">Asia Intelligence Pro Dashboard V3.4</h3>
            <div style="font-size:11px; color:#676d7d; margin-top:5px;">بروزرسانی نهایی: {now_time}</div>
        </div>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_chart_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(symbol) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "60", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#f1f3f6",
                    "enable_publishing": false, "hide_top_toolbar": false, "container_id": "tv_chart_container"
                }});
            }}
            changeChart('FX_IDC:CHINAA50');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ عملیات با موفقیت انجام شد. CHINA50 (XIN9.F) با قیمت صحیح جایگزین شد. ساعت: {now_time}")

if __name__ == "__main__": generate_dashboard()
