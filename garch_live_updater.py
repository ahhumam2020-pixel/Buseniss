#!/usr/bin/env python3
"""
GARCH Live Dashboard Updater v3
منابع: Yahoo Finance + Alpha Vantage (اختیاری) + TradingView (لینک چارت)
"""

import yfinance as yf
import numpy as np
import pandas as pd
from arch import arch_model
from datetime import datetime
import json, os, sys

# ─────────────────────────────────────────────
# Alpha Vantage API Key
# برای دریافت رایگان: https://www.alphavantage.co/support/#api-key
# ─────────────────────────────────────────────
ALPHA_VANTAGE_KEY = "YOUR_API_KEY_HERE"  # <-- بعداً اینجا key خود را وارد کنید

MARKETS = {
    "AUD/JPY": {
        "yahoo":   "AUDJPY=X",
        "alpha":   "AUDJPY",
        "tv":      "https://www.tradingview.com/chart/?symbol=AUDJPY",
        "session": "AUS", "flag": "au"
    },
    "USD/JPY": {
        "yahoo":   "JPY=X",
        "alpha":   "USDJPY",
        "tv":      "https://www.tradingview.com/chart/?symbol=USDJPY",
        "session": "JAPAN", "flag": "jp"
    },
    "USD/CNH": {
        "yahoo":   "USDCNH=X",
        "alpha":   "USDCNH",
        "tv":      "https://www.tradingview.com/chart/?symbol=USDCNH",
        "session": "CHINA", "flag": "cn"
    },
    "HSI": {
        "yahoo":   "^HSI",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=HSI",
        "session": "HK", "flag": "hk"
    },
    "AUD/USD": {
        "yahoo":   "AUDUSD=X",
        "alpha":   "AUDUSD",
        "tv":      "https://www.tradingview.com/chart/?symbol=AUDUSD",
        "session": "AUS", "flag": "au"
    },
    "EUR/USD": {
        "yahoo":   "EURUSD=X",
        "alpha":   "EURUSD",
        "tv":      "https://www.tradingview.com/chart/?symbol=EURUSD",
        "session": "EU", "flag": "eu"
    },
    "Nikkei 225": {
        "yahoo":   "^N225",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=NKY",
        "session": "JAPAN", "flag": "jp"
    },
    "ASX 200": {
        "yahoo":   "^AXJO",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=ASX:XJO",
        "session": "AUS", "flag": "au"
    },
    "Shanghai": {
        "yahoo":   "000001.SS",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=SSE:000001",
        "session": "CHINA", "flag": "cn"
    },
    "KOSPI": {
        "yahoo":   "^KS11",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=KRX:KOSPI",
        "session": "KOREA", "flag": "kr"
    },
    # ─── ارزهای دیجیتال ───
    "Bitcoin": {
        "yahoo":   "BTC-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT",
        "session": "CRYPTO", "flag": "btc", "type": "crypto"
    },
    "Ethereum": {
        "yahoo":   "ETH-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:ETHUSDT",
        "session": "CRYPTO", "flag": "eth", "type": "crypto"
    },
    "Solana": {
        "yahoo":   "SOL-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:SOLUSDT",
        "session": "CRYPTO", "flag": "sol", "type": "crypto"
    },
    "XRP": {
        "yahoo":   "XRP-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:XRPUSDT",
        "session": "CRYPTO", "flag": "xrp", "type": "crypto"
    },
    "Dogecoin": {
        "yahoo":   "DOGE-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:DOGEUSDT",
        "session": "CRYPTO", "flag": "doge", "type": "crypto"
    },
    "Chainlink": {
        "yahoo":   "LINK-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:LINKUSDT",
        "session": "CRYPTO", "flag": "link", "type": "crypto"
    },
    "Avalanche": {
        "yahoo":   "AVAX-USD",
        "alpha":   None,
        "tv":      "https://www.tradingview.com/chart/?symbol=BINANCE:AVAXUSDT",
        "session": "CRYPTO", "flag": "avax", "type": "crypto"
    },
}

# ─────────────────────────────────────────────
# Yahoo Finance
# ─────────────────────────────────────────────
def fetch_yahoo(ticker, period="6mo"):
    try:
        raw = yf.download(ticker, period=period, interval="1d",
                          progress=False, auto_adjust=True)
        if raw is None or raw.empty:
            return None
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ['_'.join([c for c in col if c]).strip('_')
                           for col in raw.columns]
        close_col = next((c for c in raw.columns if 'close' in c.lower()), None)
        if close_col is None:
            return None
        s = raw[close_col].dropna()
        return s if len(s) >= 10 else None
    except:
        return None

# ─────────────────────────────────────────────
# Alpha Vantage
# ─────────────────────────────────────────────
def fetch_alpha(symbol):
    if ALPHA_VANTAGE_KEY == "YOUR_API_KEY_HERE" or symbol is None:
        return None
    try:
        import urllib.request
        url = (f"https://www.alphavantage.co/query"
               f"?function=FX_DAILY&from_symbol={symbol[:3]}"
               f"&to_symbol={symbol[3:]}&outputsize=compact"
               f"&apikey={ALPHA_VANTAGE_KEY}")
        with urllib.request.urlopen(url, timeout=10) as r:
            import json as j
            data = j.loads(r.read())
        ts = data.get("Time Series FX (Daily)", {})
        if not ts:
            return None
        dates = sorted(ts.keys())
        closes = [float(ts[d]["4. close"]) for d in dates]
        s = pd.Series(closes, index=pd.to_datetime(dates))
        return s if len(s) >= 10 else None
    except:
        return None

# ─────────────────────────────────────────────
# انتخاب بهترین منبع
# ─────────────────────────────────────────────
def fetch_best(info):
    """Yahoo و Alpha Vantage هر دو را امتحان می‌کند — بهترین را برمی‌گرداند"""
    results = {}

    # Yahoo
    y = fetch_yahoo(info["yahoo"])
    if y is not None:
        results["Yahoo Finance"] = y
        print(f"       Yahoo Finance: {len(y)} روز ✅")
    else:
        print(f"       Yahoo Finance: رد شد ⚠️")

    # Alpha Vantage
    if info.get("alpha") and ALPHA_VANTAGE_KEY != "YOUR_API_KEY_HERE":
        a = fetch_alpha(info["alpha"])
        if a is not None:
            results["Alpha Vantage"] = a
            print(f"       Alpha Vantage: {len(a)} روز ✅")
        else:
            print(f"       Alpha Vantage: رد شد ⚠️")
    elif ALPHA_VANTAGE_KEY == "YOUR_API_KEY_HERE":
        print(f"       Alpha Vantage: API key تنظیم نشده")

    if not results:
        return None, None

    # بهترین منبع = بیشترین داده
    best_source = max(results, key=lambda k: len(results[k]))
    return results[best_source], best_source, results

# ─────────────────────────────────────────────
# GARCH
# ─────────────────────────────────────────────
def fit_garch(series):
    try:
        s = pd.Series(series.values, dtype=float)
        returns = 100 * s.pct_change().dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        if len(returns) < 30:
            return None
        model = arch_model(returns, vol='Garch', p=1, q=1,
                           dist='normal', rescale=False)
        res = model.fit(disp='off', show_warning=False)
        params = res.params
        alpha = float(params.get('alpha[1]', params.iloc[2] if len(params)>2 else 0))
        beta  = float(params.get('beta[1]',  params.iloc[3] if len(params)>3 else 0))
        persistence = alpha + beta
        cond_vol  = float(res.conditional_volatility.iloc[-1])
        fcast     = res.forecast(horizon=1)
        fcast_vol = float(np.sqrt(fcast.variance.values[-1, 0]))
        stability = ("STABLE" if persistence < 0.95
                     else "MODERATE" if persistence < 0.99 else "EXPLOSIVE")
        return {
            "alpha": round(alpha, 4),
            "beta":  round(beta, 4),
            "persistence": round(persistence, 4),
            "cond_vol":    round(cond_vol, 4),
            "forecast_vol":round(fcast_vol, 4),
            "stability":   stability,
            "returns":     returns.tail(60).tolist(),
            "cvol_series": res.conditional_volatility.tail(60).tolist(),
        }
    except Exception as e:
        print(f"       GARCH خطا: {e}")
        return None

def calc_atr(series, period=14):
    """محاسبه ATR برای تعیین Stop Loss منطقی"""
    try:
        s = pd.Series(series.values, dtype=float)
        high = s.rolling(2).max()
        low  = s.rolling(2).min()
        tr   = high - low
        atr  = tr.rolling(period).mean().iloc[-1]
        return round(float(atr), 6) if not np.isnan(atr) else None
    except:
        return None

def calc_support_resistance(series, window=20):
    """شناسایی سطوح حمایت و مقاومت کلیدی"""
    try:
        s = pd.Series(series.values, dtype=float)
        recent = s.tail(window)
        support    = round(float(recent.min()), 6)
        resistance = round(float(recent.max()), 6)
        pivot      = round(float((recent.max() + recent.min() + recent.iloc[-1]) / 3), 6)
        return {"support": support, "resistance": resistance, "pivot": pivot}
    except:
        return None

def calc_order_blocks(series, window=5):
    """شناسایی Order Block های صعودی و نزولی"""
    try:
        s = pd.Series(series.values, dtype=float)
        recent = s.tail(20)
        # Bullish OB: آخرین کف قوی قبل از حرکت صعودی
        bull_ob = round(float(recent.nsmallest(3).mean()), 6)
        # Bearish OB: آخرین سقف قوی قبل از حرکت نزولی
        bear_ob = round(float(recent.nlargest(3).mean()), 6)
        return {"bullish_ob": bull_ob, "bearish_ob": bear_ob}
    except:
        return None

def calc_fvg(series):
    """شناسایی Fair Value Gap"""
    try:
        s = pd.Series(series.values, dtype=float)
        recent = s.tail(10)
        gaps = []
        for i in range(1, len(recent)-1):
            gap = abs(recent.iloc[i+1] - recent.iloc[i-1])
            gap_pct = gap / recent.iloc[i] * 100
            if gap_pct > 0.5:
                gaps.append({
                    "level": round(float((recent.iloc[i+1] + recent.iloc[i-1]) / 2), 6),
                    "size_pct": round(gap_pct, 3)
                })
        return gaps[-1] if gaps else None
    except:
        return None

def get_signal(garch, cur, prev, series=None):
    if garch is None:
        return {"direction":"NEUTRAL","entry":cur,"tp":cur,"sl":cur,
                "confidence":50,"rr":1,"atr":None,"sr":None,"ob":None,"fvg":None}
    
    fvol = garch["forecast_vol"]
    mom  = (cur - prev) / prev * 100 if prev else 0
    
    # ATR برای Stop Loss دقیق‌تر
    atr = calc_atr(series) if series is not None else None
    sr  = calc_support_resistance(series) if series is not None else None
    ob  = calc_order_blocks(series) if series is not None else None
    fvg = calc_fvg(series) if series is not None else None
    
    # تعیین جهت
    if mom > 0.05:
        d = "LONG"
        # Entry: نزدیک به Bullish Order Block یا سطح حمایت
        if ob and sr:
            entry = round(max(ob["bullish_ob"], sr["support"] * 1.001), 6)
        else:
            entry = round(cur, 6)
        # SL: زیر Order Block یا بر اساس ATR
        if atr and ob:
            sl = round(min(ob["bullish_ob"] - atr, cur * (1 - fvol/100)), 6)
        elif sr:
            sl = round(sr["support"] * 0.998, 6)
        else:
            sl = round(cur * (1 - fvol/100), 6)
        # TP: نزدیک به Bearish OB یا مقاومت
        if ob and sr:
            tp = round(min(ob["bearish_ob"], sr["resistance"] * 0.999), 6)
        else:
            tp = round(cur * (1 + fvol/100 * 2), 6)
    elif mom < -0.05:
        d = "SHORT"
        if ob and sr:
            entry = round(min(ob["bearish_ob"], sr["resistance"] * 0.999), 6)
        else:
            entry = round(cur, 6)
        if atr and ob:
            sl = round(max(ob["bearish_ob"] + atr, cur * (1 + fvol/100)), 6)
        elif sr:
            sl = round(sr["resistance"] * 1.002, 6)
        else:
            sl = round(cur * (1 + fvol/100), 6)
        if ob and sr:
            tp = round(max(ob["bullish_ob"], sr["support"] * 1.001), 6)
        else:
            tp = round(cur * (1 - fvol/100 * 2), 6)
    else:
        d = "NEUTRAL"
        entry = round(cur, 6)
        tp    = round(cur * 1.005, 6)
        sl    = round(cur * 0.995, 6)
    
    # اطمینان از معقول بودن SL و TP
    if d == "LONG" and sl >= entry:
        sl = round(entry * 0.995, 6)
    if d == "LONG" and tp <= entry:
        tp = round(entry * 1.01, 6)
    if d == "SHORT" and sl <= entry:
        sl = round(entry * 1.005, 6)
    if d == "SHORT" and tp >= entry:
        tp = round(entry * 0.99, 6)
    
    conf = min(90, int(70 + (0.99 - garch["persistence"]) * 100))
    rr   = round(abs(tp-entry)/abs(sl-entry), 2) if abs(sl-entry) > 0 else 1
    
    return {
        "direction": d, "entry": entry, "tp": tp, "sl": sl,
        "confidence": conf, "rr": rr,
        "atr": atr, "sr": sr, "ob": ob, "fvg": fvg
    }

# ─────────────────────────────────────────────
# تحلیل همه بازارها
# ─────────────────────────────────────────────
def analyze_all():
    results = {}
    print("\n📊 دریافت داده‌ها...\n")
    for name, info in MARKETS.items():
        print(f"  {name} ({info['yahoo']}) ...")
        out = fetch_best(info)
        if out is None or out[0] is None:
            print(f"     رد شد\n")
            continue
        series, source, all_sources = out
        cur  = float(series.iloc[-1])
        prev = float(series.iloc[-2]) if len(series)>1 else cur
        chg  = round((cur-prev)/prev*100, 4) if prev else 0
        g    = fit_garch(series)
        sig  = get_signal(g, cur, prev, series)

        # مقایسه منابع
        comparison = {}
        for src, s in all_sources.items():
            comparison[src] = round(float(s.iloc[-1]), 4)

        results[name] = {
            "yahoo": info["yahoo"], "session": info["session"],
            "flag":  info["flag"],  "tv_url":  info["tv"],
            "price": round(cur,4),  "change_pct": chg,
            "direction_up": chg>=0, "source": source,
            "comparison": comparison,
            "type": info.get("type", "market"),
            "garch": g, "signal": sig,
        }
        vol_str = f"{g['cond_vol']}%" if g else "N/A"
        print(f"     ✅ منبع: {source} | قیمت: {cur:.4f} | تغییر: {chg:+.2f}% | نوسانات: {vol_str}\n")
    return results

# ─────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────
def gv(r,k,d="N/A"):
    g=r.get("garch"); return g.get(k,d) if g else d

def sv(r,k,d="N/A"):
    s=r.get("signal"); return s.get(k,d) if s else d

def build_html(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    alpha_active = ALPHA_VANTAGE_KEY != "YOUR_API_KEY_HERE"
    alpha_status = "فعال ✅" if alpha_active else "نیاز به API key"

    def ticker_item(name, r):
        chg   = r.get("change_pct", 0)
        arrow = "▲" if chg>=0 else "▼"
        color = "#00ff88" if chg>=0 else "#ff4444"
        vol   = gv(r,"cond_vol","")
        sigma = f"σ={vol}%" if vol not in ("N/A","") else ""
        src   = r.get("source","")
        return (f'<span class="ticker-item">'
                f'<span class="tsig">{sigma}</span>'
                f'<span style="color:{color}">{abs(chg):.2f}% {arrow}</span>'
                f'<strong>{r.get("price","N/A")}</strong>'
                f'<span class="tname">{name}</span>'
                f'<span class="tsrc">{src}</span></span>')

    ticker_html = "".join([ticker_item(k,v) for k,v in results.items()]*4)

    audjpy = results.get("AUD/JPY", {})
    usdjpy = results.get("USD/JPY", {})
    rets   = gv(audjpy,"returns",[])
    cvols  = gv(audjpy,"cvol_series",[])

    persist = gv(audjpy,"persistence","N/A")
    cond_v  = gv(usdjpy,"cond_vol","N/A")
    fcast_v = gv(audjpy,"forecast_vol","N/A")
    stab    = gv(audjpy,"stability","STABLE")
    sc      = {"STABLE":"#00ff88","MODERATE":"#ffa500","EXPLOSIVE":"#ff4444"}.get(stab,"#00ff88")

    # سیگنال‌ها — بازارها و کریپتو جداگانه
    def make_signal_card(name, r):
        sig = r.get("signal")
        if not sig: return ""
        d  = sig["direction"]
        bg = "#00ff88" if d=="LONG" else ("#ff4444" if d=="SHORT" else "#888")
        arrow_s = "↑" if d=="LONG" else ("↓" if d=="SHORT" else "→")
        tv_url  = r.get("tv_url","#")
        src     = r.get("source","Yahoo Finance")
        src_color = "#4da6ff" if src=="Alpha Vantage" else "#00cc66"
        is_crypto = r.get("type") == "crypto"
        border_color = "#f7931a44" if is_crypto else "#1e2d45"
        
        comp = r.get("comparison",{})
        comp_html = "".join([f'<span style="color:{"#4da6ff" if s=="Alpha Vantage" else "#00cc66"};font-size:10px">{s}: {p}</span> ' for s,p in comp.items()])
        
        # ATR و سطوح پیشرفته
        atr  = sig.get("atr")
        sr   = sig.get("sr")
        ob   = sig.get("ob")
        fvg  = sig.get("fvg")
        
        adv_html = ""
        if sr:
            adv_html += f'<div class="adv-row"><span class="adv-label">حمایت</span><span class="adv-val" style="color:#00ff8888">{sr["support"]}</span><span class="adv-label">مقاومت</span><span class="adv-val" style="color:#ff444488">{sr["resistance"]}</span><span class="adv-label">Pivot</span><span class="adv-val" style="color:#ffa50088">{sr["pivot"]}</span></div>'
        if ob:
            adv_html += f'<div class="adv-row"><span class="adv-label">Bullish OB</span><span class="adv-val" style="color:#00ff8866">{ob["bullish_ob"]}</span><span class="adv-label">Bearish OB</span><span class="adv-val" style="color:#ff444466">{ob["bearish_ob"]}</span>{f'<span class="adv-label">ATR</span><span class="adv-val" style="color:#ffa500">{atr}</span>' if atr else ""}</div>'
        if fvg:
            adv_html += f'<div class="adv-row"><span class="adv-label">FVG Level</span><span class="adv-val" style="color:#a0a0ff">{fvg["level"]}</span><span class="adv-label">Gap</span><span class="adv-val" style="color:#a0a0ff">{fvg["size_pct"]}%</span></div>'
        
        crypto_badge = '<span style="background:#f7931a22;color:#f7931a;border:1px solid #f7931a44;padding:2px 6px;border-radius:3px;font-size:9px">CRYPTO</span>' if is_crypto else ""
        
        return f"""
        <div class="scard" style="border-color:{border_color}">
          <div class="sh">
            <span class="sbadge" style="background:{bg}22;color:{bg};border:1px solid {bg}44">{arrow_s} {d}</span>
            <span class="smkt"><span class="fl">{r.get("flag","")}</span> {name} {crypto_badge}</span>
            <a href="{tv_url}" target="_blank" class="tv-btn">📈 TV</a>
          </div>
          <div class="src-row">{comp_html}</div>
          <div class="slvl">
            <div><span class="lb">ورود بهینه</span><span class="vl">{sig["entry"]}</span></div>
            <div><span class="lb">Take Profit</span><span class="vl" style="color:#00ff88">{sig["tp"]}</span></div>
            <div><span class="lb">Stop Loss</span><span class="vl" style="color:#ff4444">{sig["sl"]}</span></div>
          </div>
          {adv_html}
          <div class="sf">Confidence: {sig["confidence"]}% · R/R: 1:{sig["rr"]} · <span style="color:{src_color}">{src}</span></div>
        </div>"""
    
    signals_html = "".join([make_signal_card(k,v) for k,v in results.items() if v.get("type","market") != "crypto"])
    crypto_html  = "".join([make_signal_card(k,v) for k,v in results.items() if v.get("type") == "crypto"])

    # جدول بازارها (غیر کریپتو)
    def make_row(k, v, is_crypto=False):
        chg  = v.get("change_pct",0)
        cls  = "up" if chg>=0 else "dn"
        arrow= "▲" if chg>=0 else "▼"
        sig  = v.get("signal",{})
        d    = sig.get("direction","—") if sig else "—"
        dcls = "up" if d=="LONG" else ("dn" if d=="SHORT" else "")
        tv   = v.get("tv_url","#")
        src  = v.get("source","—")
        entry= sig.get("entry","—") if sig else "—"
        tp   = sig.get("tp","—") if sig else "—"
        sl   = sig.get("sl","—") if sig else "—"
        rr   = sig.get("rr","—") if sig else "—"
        conf = sig.get("confidence","—") if sig else "—"
        if is_crypto:
            return (f"<tr style='background:#0f1a10'>"
                    f"<td><span style='background:#f7931a22;color:#f7931a;padding:1px 5px;border-radius:3px;font-size:10px'>{k}</span></td>"
                    f"<td><strong>{v.get('price','N/A')}</strong></td>"
                    f"<td class='{cls}'>{arrow} {abs(chg):.2f}%</td>"
                    f"<td>{gv(v,'cond_vol','N/A')}%</td>"
                    f"<td style='color:#00ff88'>{entry}</td>"
                    f"<td style='color:#00ff88'>{tp}</td>"
                    f"<td style='color:#ff4444'>{sl}</td>"
                    f"<td>{rr}</td>"
                    f"<td>{conf}%</td>"
                    f"<td><a href='{tv}' target='_blank' style='color:#f7931a;font-size:11px'>📈</a></td>"
                    f"</tr>")
        else:
            return (f"<tr>"
                    f"<td><span class='fl'>{v.get('flag','')}</span> {k}</td>"
                    f"<td>{v.get('price','N/A')}</td>"
                    f"<td class='{cls}'>{arrow} {abs(chg):.2f}%</td>"
                    f"<td>{gv(v,'cond_vol','N/A')}%</td>"
                    f"<td>{gv(v,'persistence','N/A')}</td>"
                    f"<td style='color:#00ff88'>{entry}</td>"
                    f"<td style='color:#00ff88'>{tp}</td>"
                    f"<td style='color:#ff4444'>{sl}</td>"
                    f"<td class='{dcls}'>{d}</td>"
                    f"<td>{rr}</td>"
                    f"<td><a href='{tv}' target='_blank' style='color:#4da6ff;font-size:11px'>📈</a></td>"
                    f"</tr>")

    rows       = "".join([make_row(k,v) for k,v in results.items() if v.get("type","market")!="crypto"])
    crypto_rows= "".join([make_row(k,v,True) for k,v in results.items() if v.get("type")=="crypto"])

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GARCH // APAC Live v3</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0e1a;color:#e0e6f0;font-family:'Segoe UI',sans-serif}}
.hdr{{display:flex;justify-content:space-between;align-items:center;padding:14px 24px;background:#0d1220;border-bottom:1px solid #1e2d45}}
.hleft{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.live{{background:#00ff8822;color:#00ff88;border:1px solid #00ff8844;padding:5px 14px;border-radius:6px;font-size:13px;display:flex;align-items:center;gap:6px}}
.dot{{width:8px;height:8px;border-radius:50%;background:#00ff88;animation:pulse 1.5s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.sbtn{{background:#1a2540;border:1px solid #2a3a5a;color:#7a9cc0;padding:5px 14px;border-radius:6px;font-size:12px}}
.sbtn.act{{background:#1e3a5f;color:#4da6ff;border-color:#4da6ff55}}
.logo{{font-size:24px;font-weight:700;color:#4da6ff;letter-spacing:3px;font-family:monospace}}
.sub{{font-size:11px;color:#445}}
.ibar{{display:flex;justify-content:space-between;gap:8px;padding:8px 24px;background:#0d1220;border-bottom:1px solid #1a2535;flex-wrap:wrap;align-items:center}}
.itag{{background:#131f35;border:1px solid #1e3050;color:#7a9cc0;padding:3px 10px;border-radius:5px;font-size:11px}}
.src-status{{display:flex;gap:8px;align-items:center}}
.src-badge{{padding:3px 10px;border-radius:5px;font-size:11px;font-weight:600}}
.ubar{{background:#0f1825;padding:5px 24px;font-size:11px;color:#445;border-bottom:1px solid #1a2535;display:flex;justify-content:space-between}}
.ticker{{background:#0d1220;border-bottom:1px solid #1a2535;overflow:hidden;white-space:nowrap;padding:8px 0}}
.ttrack{{display:inline-block;animation:scroll 35s linear infinite}}
@keyframes scroll{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
.ticker-item{{display:inline-flex;align-items:center;gap:6px;margin:0 18px;font-size:13px;font-family:monospace}}
.tsig{{color:#445;font-size:10px}}.tname{{color:#4da6ff;font-weight:600}}
.tsrc{{font-size:9px;color:#334;background:#111827;padding:1px 5px;border-radius:3px}}
.krow{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;padding:18px 24px}}
.kcard{{background:#0d1525;border:1px solid #1e2d45;border-radius:10px;padding:18px}}
.kcard .lbl{{font-size:11px;color:#556;margin-bottom:6px}}
.kcard .val{{font-size:32px;font-weight:700;font-family:monospace;margin:4px 0}}
.kcard .s{{font-size:10px;color:#4da6ff55}}
.badge{{display:inline-block;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;margin-bottom:8px}}
.mgrid{{display:grid;grid-template-columns:1fr 1.6fr;gap:14px;padding:0 24px 20px}}
.panel{{background:#0d1525;border:1px solid #1e2d45;border-radius:10px;padding:16px;overflow-y:auto;max-height:700px}}
.ptitle{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}}
.ptitle h3{{font-size:12px;color:#556}}
.ptitle span{{font-size:11px;color:#4da6ff;font-family:monospace}}
.scard{{background:#111e35;border:1px solid #1e2d45;border-radius:8px;padding:12px;margin-bottom:10px}}
.sh{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:6px}}
.sbadge{{padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700;font-family:monospace}}
.smkt{{font-size:13px;font-weight:600;color:#cde;display:flex;align-items:center;gap:6px}}
.fl{{font-size:10px;background:#1e3050;padding:2px 5px;border-radius:3px;color:#4da6ff}}
.tv-btn{{background:#1a1a40;border:1px solid #4da6ff44;color:#4da6ff;padding:3px 10px;border-radius:5px;font-size:11px;text-decoration:none;white-space:nowrap}}
.tv-btn:hover{{background:#4da6ff22}}
.src-row{{margin-bottom:8px;display:flex;gap:10px;flex-wrap:wrap}}
.slvl{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:8px}}
.lb{{font-size:10px;color:#445;display:block}}.vl{{font-family:monospace;font-size:13px;font-weight:600}}
.sf{{font-size:11px;color:#4da6ff66;border-top:1px solid #1e2d45;padding-top:6px}}
.adv-row{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:6px;padding:4px 0;border-top:1px solid #1a2535}}
.adv-label{{font-size:9px;color:#445}}
.adv-val{{font-size:11px;font-family:monospace;font-weight:600;margin-left:3px}}
canvas{{max-height:250px}}
table{{width:100%;border-collapse:collapse;font-size:11px;margin-top:10px}}
th{{color:#445;font-weight:500;text-align:left;padding:5px 6px;border-bottom:1px solid #1a2535}}
td{{padding:6px;border-bottom:1px solid #12192a;font-family:monospace}}
tr:hover td{{background:#111e35}}
.up{{color:#00ff88}}.dn{{color:#ff4444}}
a{{text-decoration:none}}
@media(max-width:768px){{.krow,.mgrid{{grid-template-columns:1fr}}}}
</style></head><body>

<div class="hdr">
  <div class="hleft">
    <div class="live"><span class="dot"></span> داده‌های واقعی</div>
    <span class="sbtn">HK</span><span class="sbtn">CHINA</span>
    <span class="sbtn">JAPAN</span><span class="sbtn act">AUS SESSION</span>
  </div>
  <div style="text-align:left">
    <div class="logo">GARCH // APAC v3</div>
    <div class="sub">Yahoo Finance + Alpha Vantage + TradingView</div>
  </div>
</div>

<div class="ibar">
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    <span class="itag">مدل: GARCH(1,1)</span>
    <span class="itag">بازه: روزانه</span>
    <span class="itag">کتابخانه: arch · yfinance</span>
  </div>
  <div class="src-status">
    <span class="src-badge" style="background:#00cc6622;color:#00cc66;border:1px solid #00cc6644">Yahoo Finance ✅</span>
    <span class="src-badge" style="background:{"#4da6ff22" if alpha_active else "#44444422"};color:{"#4da6ff" if alpha_active else "#666"};border:1px solid {"#4da6ff44" if alpha_active else "#44444444"}">Alpha Vantage {alpha_status}</span>
    <span class="src-badge" style="background:#ff990022;color:#ff9900;border:1px solid #ff990044">TradingView 📈</span>
  </div>
</div>

<div class="ubar">
  <span>منبع اولیه: بهترین داده انتخاب می‌شود</span>
  <span>آخرین به‌روزرسانی: {now}</span>
</div>

<div class="ticker"><div class="ttrack">{ticker_html}</div></div>

<div class="krow">
  <div class="kcard">
    <span class="badge" style="background:{sc}22;color:{sc};border:1px solid {sc}44">{stab}</span>
    <div class="lbl">ضریب پایداری (α + β) — AUD/JPY</div>
    <div class="val" style="color:{sc}">{persist}</div>
    <div class="s">High Persistence — Shocks Decay Slowly</div>
  </div>
  <div class="kcard">
    <span class="badge" style="background:#ffa50022;color:#ffa500;border:1px solid #ffa50044">MODERATE</span>
    <div class="lbl">نوسانات شرطی روزانه — USD/JPY</div>
    <div class="val" style="color:#00ff88">{cond_v}%</div>
    <div class="s">Daily Conditional Volatility</div>
  </div>
  <div class="kcard">
    <span class="badge" style="background:#ff440022;color:#ff6666;border:1px solid #ff444444">FORECAST</span>
    <div class="lbl">پیش‌بینی نوسانات (1 روز آینده) — AUD/JPY</div>
    <div class="val" style="color:#ff6666">{fcast_v}%</div>
    <div class="s">GARCH Forecast · Next Day</div>
  </div>
</div>

<div class="mgrid">
  <div class="panel">
    <div class="ptitle"><h3>سیگنال‌های معاملاتی — بازارها</h3><span>TRADE SETUPS</span></div>
    {signals_html}
  </div>
  <div class="panel">
    <div class="ptitle"><h3>نمودار نوسانات شرطی — AUD/JPY</h3><span>GARCH(1,1)</span></div>
    <canvas id="chart"></canvas>
    <div style="margin-top:14px;border-top:1px solid #1a2535;padding-top:12px">
      <div class="ptitle"><h3>مقایسه بازارها</h3><span>MARKET OVERVIEW</span></div>
      <table>
        <thead><tr>
          <th>بازار</th><th>قیمت</th><th>تغییر</th>
          <th>نوسانات</th><th>پایداری</th>
          <th>ورود</th><th>TP</th><th>SL</th>
          <th>سیگنال</th><th>R/R</th><th>چارت</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</div>

<!-- بخش کریپتو -->
<div style="padding:0 24px 20px">
  <div class="panel" style="border-color:#f7931a44">
    <div class="ptitle">
      <h3 style="color:#f7931a">ارزهای دیجیتال</h3>
      <span style="color:#f7931a">CRYPTO — GARCH ANALYSIS</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px">
      {crypto_html}
    </div>
    <!-- جدول کریپتو -->
    <div style="margin-top:16px;border-top:1px solid #f7931a22;padding-top:12px">
      <table>
        <thead><tr>
          <th>ارز</th><th>قیمت</th><th>تغییر</th>
          <th>نوسانات GARCH</th><th>ورود بهینه</th>
          <th>Take Profit</th><th>Stop Loss</th>
          <th>R/R</th><th>Confidence</th><th>چارت</th>
        </tr></thead>
        <tbody>{crypto_rows}</tbody>
      </table>
    </div>
  </div>
</div>

<script>
const rets={json.dumps(rets)},cvols={json.dumps(cvols)};
const labels=rets.map((_,i)=>`D-${{rets.length-i}}`);
new Chart(document.getElementById('chart'),{{
  type:'bar',
  data:{{labels,datasets:[
    {{type:'line',label:'Conditional Volatility (σ)',data:cvols,
      borderColor:'#4da6ff',backgroundColor:'#4da6ff22',
      borderWidth:2,pointRadius:0,yAxisID:'y2',tension:.3,fill:true}},
    {{type:'bar',label:'Returns',data:rets,
      backgroundColor:rets.map(v=>v>=0?'#00ff8855':'#ff444455'),
      borderColor:rets.map(v=>v>=0?'#00ff88':'#ff4444'),
      borderWidth:1,yAxisID:'y'}}
  ]}},
  options:{{responsive:true,
    plugins:{{legend:{{labels:{{color:'#778',font:{{size:11}}}}}}}},
    scales:{{
      x:{{ticks:{{color:'#445',maxRotation:0,autoSkip:true,maxTicksLimit:12}},grid:{{color:'#1a2535'}}}},
      y:{{position:'left',ticks:{{color:'#778',font:{{size:10}}}},grid:{{color:'#1a2535'}},
         title:{{display:true,text:'Returns (%)',color:'#445',font:{{size:10}}}}}},
      y2:{{position:'right',ticks:{{color:'#4da6ff88',font:{{size:10}}}},
           grid:{{drawOnChartArea:false}},
           title:{{display:true,text:'Volatility (%)',color:'#4da6ff88',font:{{size:10}}}}}}
    }}
  }}
}});
</script>
</body></html>"""

def main():
    print("="*55)
    print("  GARCH LIVE DASHBOARD UPDATER  v3")
    print("  Yahoo Finance + Alpha Vantage + TradingView")
    print("="*55)
    results = analyze_all()
    if not results:
        print("\n❌ هیچ داده‌ای دریافت نشد.")
        sys.exit(1)
    html = build_html(results)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "garch_dashboard_live.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ داشبورد ذخیره شد:")
    print(f"   {out}")
    print(f"\n📂 در مرورگر باز کنید:")
    print(f"   file:///{out.replace(os.sep,'/')}")
    print("\n" + "="*55)
    print("  برای Alpha Vantage:")
    print("  1. رایگان ثبت نام کنید: alphavantage.co")
    print("  2. API key را در خط 14 وارد کنید:")
    print("     ALPHA_VANTAGE_KEY = 'YOUR_KEY'")
    print("="*55)

if __name__ == "__main__":
    main()
