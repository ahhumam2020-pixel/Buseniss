#!/usr/bin/env python3
"""
GARCH Live Dashboard Updater v3.1 - Fixed Version
منابع: Yahoo Finance + Alpha Vantage (اختیاری) + TradingView
"""

import yfinance as yf
import numpy as np
import pandas as pd
from arch import arch_model
from datetime import datetime
import json, os, sys, webbrowser

# ─────────────────────────────────────────────
# Alpha Vantage API Key
# ─────────────────────────────────────────────
ALPHA_VANTAGE_KEY = "YOUR_API_KEY_HERE"  # <-- کلید خود را اینجا وارد کنید

MARKETS = {
    "AUD/JPY": {"yahoo": "AUDJPY=X", "alpha": "AUDJPY", "tv": "https://www.tradingview.com/chart/?symbol=AUDJPY", "session": "AUS", "flag": "au"},
    "USD/JPY": {"yahoo": "JPY=X", "alpha": "USDJPY", "tv": "https://www.tradingview.com/chart/?symbol=USDJPY", "session": "JAPAN", "flag": "jp"},
    "USD/CNH": {"yahoo": "USDCNH=X", "alpha": "USDCNH", "tv": "https://www.tradingview.com/chart/?symbol=USDCNH", "session": "CHINA", "flag": "cn"},
    "HSI": {"yahoo": "^HSI", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=HSI", "session": "HK", "flag": "hk"},
    "AUD/USD": {"yahoo": "AUDUSD=X", "alpha": "AUDUSD", "tv": "https://www.tradingview.com/chart/?symbol=AUDUSD", "session": "AUS", "flag": "au"},
    "EUR/USD": {"yahoo": "EURUSD=X", "alpha": "EURUSD", "tv": "https://www.tradingview.com/chart/?symbol=EURUSD", "session": "EU", "flag": "eu"},
    "Nikkei 225": {"yahoo": "^N225", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=NKY", "session": "JAPAN", "flag": "jp"},
    "ASX 200": {"yahoo": "^AXJO", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=ASX:XJO", "session": "AUS", "flag": "au"},
    "Bitcoin": {"yahoo": "BTC-USD", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT", "session": "CRYPTO", "flag": "btc", "type": "crypto"},
    "Ethereum": {"yahoo": "ETH-USD", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=BINANCE:ETHUSDT", "session": "CRYPTO", "flag": "eth", "type": "crypto"},
    "Solana": {"yahoo": "SOL-USD", "alpha": None, "tv": "https://www.tradingview.com/chart/?symbol=BINANCE:SOLUSDT", "session": "CRYPTO", "flag": "sol", "type": "crypto"}
}

# ─── توابع دریافت داده و تحلیل ───
def fetch_yahoo(ticker, period="6mo"):
    try:
        raw = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if raw is None or raw.empty: return None
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ['_'.join([c for c in col if c]).strip('_') for col in raw.columns]
        close_col = next((c for c in raw.columns if 'close' in c.lower()), None)
        s = raw[close_col].dropna()
        return s if len(s) >= 10 else None
    except: return None

def fetch_alpha(symbol):
    if ALPHA_VANTAGE_KEY == "YOUR_API_KEY_HERE" or symbol is None: return None
    try:
        import urllib.request
        url = (f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={symbol[:3]}&to_symbol={symbol[3:]}&outputsize=compact&apikey={ALPHA_VANTAGE_KEY}")
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        ts = data.get("Time Series FX (Daily)", {})
        if not ts: return None
        dates = sorted(ts.keys())
        closes = [float(ts[d]["4. close"]) for d in dates]
        return pd.Series(closes, index=pd.to_datetime(dates))
    except: return None

def fetch_best(info):
    results = {}
    y = fetch_yahoo(info["yahoo"])
    if y is not None: results["Yahoo Finance"] = y
    if info.get("alpha") and ALPHA_VANTAGE_KEY != "YOUR_API_KEY_HERE":
        a = fetch_alpha(info["alpha"])
        if a is not None: results["Alpha Vantage"] = a
    if not results: return None, None, {}
    best_source = max(results, key=lambda k: len(results[k]))
    return results[best_source], best_source, results

def fit_garch(series):
    try:
        s = pd.Series(series.values, dtype=float)
        returns = 100 * s.pct_change().dropna()
        if len(returns) < 30: return None
        model = arch_model(returns, vol='Garch', p=1, q=1, dist='normal', rescale=False)
        res = model.fit(disp='off', show_warning=False)
        alpha = float(res.params.get('alpha[1]', 0.05))
        beta  = float(res.params.get('beta[1]', 0.90))
        persistence = alpha + beta
        return {
            "persistence": round(persistence, 4),
            "cond_vol": round(float(res.conditional_volatility.iloc[-1]), 4),
            "forecast_vol": round(float(np.sqrt(res.forecast(horizon=1).variance.values[-1, 0])), 4),
            "stability": "STABLE" if persistence < 0.95 else "MODERATE" if persistence < 0.99 else "EXPLOSIVE",
            "returns": returns.tail(60).tolist(),
            "cvol_series": res.conditional_volatility.tail(60).tolist()
        }
    except: return None

# ─── سیگنال دهی و تحلیل نهایی ───
def analyze_all():
    results = {}
    print("📊 در حال به‌روزرسانی داشبورد...")
    for name, info in MARKETS.items():
        series, source, all_sources = fetch_best(info)
        if series is None: continue
        g = fit_garch(series)
        cur = float(series.iloc[-1])
        prev = float(series.iloc[-2])
        chg = (cur - prev) / prev * 100
        
        results[name] = {
            "price": round(cur, 4), "change_pct": round(chg, 2),
            "flag": info["flag"], "tv_url": info["tv"], "source": source,
            "type": info.get("type", "market"), "garch": g
        }
        print(f"✅ {name} به‌روز شد.")
    return results

# ─── ساخت HTML ───
def build_html(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    audjpy = results.get("AUD/JPY", {})
    rets = audjpy.get("garch", {}).get("returns", []) if audjpy else []
    cvols = audjpy.get("garch", {}).get("cvol_series", []) if audjpy else []

    # بدنه اصلی HTML ناتمام شما در اینجا تکمیل شده است
    rows_html = ""
    for name, r in results.items():
        g = r.get("garch")
        vol = g["cond_vol"] if g else "N/A"
        rows_html += f"<tr><td>{r['flag']} {name}</td><td>{r['price']}</td><td>{r['change_pct']}%</td><td>{vol}%</td><td><a href='{r['tv_url']}' target='_blank'>📈</a></td></tr>"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>GARCH Dashboard Live</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
        <style>
            body {{ background: #0a0e1a; color: white; font-family: sans-serif; padding: 20px; }}
            .panel {{ background: #0d1525; border: 1px solid #1e2d45; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 10px; text-align: right; border-bottom: 1px solid #1e2d45; }}
            th {{ color: #4da6ff; }}
            canvas {{ max-height: 300px; }}
        </style>
    </head>
    <body>
        <div class="panel">
            <h2>داشبورد زنده نوسانات (GARCH)</h2>
            <p>آخرین به‌روزرسانی: {now}</p>
        </div>
        <div class="panel">
            <canvas id="chart"></canvas>
        </div>
        <div class="panel">
            <table>
                <thead><tr><th>بازار</th><th>قیمت</th><th>تغییر</th><th>نوسان GARCH</th><th>چارت</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        <script>
            new Chart(document.getElementById('chart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps([f"T-{i}" for i in range(len(rets))][::-1])},
                    datasets: [
                        {{ label: 'Returns', data: {json.dumps(rets)}, borderColor: '#00ff88', yAxisID: 'y' }},
                        {{ label: 'GARCH Vol', data: {json.dumps(cvols)}, borderColor: '#4da6ff', yAxisID: 'y1' }}
                    ]
                }},
                options: {{ scales: {{ y: {{ position: 'left' }}, y1: {{ position: 'right' }} }} }}
            }});
        </script>
    </body></html>"""
    return html_template

if __name__ == "__main__":
    data_results = analyze_all()
    if data_results:
        html = build_html(data_results)
        # مسیر ذخیره بر اساس تصویر شما
        folder_path = r"C:\Users\ahhum\OneDrive\Documents\آسیا\بزنس"
        if not os.path.exists(folder_path): os.makedirs(folder_path)
        file_path = os.path.join(folder_path, "garch_dashboard_live.html")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"\n🚀 داشبورد با موفقیت ایجاد شد:\n{file_path}")
        webbrowser.open(f"file:///{file_path}")
