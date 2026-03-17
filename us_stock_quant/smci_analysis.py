#!/usr/bin/env python3
"""
SMCI (Super Micro Computer) 技术分析
支撑位、压力位、短期走势
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
print("   SMCI (Super Micro Computer) 技术分析")
print("   支撑位、压力位、短期走势预测")
print("="*70)

# 下载SMCI历史数据
ticker = 'SMCI'
print(f"\n[1/5] 下载 {ticker} 历史数据...")

stock = yf.Ticker(ticker)
# 下载更多数据用于计算支撑压力
df = stock.history(period='2y')

if df.empty:
    print("数据下载失败!")
    sys.exit(1)

print(f"  数据区间: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
print(f"  数据条数: {len(df)}")
print(f"  当前价格: ${df['Close'].iloc[-1]:.2f}")

# 计算技术指标
print("\n[2/5] 计算技术指标...")

# 移动平均线
df['MA5'] = df['Close'].rolling(window=5).mean()
df['MA10'] = df['Close'].rolling(window=10).mean()
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA50'] = df['Close'].rolling(window=50).mean()
df['MA200'] = df['Close'].rolling(window=200).mean()

# 布林带
df['BB_Middle'] = df['Close'].rolling(window=20).mean()
df['BB_Std'] = df['Close'].rolling(window=20).std()
df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)

# ATR (平均真实波幅)
df['High_Low'] = df['High'] - df['Low']
df['High_Close'] = np.abs(df['High'] - df['Close'].shift())
df['Low_Close'] = np.abs(df['Low'] - df['Close'].shift())
df['TR'] = df[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
df['ATR'] = df['TR'].rolling(window=14).mean()

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

# 成交量
df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()

# 计算支撑位和压力位
print("\n[3/5] 计算支撑位和压力位...")

latest = df.iloc[-1]
prev = df.iloc[-2]
current_price = latest['Close']

# 方法1: 近期高低点 (过去60天)
recent_60d = df.tail(60)
recent_high = recent_60d['High'].max()
recent_low = recent_60d['Low'].min()
recent_high_date = recent_60d['High'].idxmax()
recent_low_date = recent_60d['Low'].idxmin()

# 方法2: 移动平均线
ma_levels = {
    'MA5': latest['MA5'],
    'MA10': latest['MA10'],
    'MA20': latest['MA20'],
    'MA50': latest['MA50'],
    'MA200': latest['MA200']
}

# 方法3: 布林带
bb_upper = latest['BB_Upper']
bb_lower = latest['BB_Lower']
bb_middle = latest['BB_Middle']

# 方法4: 斐波那契回撤 (基于近期高低点)
fib_levels = {}
if recent_high > recent_low:
    diff = recent_high - recent_low
    fib_levels['0%'] = recent_high
    fib_levels['23.6%'] = recent_high - diff * 0.236
    fib_levels['38.2%'] = recent_high - diff * 0.382
    fib_levels['50%'] = recent_high - diff * 0.5
    fib_levels['61.8%'] = recent_high - diff * 0.618
    fib_levels['78.6%'] = recent_high - diff * 0.786
    fib_levels['100%'] = recent_low

# 方法5: 前密集成交区 (成交量加权平均价格)
# 取近期成交量最大的10天的价格区域
vol_threshold = df.tail(30)['Volume'].quantile(0.8)
high_vol_days = df.tail(30)[df.tail(30)['Volume'] >= vol_threshold]
vwap_support = high_vol_days['Low'].min()
vwap_resistance = high_vol_days['High'].max()

print("\n  === 支撑位 (Support Levels) ===")
supports = []

# 近期低点
if recent_low < current_price:
    supports.append(('近期低点', recent_low, f"{recent_low_date.strftime('%Y-%m-%d')}"))

# 斐波那契回撤位
for level, price in fib_levels.items():
    if price < current_price:
        supports.append((f'斐波那契{level}', price, '回撤支撑'))

# 布林带下轨
if bb_lower < current_price:
    supports.append(('布林带下轨', bb_lower, '20日标准差'))

# 移动平均线 (价格在均线上方时，均线是支撑)
for ma_name, ma_val in ma_levels.items():
    if ma_val < current_price and not np.isnan(ma_val):
        supports.append((ma_name, ma_val, '移动平均'))

# 按价格排序
supports = sorted(supports, key=lambda x: x[1], reverse=True)

for name, price, note in supports[:8]:
    dist = (current_price - price) / current_price * 100
    print(f"  {name:<12} ${price:>8.2f}  (-{dist:>5.1f}%)  [{note}]")

print("\n  === 压力位 (Resistance Levels) ===")
resistances = []

# 近期高点
if recent_high > current_price:
    resistances.append(('近期高点', recent_high, f"{recent_high_date.strftime('%Y-%m-%d')}"))

# 斐波那契回撤位
for level, price in fib_levels.items():
    if price > current_price:
        resistances.append((f'斐波那契{level}', price, '回撤阻力'))

# 布林带上轨
if bb_upper > current_price:
    resistances.append(('布林带上轨', bb_upper, '20日标准差'))

# 移动平均线 (价格在均线下方时，均线是压力)
for ma_name, ma_val in ma_levels.items():
    if ma_val > current_price and not np.isnan(ma_val):
        resistances.append((ma_name, ma_val, '移动平均'))

# 按价格排序
resistances = sorted(resistances, key=lambda x: x[1])

for name, price, note in resistances[:8]:
    dist = (price - current_price) / current_price * 100
    print(f"  {name:<12} ${price:>8.2f}  (+{dist:>5.1f}%)  [{note}]")

# 短期走势分析
print("\n[4/5] 短期走势分析...")

# 计算多种信号
signals = {
    '价格vsMA5': '看多' if current_price > latest['MA5'] else '看空',
    '价格vsMA20': '看多' if current_price > latest['MA20'] else '看空',
    'MA5vsMA20': '看多' if latest['MA5'] > latest['MA20'] else '看空',
    'RSI': '超买' if latest['RSI'] > 70 else '超卖' if latest['RSI'] < 30 else '中性',
    'MACD': '看多' if latest['MACD'] > latest['Signal'] else '看空',
    '布林带': '上轨附近' if current_price > bb_upper * 0.98 else '下轨附近' if current_price < bb_lower * 1.02 else '中轨',
    '成交量': '放量' if latest['Volume'] > latest['Volume_MA20'] * 1.2 else '缩量'
}

print(f"\n  --- 当前技术指标 ({df.index[-1].strftime('%Y-%m-%d')}) ---")
print(f"  收盘价:     ${current_price:.2f}")
print(f"  MA5:        ${latest['MA5']:.2f}  [{signals['价格vsMA5']}]")
print(f"  MA20:       ${latest['MA20']:.2f}  [{signals['价格vsMA20']}]")
print(f"  MA50:       ${latest['MA50']:.2f}")
print(f"  MA200:      ${latest['MA200']:.2f}")
print(f"  RSI(14):    {latest['RSI']:.1f}  [{signals['RSI']}]")
print(f"  MACD:       {latest['MACD']:.3f}  [{signals['MACD']}]")
print(f"  布林带:     ${bb_lower:.2f} - ${bb_middle:.2f} - ${bb_upper:.2f}  [{signals['布林带']}]")
print(f"  ATR(14):    ${latest['ATR']:.2f} (日均波幅)")
print(f"  成交量:     {latest['Volume']:,.0f}  [{signals['成交量']}]")

# 多空评分
print("\n[5/5] 多空评分与预测...")

bull_score = 0
bear_score = 0

# 趋势评分
if current_price > latest['MA5']: bull_score += 1
else: bear_score += 1

if current_price > latest['MA20']: bull_score += 1
else: bear_score += 1

if latest['MA5'] > latest['MA20']: bull_score += 1
else: bear_score += 1

if current_price > latest['MA50']: bull_score += 1
else: bear_score += 1

# 动量评分
if latest['RSI'] > 50 and latest['RSI'] < 70: bull_score += 1
elif latest['RSI'] < 50: bear_score += 1
elif latest['RSI'] > 70: bear_score += 1  # 超买转空

if latest['MACD'] > latest['Signal']: bull_score += 1
else: bear_score += 1

if latest['Histogram'] > 0 and latest['Histogram'] > prev['Histogram']: bull_score += 1
elif latest['Histogram'] < 0: bear_score += 1

# 成交量评分
if signals['成交量'] == '放量' and current_price > prev['Close']: bull_score += 1
elif signals['成交量'] == '放量' and current_price < prev['Close']: bear_score += 1

# 布林带评分
if current_price > bb_middle: bull_score += 1
else: bear_score += 1

total_signals = bull_score + bear_score
bull_pct = bull_score / total_signals * 100 if total_signals > 0 else 50

print(f"\n  --- 多空力量对比 ---")
print(f"  多头因子: {bull_score}/{total_signals} ({bull_pct:.0f}%)")
print(f"  空头因子: {bear_score}/{total_signals} ({100-bull_pct:.0f}%)")

# 短期预测
print(f"\n  --- 短期走势预测 (1-5天) ---")

# 基于ATR计算目标价
atr = latest['ATR']

if bull_pct >= 60:
    trend = "偏多震荡"
    target_up = current_price + atr * 2
    target_down = current_price - atr * 1
elif bull_pct <= 40:
    trend = "偏空震荡"
    target_up = current_price + atr * 1
    target_down = current_price - atr * 2
else:
    trend = "横盘震荡"
    target_up = current_price + atr * 1.5
    target_down = current_price - atr * 1.5

# 找到最近的支撑和阻力
nearest_support = None
nearest_resistance = None

for name, price, note in supports:
    if price < current_price * 0.98:
        nearest_support = (name, price)
        break

for name, price, note in resistances:
    if price > current_price * 1.02:
        nearest_resistance = (name, price)
        break

print(f"  趋势判断: {trend}")
print(f"  上方目标: ${target_up:.2f} (+{(target_up/current_price-1)*100:.1f}%)")
print(f"  下方目标: ${target_down:.2f} ({(target_down/current_price-1)*100:.1f}%)")

if nearest_resistance:
    print(f"  关键阻力: {nearest_resistance[0]} ${nearest_resistance[1]:.2f}")
if nearest_support:
    print(f"  关键支撑: {nearest_support[0]} ${nearest_support[1]:.2f}")

# 操作建议
print("\n" + "="*70)
print("   操作建议")
print("="*70)

if bull_pct >= 70:
    action = "逢低做多"
    stop_loss = nearest_support[1] if nearest_support else current_price - atr * 2
    take_profit = nearest_resistance[1] if nearest_resistance else current_price + atr * 3
elif bull_pct <= 30:
    action = "逢高做空/观望"
    stop_loss = nearest_resistance[1] if nearest_resistance else current_price + atr * 2
    take_profit = nearest_support[1] if nearest_support else current_price - atr * 3
else:
    action = "区间操作/观望"
    stop_loss = current_price - atr * 2
    take_profit = current_price + atr * 2

print(f"\n  操作建议: {action}")
print(f"  入场区间: ${current_price - atr:.2f} - ${current_price + atr:.2f}")
print(f"  止损位:   ${stop_loss:.2f} ({(stop_loss/current_price-1)*100:.1f}%)")
print(f"  目标位:   ${take_profit:.2f} ({(take_profit/current_price-1)*100:.1f}%)")
print(f"  风险收益比: {abs(take_profit-current_price)/abs(stop_loss-current_price):.1f}:1")

print("\n" + "="*70)
print("   分析完成!")
print("="*70)

# 保存数据
df.to_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\SMCI_analysis.csv')
print(f"\n详细数据已保存: SMCI_analysis.csv")
