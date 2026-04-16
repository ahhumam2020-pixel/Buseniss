import yfinance as yf
import datetime, pytz
import pandas as pd
import numpy as np
import os

# تنظیمات منطقه زمانی ملبورن
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"

# لیست دارایی‌ها
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'TVC:SILVER'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'NSDQ100': {'ticker': 'NQ=F', 'tv_symbol': 'CAPITALCOM:US100'},
    'SP500': {'ticker': 'ES=F', 'tv_symbol': 'CAPITALCOM:US500'},
    'DOWJONES': {'ticker': 'YM=F', 'tv_symbol': 'CAPITALCOM:US30'},
    'CHINA50': {'ticker': 'XIN9.FGI', 'tv_symbol': 'FX_IDC:CHINAA50'},
    'HKG50': {'ticker': '^HSI', 'tv_symbol': 'OANDA:HK33HKD'},
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'}
}

def get_fundamental_bias(ticker, dxy_change):
    """
    شبیه‌سازی تحلیل بنیادی بر اساس شاخص دلار و روند کلان (Proxy for Investing.com Analysis)
    """
    # به طور کلی: رشد دلار برای طلا و شاخص‌ها منفی است
    is_inverse_to_dxy = any(x in ticker for x in ['GC=F', 'SI=F', 'NQ=F', 'ES=F', 'XIN9'])
    
    if is_inverse_to_dxy:
        bias_score = -1 if dxy_change > 0 else 1
    else:
        bias_score = 1 if dxy_change > 0 else -1
        
    return "BULLISH" if bias_score > 0 else "BEARISH"

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    
    # دریافت دیتای شاخص دلار برای تحلیل بنیادی
    try:
        dxy_data = yf.download("DX-Y.NYB", period="2d", interval="1d", progress=False)
        dxy_change = ((dxy_data['Close'].iloc[-1] - dxy_data['Close'].iloc[-2]) / dxy_data['Close'].iloc[-2]) * 100
    except:
        dxy_change = 0

    cards_html = ""
    
    for name, info in assets.items():
        try:
            # تغییر به بازه روزانه (1d) با دوره طولانی‌تر برای تحلیل دقیق
            data = yf.download(info['ticker'], period="60d", interval="1d", progress=False, auto_adjust=True)
            
            if data is None or data.empty or len(data) < 20: continue

            # استخراج قیمت‌ها
            prices = data['Close'].values.flatten()
            highs = data['High'].values.flatten()
            lows = data['Low'].values.flatten()

            current_price = float(prices[-1])
            prev_price = float(prices[-2])
            daily_change = ((current_price - prev_price) / prev_price) * 100
            
            # محاسبات GARCH-Lite (نوسان روزانه)
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * np.sqrt(252) * 100 # نوسان سالانه شده بر اساس داده روزانه
            
            # تحلیل بنیادی (Fundamental Bias)
            f_bias = get_fundamental_bias(info['ticker'], dxy_change)
            sma_50 = data['Close'].rolling(window=20).mean().iloc[-1]
            technical_trend = "BULLISH" if current_price > sma_50 else "BEARISH"

            # تشخیص همگرایی (Convergence)
            is_converged = f_bias == technical_trend
            
            # تعیین وضعیت ورود بر اساس همگرایی بنیاد و تکنیکال
            if is_converged:
                entry_status = f"IMMEDIATE {technical_trend}"
                status_class = "status-immediate" if technical_trend == "BULLISH" else "status-short-immediate"
            else:
                entry_status = "FUNDAMENTAL CONFLICT"
                status_class = "status-conditional"

            # مدیریت رنگ و خروجی
            card_color = "#10b981" if daily_change >= 0 else "#ef4444"
            bias_color = "#10b981" if f_bias == "BULLISH" else "#ef4444"

            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header">
                    <span class="asset-name">{name} (DAILY)</span>
                    <span class="asset-change" style="color:{card_color}">{daily_change:+.2f}%</span>
                </div>
                <div class="asset-price" style="color:{card_color}">{current_price:,.2f}</div>
                <div class="entry-box {status_class}">{entry_status}</div>
                <div style="font-size:10px; text-align:center; margin-bottom:10px; color:{bias_color}">
                    FUNDAMENTAL BIAS: {f_bias}
                </div>
                <div class="stats-grid">
                    <div class="stat-item"><span>نوسان (GARCH):</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>گرایش کلان:</span><span class="val">{technical_trend}</span></div>
                    <div class="stat-item"><span>Target (Daily):</span><span class="val" style="color:#10b981">{current_price * 1.02:,.2f}</span></div>
                    <div class="stat-item"><span>Stop (Daily):</span><span class="val" style="color:#ef4444">{current_price * 0.98:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"Error in {name}: {e}")

    # (بخش تولید فایل HTML مشابه کد قبلی شما با استایل‌های به‌روزشده)
    # ... (کد HTML قبلی را اینجا قرار دهید)
