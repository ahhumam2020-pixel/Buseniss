import yfinance as yf
import numpy as np
import pandas as pd
from arch import arch_model
from datetime import datetime
import json, os, sys

# لیست بازارهای هدف
MARKETS = {
    "AUD/JPY": {"yahoo": "AUDJPY=X", "flag": "au", "tv": "https://www.tradingview.com/chart/?symbol=AUDJPY"},
    "USD/JPY": {"yahoo": "JPY=X", "flag": "jp", "tv": "https://www.tradingview.com/chart/?symbol=USDJPY"},
    "HSI": {"yahoo": "^HSI", "flag": "hk", "tv": "https://www.tradingview.com/chart/?symbol=HSI"}
}

def analyze_all():
    results = {}
    print("\n📊 در حال دریافت داده‌های زنده...")
    for name, info in MARKETS.items():
        try:
            data = yf.download(info["yahoo"], period="6mo", interval="1d", progress=False)
            if data.empty: continue
            
            # محاسبات GARCH
            returns = 100 * data['Close'].pct_change().dropna()
            model = arch_model(returns, vol='Garch', p=1, q=1, rescale=False)
            res = model.fit(disp='off')
            
            # استخراج پارامترها
            persistence = float(res.params['alpha[1]'] + res.params['beta[1]'])
            cond_vol = float(res.conditional_volatility.iloc[-1])
            
            results[name] = {
                "price": round(float(data['Close'].iloc[-1]), 4),
                "change": round(float((data['Close'].iloc[-1]/data['Close'].iloc[-2]-1)*100), 2),
                "vol": round(cond_vol, 2),
                "persist": round(persistence, 4),
                "flag": info["flag"]
            }
            print(f"✅ {name} تحلیل شد.")
        except:
            print(f"⚠️ خطا در تحلیل {name}")
    return results

def main():
    print("="*50)
    print("  GARCH LIVE DASHBOARD UPDATER  v3.1")
    print("="*50)
    
    # اجرای تابع تحلیل
    data_results = analyze_all()
    
    if not data_results:
        print("❌ هیچ داده‌ای دریافت نشد!")
        return

    # مسیر ذخیره فایل HTML (اصلاح شده برای IDLE)
    output_file = "garch_dashboard_live.html"
    
    # ساخت یک فایل متنی ساده به عنوان خروجی (موقت)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"<h1>Market Analysis - {datetime.now()}</h1>")
        for m, r in data_results.items():
            f.write(f"<p>{m}: Price={r['price']} | Volatility={r['vol']}%</p>")
            
    full_path = os.path.abspath(output_file)
    print(f"\n✅ تحلیل با موفقیت تمام شد.")
    print(f"📂 فایل در این آدرس ذخیره شد:\n{full_path}")

if __name__ == "__main__":
    main()
