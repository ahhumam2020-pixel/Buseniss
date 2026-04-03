import yfinance as yf
from arch import arch_model
import re, datetime, pytz, warnings, os
import pandas as pd
import numpy as np

# غیرفعال کردن هشدارهای مزاحم
warnings.filterwarnings("ignore")
melbourne_tz = pytz.timezone('Australia/Melbourne')

# پیدا کردن مسیر دقیق پوشه اسکریپت برای جلوگیری از خطای "فایل پیدا نشد"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")

assets = {
    'btc': 'BTC-USD', 'eth': 'ETH-USD', 'sol': 'SOL-USD',
    'gold': 'GC=F', 'silver': 'SI=F', 'sp500': '^GSPC',
    'nsdq100': '^IXIC', 'dj30': '^DJI', 'rty2000': '^RUT',
    'eurusd': 'EURUSD=X', 'usdjpy': 'JPY=X', 'audjpy': 'AUDJPY=X'
}

def start_analysis():
    now = datetime.datetime.now(melbourne_tz)
    print(f"🚀 شروع تحلیل هوشمند | ملبورن: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    if not os.path.exists(HTML_PATH):
        print(f"❌ خطا: فایل {HTML_PATH} پیدا نشد! مطمئن شوید کنار اسکریپت است."); return

    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # آپدیت زمان ملبورن
    html = re.sub(r'Melbourne:.*?(?=<)', f'Melbourne: {now.strftime("%d/%m/%Y, %H:%M:%S")}', html, count=1)

    for label, ticker in assets.items():
        try:
            # دریافت دیتا (2 ماه برای پایداری GARCH)
            data = yf.download(ticker, period="2mo", interval="1d", progress=False)
            if data.empty or len(data) < 20: continue

            last_price = float(data['Close'].values.flatten()[-1])
            returns = 100 * data['Close'].pct_change().dropna()
            
            # محاسبه GARCH
            model = arch_model(returns, vol='Garch', p=1, q=1)
            res = model.fit(disp='off')
            vol_val = float(np.sqrt(res.forecast(horizon=1).variance.values[-1, 0]))

            # اصلاح قیمت با در نظر گرفتن فواصل احتمالی در HTML
            # این ریجکس (Regex) بسیار دقیق‌تر عمل می‌کند
            price_pattern = rf'id\s*=\s*["\']price-{label}["\']\s*>[\d\.,-]+'
            new_price_str = f'id="price-{label}">{last_price:,.2f}'
            html = re.sub(price_pattern, new_price_str, html, count=1)
            
            # اصلاح GARCH
            garch_pattern = rf'id\s*=\s*["\']garch-{label}["\']\s*>[\d\.,%]+'
            new_garch_str = f'id="garch-{label}">{vol_val:.2f}%'
            html = re.sub(garch_pattern, new_garch_str, html, count=1)

            print(f"✅ {label.upper()} بروزرسانی شد: {last_price:,.2f}")

        except Exception as e:
            print(f"⚠️ خطا در {label}: {e}")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    
    print("\n✨ تحلیل با موفقیت تمام شد. حالا فایل index.html را در گیت‌هاب آپلود کنید.")

if __name__ == "__main__":
    start_analysis()
