def analyze():
    results = {}
    
    # APAC INDEXES
    APAC = {"HSI": "^HSI", "ASX200": "^AXJO", "Shanghai": "000001.SS", "KOSPI": "^KS11"}
    
    for name, symbol in {**MARKETS, **APAC}.items():
        df = yf.download(symbol, period="6mo", progress=False)
        close = df['Close'].dropna()
        returns = 100 * close.pct_change().dropna()
        
        # GARCH(1,1)
        model = arch_model(returns, vol="Garch", p=1, q=1)
        res = model.fit(disp="off")
        
        # 1-DAY FORECAST
        forecast = res.forecast(horizon=1)
        vol_forecast = np.sqrt(forecast.variance.iloc[-1, 0])
        
        # TRADING SIGNALS
        atr = calculate_atr(close.tail(14))  # ATR(14)
        price = close.iloc[-1]
        signal = "LONG" if returns.iloc[-1] > 0 else "SHORT"
        
        sl = price * (1 - 0.02 if signal == "LONG" else +0.02)  # 2% SL
        tp = price * (1 + 0.10 if signal == "LONG" else -0.10)  # 10% TP
        rr_ratio = abs(tp - price) / abs(sl - price)
        confidence = min(5, int(rr_ratio * 2))  # ⭐ تبدیل
        
        results[name] = {
            "price": round(price, 4),
            "change": round(returns.iloc[-1], 2),
            "vol": round(res.conditional_volatility.iloc[-1], 4),
            "vol_forecast": round(vol_forecast, 4),
            "atr": round(atr, 4),
            "signal": signal,
            "sl": round(sl, 4), "tp": round(tp, 4),
            "rr": round(rr_ratio, 2),
            "confidence": "⭐" * confidence,
            "persistence": round(res.params['beta[1]'] + res.params['alpha[1]'], 3)
        }
    return results
