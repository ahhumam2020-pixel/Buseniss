import yfinance as yf
import numpy as np
import pandas as pd
from arch import arch_model
from datetime import datetime
import json, os, sys, webbrowser, subprocess

# 1. تنظیمات اولیه
ALPHA_VANTAGE_KEY = "YOUR_API_KEY_HERE"
FOLDER_PATH = r"C:\Users\ahhum\OneDrive\Documents\آسیا\بزنس"

MARKETS = {
    "AUD/JPY": {"yahoo": "AUDJPY=X", "alpha": "AUDJPY", "tv": "https://www.tradingview.com/chart/?symbol=AUDJPY", "flag": "au"},
    "USD/JPY": {"yahoo": "JPY=X", "alpha": "USDJPY", "tv": "https://www.tradingview.com/chart/?symbol=USDJPY", "flag": "jp"},
    "Bitcoin": {"yahoo": "BTC-USD", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT", "flag": "btc", "type": "crypto"},
    "Ethereum": {"yahoo": "ETH-USD", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=BINANCE:ETHUSDT", "flag": "eth", "type": "crypto"}
}

# 2. توابع پردازشی
def fetch_data(info):
    try:
        data = yf.download(info["yahoo"], period="6mo", interval="1d", progress=False, auto_adjust=True)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join([c for c in col if c]).strip('_') for col in data.columns]
        close_col = next((c for c in data.columns if 'close' in c.lower()), None)
        return data[close_col].dropna()
    except: return None

def fit_garch(series):
    try:
        returns = 100 * series.pct_change().dropna()
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='normal', rescale=False)
        res = model.fit(disp='off', show_warning=False)
        return {
            "persistence": round(float(res.params.get('alpha[1]', 0) + res.params.get('beta[1]', 0)), 4),
            "cond_vol": round(float(res.conditional_volatility.iloc[-1]), 4),
            "returns": returns.tail(60).tolist(),
            "cvol_series": res.conditional_volatility.tail(60).tolist()
        }
    except: return None

def analyze_all():
    results = {}
    print("📊 در حال تحلیل بازارها...")
    for name, info in MARKETS.items():
        series = fetch_data(info)
        if series is None: continue
        g = fit_garch(series)
        cur = float(series.iloc[-1])
        prev = float(series.iloc[-2])
        results[name] = {
            "price": round(cur, 4), "change_pct": round(((cur-prev)/prev)*100, 2),
            "flag": info["flag"], "tv_url": info["tv"], "garch": g
        }
        print(f"✅ {name} تحلیل شد.")
    return results

def build_html(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    audjpy_g = results.get("AUD/JPY", {}).get("garch", {})
    rets = audjpy_g.get("returns", [])
    cvols = audjpy_g.get("cvol_series", [])
    
    rows = ""
    for name, r in results.items():
        vol = r['garch']['cond_vol'] if r['garch'] else "N/A"
        rows += f"<tr><td>{r['flag']} {name}</td><td>{r['price']}</td><td>{r['change_pct']}%</td><td>{vol}%</td><td><a href='{r['tv_url']}' target='_blank'>📈</a></td></tr>"

    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>body{{background:#0a0e1a;color:white;font-family:sans-serif;padding:20px;}} .panel{{background:#0d1525;padding:20px;border-radius:10px;margin-bottom:20px;}} table{{width:100%;border-collapse:collapse;}} th,td{{padding:10px;border-bottom:1px solid #1e2d45;text-align:right;}}</style>
    </head><body>
    <div class="panel"><h2>داشبورد نوسانات GARCH</h2><p>به‌روزرسانی: {now}</p></div>
    <div class="panel"><canvas id="chart"></canvas></div>
    <div class="panel"><table><thead><tr><th>بازار</th><th>قیمت</th><th>تغییر</th><th>نوسان</th><th>چارت</th></tr></thead><tbody>{rows}</tbody></table></div>
    <script>new Chart(document.getElementById('chart'),{{type:'line',data:{{labels:{json.dumps([f"T-{i}" for i in range(len(rets))][::-1])},datasets:[{{label:'Returns',data:{json.dumps(rets)},borderColor:'#00ff88'}},{{label:'Vol',data:{json.dumps(cvols)},borderColor:'#4da6ff'}}]}}}});</script>
    </body></html>"""

# 3. بخش اصلی اجرا (در انتهای کد)
if __name__ == "__main__":
    data = analyze_all()
    if data:
        html_content = build_html(data)
        if not os.path.exists(FOLDER_PATH): os.makedirs(FOLDER_PATH)
        file_path = os.path.join(FOLDER_PATH, "index.html")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ فایل ذخیره شد: {file_path}")
        
        # عملیات گیت
        try:
            subprocess.run("git add index.html", cwd=FOLDER_PATH, shell=True)
            subprocess.run(f'git commit -m "Auto-update {datetime.now()}"', cwd=FOLDER_PATH, shell=True)
            subprocess.run("git push origin main", cwd=FOLDER_PATH, shell=True)
            print("🚀 گیت‌هاب آپدیت شد.")
        except: print("⚠️ خطای گیت (دستی انجام دهید)")
        
        webbrowser.open(f"file:///{file_path}")
