import yfinance as yf
from arch import arch_model
import re, datetime, pytz, warnings
import pandas as pd
import numpy as np

# تنظیمات اولیه
warnings.filterwarnings("ignore")
melbourne_tz = pytz.timezone('Australia/Melbourne')

assets = {
    'btc': 'BTC-USD', 'eth': 'ETH-USD', 'sol': 'SOL-USD',
    'gold': 'GC=F', 'silver': 'SI=F', 'sp500': '^GSPC',
    'nsdq100': '^IXIC', 'dj30': '^DJI', 'rty2000': '^RUT',
    'eurusd': 'EURUSD=X', 'usdjpy': 'JPY=X', 'audjpy': 'AUDJPY=X'
}

def start_analysis():
    now = datetime.datetime.now(melbourne_tz)
    print(f"🚀 شروع تحلیل هوشمند | ملبورن: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print("❌ خطا: فایل index.html پیدا نشد!"); return

    for label, ticker in assets.items():
        try:
            # ۱. دریافت دیتا
            data = yf.download(ticker, period="2mo", interval="1d", progress=False)
            if data.empty or len(data) < 20: continue

            # ۲. استخراج قیمت فعلی (رفع خطای scalar در تصویر شما)
            last_price = float(data['Close'].iloc[-1])
            returns = 100 * data['Close'].pct_change().dropna()

            # ۳. محاسبه نوسان با مدل GARCH
            try:
                model = arch_model(returns, vol='Garch', p=1, q=1)
                res = model.fit(disp='off')
                forecast = res.forecast(horizon=1)
                vol_val = np.sqrt(forecast.variance.iloc[-1].values[0])
            except:
                vol_val = returns.std()

            # ۴. محاسبه نقاط ورود و خروج (استراتژی نوسان‌محور)
            # حد ضرر و هدف بر اساس ۲ برابر نوسان GARCH تنظیم شده است
            entry = last_price
            stop_loss = entry * (1 - (vol_val * 0.01 * 1.5)) # 1.5x Volatility
            target = entry * (1 + (vol_val * 0.01 * 2))    # 2x Volatility
            
            # تعیین روند
            trend = "BUY ZONE" if returns.iloc[-1] > 0 else "SELL ZONE"
            trend_color = "#10b981" if trend == "BUY ZONE" else "#ef4444"

            # ۵. تزریق دقیق اعداد به HTML
            html = re.sub(rf'id="price-{label}">.*?</div>', f'id="price-{label}">{last_price:,.2f}</div>', html)
            html = re.sub(rf'id="garch-{label}">.*?</div>', f'id="garch-{label}">{vol_val:.2f}%</div>', html)
            html = re.sub(rf'id="entry-{label}">.*?</div>', f'id="entry-{label}">{entry:,.2f}</div>', html)
            html = re.sub(rf'id="sl-{label}">.*?</div>', f'id="sl-{label}">{stop_loss:,.2f}</div>', html)
            html = re.sub(rf'id="tp-{label}">.*?</div>', f'id="tp-{label}">{target:,.2f}</div>', html)
            html = re.sub(rf'id="trend-{label}">.*?</span>', f'id="trend-{label}" style="color:{trend_color}">{trend}</span>', html)
            
            print(f"✅ {label.upper()} بروزرسانی شد.")

        except Exception as e:
            print(f"⚠️ مشکل در {label}: {e}")

    # ثبت زمان آپدیت
    update_time = now.strftime('%Y/%m/%d %H:%M:%S')
    html = re.sub(rf'Melbourne:.*?</div>', f'Melbourne: {update_time}</div>', html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n✨ تحلیل تمام شد. صفحه مرورگر را رفرش کنید.")

if __name__ == "__main__":
    start_analysis()
