import yfinance as yf
from arch import arch_model
import re, datetime, pytz, warnings
import pandas as pd
import numpy as np

# غیرفعال کردن هشدارهای مزاحم
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

            # ۲. استخراج قیمت (تبدیل قطعی به عدد تکی برای رفع خطای Ambiguous)
            last_price = float(data['Close'].values.flatten()[-1])
            returns = 100 * data['Close'].pct_change().dropna()
            last_return = float(returns.values.flatten()[-1])

            # ۳. محاسبه نوسان GARCH
            try:
                model = arch_model(returns, vol='Garch', p=1, q=1)
                res = model.fit(disp='off')
                forecast = res.forecast(horizon=1)
                vol_val = float(np.sqrt(forecast.variance.values[-1, 0]))
            except:
                vol_val = float(returns.std())

            # ۴. محاسبه نقاط ورود و خروج
            entry = last_price
            stop_loss = entry * (1 - (vol_val * 0.01 * 1.5))
            target = entry * (1 + (vol_val * 0.01 * 2))
            
            # تعیین روند
            trend = "BUY ZONE" if last_return > 0 else "SELL ZONE"
            trend_color = "#10b981" if trend == "BUY ZONE" else "#ef4444"

            # ۵. تزریق به HTML
            html = re.sub(rf'id="price-{label}">.*?</div>', f'id="price-{label}">{last_price:,.2f}</div>', html)
            html = re.sub(rf'id="garch-{label}">.*?</div>', f'id="garch-{label}">{vol_val:.2f}%</div>', html)
            html = re.sub(rf'id="entry-{label}">.*?</div>', f'id="entry-{label}">{entry:,.2f}</div>', html)
            html = re.sub(rf'id="sl-{label}">.*?</div>', f'id="sl-{label}">{stop_loss:,.2f}</div>', html)
            html = re.sub(rf'id="tp-{label}">.*?</div>', f'id="tp-{label}">{target:,.2f}</div>', html)
            html = re.sub(rf'id="trend-{label}">.*?</span>', f'id="trend-{label}" style="color:{trend_color}">{trend}</span>', html)
            
            print(f"✅ {label.upper()} بروزرسانی شد.")

        except Exception as e:
            print(f"⚠️ مشکل در {label}: {e}")

    # آپدیت زمان
    update_time = now.strftime('%Y/%m/%d %H:%M:%S')
    html = re.sub(rf'Melbourne:.*?</div>', f'Melbourne: {update_time}</div>', html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n✨ تحلیل با موفقیت تمام شد. حالا فایل index.html را در گیت‌هاب آپلود کنید.")

if __name__ == "__main__":
    start_analysis()
