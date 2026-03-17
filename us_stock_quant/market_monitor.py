import yfinance as yf
import pandas as pd
from datetime import datetime

print("="*70)
print("   美股走势监控")
print("   " + datetime.now().strftime('%Y-%m-%d %H:%M'))
print("="*70)

# 主要指数
indices = {
    'SPY': '标普500 ETF',
    'QQQ': '纳斯达克100 ETF', 
    'DIA': '道琼斯ETF',
    'IWM': '罗素2000 ETF'
}

print("\n【主要指数】")
print(f"{'指数':<12} {'名称':<20} {'现价':>10} {'日涨跌':>10} {'周涨跌':>10}")
print("-"*70)

for ticker, name in indices.items():
    try:
        data = yf.Ticker(ticker).history(period='5d')
        current = data['Close'].iloc[-1]
        day_change = (current / data['Close'].iloc[-2] - 1) * 100
        week_change = (current / data['Close'].iloc[0] - 1) * 100
        print(f"{ticker:<12} {name:<20} ${current:>9.2f} {day_change:>+9.2f}% {week_change:>+9.2f}%")
    except:
        print(f"{ticker:<12} {name:<20} 获取失败")

# 你的持仓相关股票
print("\n【你的持仓股票】")
your_stocks = ['NVDA', 'NVDL', 'SMCI', 'ACN']

print(f"{'股票':<8} {'现价':>10} {'日涨跌':>10} {'周涨跌':>10} {'RSI':>8}")
print("-"*70)

for ticker in your_stocks:
    try:
        data = yf.Ticker(ticker).history(period='20d')
        current = data['Close'].iloc[-1]
        day_change = (current / data['Close'].iloc[-2] - 1) * 100
        week_change = (current / data['Close'].iloc[-5] - 1) * 100 if len(data) >= 5 else 0
        
        # 计算RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        print(f"{ticker:<8} ${current:>9.2f} {day_change:>+9.2f}% {week_change:>+9.2f}% {current_rsi:>7.1f}")
    except:
        print(f"{ticker:<8} 获取失败")

# 热门投机标的
print("\n【热门投机标的】")
speculative = {
    'TSLA': '特斯拉',
    'PLTR': 'Palantir',
    'COIN': 'Coinbase',
    'MSTR': 'MicroStrategy',
    'HOOD': 'Robinhood',
    'CRCL': 'Circle',
    'APP': 'AppLovin',
}

print(f"{'股票':<8} {'名称':<15} {'现价':>10} {'日涨跌':>10} {'月涨跌':>10}")
print("-"*70)

for ticker, name in speculative.items():
    try:
        data = yf.Ticker(ticker).history(period='30d')
        current = data['Close'].iloc[-1]
        day_change = (current / data['Close'].iloc[-2] - 1) * 100
        month_change = (current / data['Close'].iloc[0] - 1) * 100
        print(f"{ticker:<8} {name:<15} ${current:>9.2f} {day_change:>+9.2f}% {month_change:>+9.2f}%")
    except:
        print(f"{ticker:<8} {name:<15} 获取失败")

# 加密货币相关
print("\n【加密货币相关】")
crypto = {
    'BTC-USD': '比特币',
    'ETH-USD': '以太坊',
    'MSTR': 'MicroStrategy',
    'COIN': 'Coinbase',
    'HOOD': 'Robinhood',
}

print(f"{'标的':<12} {'现价':>12} {'日涨跌':>10}")
print("-"*70)

for ticker, name in crypto.items():
    try:
        data = yf.Ticker(ticker).history(period='5d')
        current = data['Close'].iloc[-1]
        day_change = (current / data['Close'].iloc[-2] - 1) * 100
        print(f"{name:<12} ${current:>11.2f} {day_change:>+9.2f}%")
    except:
        pass

print("\n" + "="*70)
