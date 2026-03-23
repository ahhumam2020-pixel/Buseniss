import os
from datetime import datetime
import yfinance as yf
import pandas as pd
from arch import arch_model
import json
import numpy as np   # ← این خط را اضافه کنید

def calculate_atr(df, period=14):
    """محاسبه ATR(14) برای SL/TP"""
    high = df['High']
    low = df['Low'] 
    close = df['Close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

import os
from datetime import datetime
import yfinance as yf
import pandas as pd
from arch import arch_model
import json
import numpy as np

def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low'] 
    close = df['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def analyze():
    results = {}
    ALL_MARKETS = {
        "AUD/JPY": {"yahoo": "AUDJPY=X"},
        "USD/JPY": {"yahoo": "JPY=X"},
        "HSI": {"yahoo": "^HSI"},
        "ASX200": {"yahoo": "^AXJO"},
        "Bitcoin": {"yahoo": "BTC-USD"},
    }
    
    for name, info in ALL_MARKETS.items():
        try:
            df = yf.download(info["yahoo"], period="60d", progress=False)
            close = df['Close'].dropna()
            returns = 100 * close.pct_change().dropna()
            
            model = arch_model(returns, vol="Garch", p=1, q=1)
            res = model.fit(disp="off")
            
            atr = calculate_atr(df)
            price = close.iloc[-1]
            signal = "LONG" if returns.iloc[-1] > 0 else "SHORT"
            
            sl_distance = atr * 1.2
            tp_distance = sl_distance * 2.5
            sl = price - sl_distance if signal=="LONG" else price + sl_distance
            tp = price + tp_distance if signal=="LONG" else price - tp_distance
            rr = abs(tp-price)/abs(sl-price)
            
            results[name] = {
                "price": round(price,4),
                "signal": signal,
                "sl": round(sl,4), "tp": round(tp,4),
                "rr": round(rr,2),
                "confidence": "⭐⭐⭐⭐" if rr>2 else "⭐⭐⭐"
            }
            print(f"✅ {name}: {signal} R/R={rr}")
        except:
            pass
    return results

# بقیه کد مثل قبل...
