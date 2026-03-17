#!/usr/bin/env python3
"""
ORCL (Oracle) 单股票回测分析
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("   ORCL (Oracle) 回测分析")
print("="*70)

# 下载ORCL历史数据
ticker = 'ORCL'
print(f"\n[1/4] 下载 {ticker} 历史数据...")

stock = yf.Ticker(ticker)
df = stock.history(period='3y')  # 下载3年数据

if df.empty:
    print("数据下载失败!")
    sys.exit(1)

print(f"  数据区间: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
print(f"  数据条数: {len(df)}")
print(f"  当前价格: ${df['Close'].iloc[-1]:.2f}")

# 计算技术指标
print("\n[2/4] 计算技术指标...")

# 移动平均线
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA50'] = df['Close'].rolling(window=50).mean()
df['MA200'] = df['Close'].rolling(window=200).mean()

# RSI
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# MACD
exp1 = df['Close'].ewm(span=12, adjust=False).mean()
exp2 = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = exp1 - exp2
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
df['Histogram'] = df['MACD'] - df['Signal']

# 波动率
df['Returns'] = df['Close'].pct_change()
df['Volatility'] = df['Returns'].rolling(window=20).std() * np.sqrt(252)

# 当前技术指标
latest = df.iloc[-1]
prev = df.iloc[-2]

print(f"\n  --- 当前技术指标 ({df.index[-1].strftime('%Y-%m-%d')}) ---")
print(f"  收盘价:    ${latest['Close']:.2f}")
print(f"  MA20:      ${latest['MA20']:.2f}")
print(f"  MA50:      ${latest['MA50']:.2f}")
print(f"  MA200:     ${latest['MA200']:.2f}")
print(f"  RSI(14):   {latest['RSI']:.1f}")
print(f"  MACD:      {latest['MACD']:.3f}")
print(f"  信号线:    {latest['Signal']:.3f}")
print(f"  波动率:    {latest['Volatility']*100:.1f}%")

# 简单回测策略：MA20上穿买入，下穿卖出
print("\n[3/4] 运行MA策略回测...")

df['Position'] = 0
df['Position'] = np.where(df['Close'] > df['MA20'], 1, 0)  # 价格在MA20上方持有多头
df['Position'] = df['Position'].shift(1)  # 延迟一天执行
df['Strategy_Returns'] = df['Position'] * df['Returns']

# 计算累计收益
df['Cumulative_Market'] = (1 + df['Returns']).cumprod()
df['Cumulative_Strategy'] = (1 + df['Strategy_Returns']).cumprod()

# 绩效指标
def calculate_metrics(returns_series):
    returns = returns_series.dropna()
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    max_dd = ((returns.cumsum() + 1).cummax() - (returns.cumsum() + 1)).max()
    win_rate = (returns > 0).sum() / len(returns)
    
    return {
        '总收益': total_return,
        '年化收益': annual_return,
        '年化波动': volatility,
        '夏普比率': sharpe,
        '最大回撤': max_dd,
        '胜率': win_rate
    }

market_metrics = calculate_metrics(df['Returns'])
strategy_metrics = calculate_metrics(df['Strategy_Returns'])

print(f"\n  --- 回测绩效 ({len(df)} 个交易日) ---")
print(f"  {'指标':<15} {'买入持有':>12} {'MA策略':>12}")
print("  " + "-"*40)
for key in ['总收益', '年化收益', '年化波动', '夏普比率', '最大回撤', '胜率']:
    if key == '胜率':
        print(f"  {key:<15} {market_metrics[key]*100:>11.1f}% {strategy_metrics[key]*100:>11.1f}%")
    else:
        print(f"  {key:<15} {market_metrics[key]*100:>11.1f}% {strategy_metrics[key]*100:>11.1f}%")

# 近期表现
print("\n[4/4] 近期表现...")
recent_periods = [5, 20, 60, 126, 252]
print(f"\n  {'周期':<10} {'收益率':>12}")
print("  " + "-"*25)
for period in recent_periods:
    if len(df) >= period:
        recent_return = df['Close'].iloc[-1] / df['Close'].iloc[-period] - 1
        label = {5: '5天', 20: '1个月', 60: '3个月', 126: '6个月', 252: '1年'}[period]
        print(f"  {label:<10} {recent_return*100:>+11.1f}%")

# 交易信号
print("\n" + "="*70)
print("   当前交易信号")
print("="*70)

signals = []

# MA信号
if latest['Close'] > latest['MA20']:
    signals.append("MA20: 多头 (价格在均线上方)")
else:
    signals.append("MA20: 空头 (价格在均线下方)")

# RSI信号
if latest['RSI'] > 70:
    signals.append(f"RSI: 超买 ({latest['RSI']:.1f})")
elif latest['RSI'] < 30:
    signals.append(f"RSI: 超卖 ({latest['RSI']:.1f})")
else:
    signals.append(f"RSI: 中性 ({latest['RSI']:.1f})")

# MACD信号
if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
    signals.append("MACD: 金叉 (买入信号)")
elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
    signals.append("MACD: 死叉 (卖出信号)")
elif latest['MACD'] > latest['Signal']:
    signals.append("MACD: 多头")
else:
    signals.append("MACD: 空头")

print()
for signal in signals:
    print(f"  - {signal}")

# 综合建议
print("\n" + "="*70)
print("   综合建议")
print("="*70)

buy_signals = sum([
    latest['Close'] > latest['MA20'],
    latest['RSI'] < 70 and latest['RSI'] > 50,
    latest['MACD'] > latest['Signal']
])

sell_signals = sum([
    latest['Close'] < latest['MA20'],
    latest['RSI'] > 70 or latest['RSI'] < 30,
    latest['MACD'] < latest['Signal']
])

if buy_signals >= 2:
    recommendation = "看多 (BULLISH)"
elif sell_signals >= 2:
    recommendation = "看空 (BEARISH)"
else:
    recommendation = "观望 (NEUTRAL)"

print(f"\n  综合评级: {recommendation}")
print(f"  多头因子: {buy_signals}/3")
print(f"  空头因子: {sell_signals}/3")

print("\n" + "="*70)
print("   回测完成!")
print("="*70)

# 保存结果
df.to_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\ORCL_backtest.csv')
print(f"\n详细数据已保存: ORCL_backtest.csv")
