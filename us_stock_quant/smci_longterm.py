#!/usr/bin/env python3
"""
SMCI (Super Micro Computer) 中长期走势分析
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
print("   SMCI (Super Micro Computer) 中长期走势分析")
print("   周期：周线/月线级别")
print("="*70)

# 下载SMCI历史数据 - 获取更多历史
ticker = 'SMCI'
print(f"\n[1/6] 下载 {ticker} 历史数据...")

stock = yf.Ticker(ticker)
df = stock.history(period='max')  # 获取全部历史数据

if df.empty:
    print("数据下载失败!")
    sys.exit(1)

print(f"  数据区间: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
print(f"  数据条数: {len(df)}天 ({len(df)/252:.1f}年)")
print(f"  当前价格: ${df['Close'].iloc[-1]:.2f}")

# 计算长期技术指标
print("\n[2/6] 计算长期技术指标...")

# 长期移动平均线
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA50'] = df['Close'].rolling(window=50).mean()
df['MA100'] = df['Close'].rolling(window=100).mean()
df['MA200'] = df['Close'].rolling(window=200).mean()

# 周线数据（取每周五收盘）
df_weekly = df.resample('W').last()
df_weekly['MA10_W'] = df_weekly['Close'].rolling(window=10).mean()  # 10周 ≈ 50日
df_weekly['MA20_W'] = df_weekly['Close'].rolling(window=20).mean()  # 20周 ≈ 100日
df_weekly['MA52_W'] = df_weekly['Close'].rolling(window=52).mean()  # 52周 ≈ 1年

# 历史高低点
all_time_high = df['High'].max()
all_time_low = df['Low'].min()
ath_date = df['High'].idxmax()
atl_date = df['Low'].idxmin()

# 年度高低点
year_start = df[df.index >= '2025-01-01']
year_high = year_start['High'].max() if not year_start.empty else df.tail(100)['High'].max()
year_low = year_start['Low'].min() if not year_start.empty else df.tail(100)['Low'].min()

# 大周期斐波那契（基于历史高低点）
price_range = all_time_high - all_time_low
fib_levels_long = {
    '0% (ATH)': all_time_high,
    '23.6%': all_time_high - price_range * 0.236,
    '38.2%': all_time_high - price_range * 0.382,
    '50%': all_time_high - price_range * 0.5,
    '61.8%': all_time_high - price_range * 0.618,
    '78.6%': all_time_high - price_range * 0.786,
    '100% (ATL)': all_time_low
}

# 长期RSI
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=50).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=50).mean()
rs = gain / loss
df['RSI_Long'] = 100 - (100 / (1 + rs))

print(f"\n  --- 历史价格数据 ---")
print(f"  历史最高价: ${all_time_high:.2f} ({ath_date.strftime('%Y-%m-%d')})")
print(f"  历史最低价: ${all_time_low:.2f} ({atl_date.strftime('%Y-%m-%d')})")
print(f"  年度最高价: ${year_high:.2f}")
print(f"  年度最低价: ${year_low:.2f}")
print(f"  从高点回撤: {(df['Close'].iloc[-1]/all_time_high-1)*100:.1f}%")
print(f"  从低点涨幅: {(df['Close'].iloc[-1]/all_time_low-1)*100:.1f}%")

# 长期趋势结构分析
print("\n[3/6] 长期趋势结构分析...")

latest = df.iloc[-1]
current_price = latest['Close']

# 趋势判断
print(f"\n  --- 趋势状态 ---")

# 年线判断
if current_price > latest['MA200']:
    print(f"  年线(MA200): ${latest['MA200']:.2f}  [价格在上方 - 长期牛市]")
    trend_200 = "BULL"
else:
    print(f"  年线(MA200): ${latest['MA200']:.2f}  [价格在下方 - 长期熊市]")
    trend_200 = "BEAR"

# 半年线判断
if current_price > latest['MA100']:
    print(f"  半年线(MA100): ${latest['MA100']:.2f}  [价格在上方 - 中期偏多]")
    trend_100 = "BULL"
else:
    print(f"  半年线(MA100): ${latest['MA100']:.2f}  [价格在下方 - 中期偏空]")
    trend_100 = "BEAR"

# 季线判断
if current_price > latest['MA50']:
    print(f"  季线(MA50): ${latest['MA50']:.2f}  [价格在上方 - 短期偏多]")
    trend_50 = "BULL"
else:
    print(f"  季线(MA50): ${latest['MA50']:.2f}  [价格在下方 - 短期偏空]")
    trend_50 = "BEAR"

# 均线排列
ma_bullish = latest['MA20'] > latest['MA50'] > latest['MA100']
ma_bearish = latest['MA20'] < latest['MA50'] < latest['MA100']

if ma_bullish:
    print(f"  均线排列: 多头排列 [ bullish ]")
elif ma_bearish:
    print(f"  均线排列: 空头排列 [ bearish ]")
else:
    print(f"  均线排列: 纠缠排列 [ neutral ]")

# 长期支撑压力位
print("\n[4/6] 长期支撑压力位...")

print(f"\n  === 长期支撑位 ===")
long_supports = []

# 大周期斐波那契
for name, price in fib_levels_long.items():
    if '61.8' in name or '78.6' in name or '100' in name:
        if price < current_price:
            dist = (current_price - price) / current_price * 100
            long_supports.append((name, price, dist))

# 年线
if latest['MA200'] < current_price:
    dist = (current_price - latest['MA200']) / current_price * 100
    long_supports.append(('年线MA200', latest['MA200'], dist))

# 年度低点
if year_low < current_price:
    dist = (current_price - year_low) / current_price * 100
    long_supports.append(('年度低点', year_low, dist))

long_supports = sorted(long_supports, key=lambda x: x[1], reverse=True)

for name, price, dist in long_supports[:6]:
    print(f"  {name:<15} ${price:>10.2f}  (-{dist:>5.1f}%)")

print(f"\n  === 长期压力位 ===")
long_resistances = []

# 大周期斐波那契
for name, price in fib_levels_long.items():
    if '23.6' in name or '38.2' in name or '50' in name or '0%' in name:
        if price > current_price:
            dist = (price - current_price) / current_price * 100
            long_resistances.append((name, price, dist))

# 年线（如果价格在下方）
if latest['MA200'] > current_price:
    dist = (latest['MA200'] - current_price) / current_price * 100
    long_resistances.append(('年线MA200', latest['MA200'], dist))

long_resistances = sorted(long_resistances, key=lambda x: x[1])

for name, price, dist in long_resistances[:6]:
    print(f"  {name:<15} ${price:>10.2f}  (+{dist:>5.1f}%)")

# 形态分析
print("\n[5/6] 形态分析...")

# 计算近期形态
df['Returns_Month'] = df['Close'].pct_change(21)
df['Returns_Quarter'] = df['Close'].pct_change(63)
df['Returns_Year'] = df['Close'].pct_change(252)

latest_returns = {
    '1月': df['Returns_Month'].iloc[-1],
    '3月': df['Returns_Quarter'].iloc[-1],
    '1年': df['Returns_Year'].iloc[-1]
}

print(f"\n  --- 阶段涨跌幅 ---")
for period, ret in latest_returns.items():
    print(f"  近{period}: {ret*100:+.1f}%")

# 波动率分析
volatility_month = df['Close'].pct_change().tail(21).std() * np.sqrt(252) * 100
volatility_year = df['Close'].pct_change().tail(252).std() * np.sqrt(252) * 100

print(f"\n  --- 波动率分析 ---")
print(f"  近1月年化波动: {volatility_month:.1f}%")
print(f"  近1年年化波动: {volatility_year:.1f}%")

# 中长期预测
print("\n[6/6] 中长期走势预测...")

# 综合评分
long_bull_score = 0
long_bear_score = 0

# 趋势评分
if trend_200 == "BULL": long_bull_score += 2
else: long_bear_score += 2

if trend_100 == "BULL": long_bull_score += 1
else: long_bear_score += 1

if trend_50 == "BULL": long_bull_score += 1
else: long_bear_score += 1

# 均线排列
if ma_bullish: long_bull_score += 1
if ma_bearish: long_bear_score += 1

# 阶段涨幅
if latest_returns['1年'] > 0: long_bull_score += 1
else: long_bear_score += 1

# 当前位置（相对于历史区间）
position_in_range = (current_price - all_time_low) / (all_time_high - all_time_low)
if position_in_range > 0.5: long_bear_score += 1  # 高位偏空
else: long_bull_score += 1  # 低位偏多

total_long = long_bull_score + long_bear_score
bull_long_pct = long_bull_score / total_long * 100 if total_long > 0 else 50

print(f"\n  --- 中长期多空评分 ---")
print(f"  多头因子: {long_bull_score}/{total_long} ({bull_long_pct:.0f}%)")
print(f"  空头因子: {long_bear_score}/{total_long} ({100-bull_long_pct:.0f}%)")

# 中长期目标
print(f"\n  --- 中长期目标价 (6-12个月) ---")

# 基于斐波那契的长期目标
if bull_long_pct >= 60:
    long_trend = "牛市延续"
    target_bull = fib_levels_long['23.6%']
    target_bear = fib_levels_long['50%']
elif bull_long_pct <= 40:
    long_trend = "熊市延续"
    target_bull = fib_levels_long['50%']
    target_bear = fib_levels_long['78.6%']
else:
    long_trend = "震荡筑底"
    target_bull = fib_levels_long['38.2%']
    target_bear = fib_levels_long['61.8%']

print(f"  趋势判断: {long_trend}")
print(f"  乐观目标: ${target_bull:.2f} ({(target_bull/current_price-1)*100:+.1f}%)")
print(f"  中性目标: ${fib_levels_long['50%']:.2f} ({(fib_levels_long['50%']/current_price-1)*100:+.1f}%)")
print(f"  悲观目标: ${target_bear:.2f} ({(target_bear/current_price-1)*100:+.1f}%)")

# 时间周期分析
print(f"\n  --- 时间周期分析 ---")
print(f"  当前位置: 历史区间的 {position_in_range*100:.1f}%")

if position_in_range > 0.7:
    print(f"  位置评估: 高位区域，风险大于机会")
elif position_in_range < 0.3:
    print(f"  位置评估: 低位区域，机会大于风险")
else:
    print(f"  位置评估: 中位区域，等待方向选择")

# 最终建议
print("\n" + "="*70)
print("   中长期投资建议")
print("="*70)

if bull_long_pct >= 60:
    advice = "逢低布局"
    entry = f"${fib_levels_long['50%']:.2f} 以下"
    stop = f"${fib_levels_long['61.8%']:.2f}"
    target = f"${fib_levels_long['23.6%']:.2f}"
elif bull_long_pct <= 40:
    advice = "逢高减仓/观望"
    entry = "观望"
    stop = f"${fib_levels_long['50%']:.2f}"
    target = f"${fib_levels_long['78.6%']:.2f}"
else:
    advice = "区间内高抛低吸"
    entry = f"${fib_levels_long['61.8%']:.2f} - ${fib_levels_long['50%']:.2f}"
    stop = f"${fib_levels_long['78.6%']:.2f}"
    target = f"${fib_levels_long['38.2%']:.2f}"

print(f"\n  投资策略: {advice}")
print(f"  建议入场: {entry}")
print(f"  止损位:   {stop}")
print(f"  目标位:   {target}")

print(f"\n  关键观察点:")
if trend_200 == "BEAR":
    print(f"  1. 能否突破年线 ${latest['MA200']:.2f} 是转多关键")
print(f"  2. 斐波那契50%位 ${fib_levels_long['50%']:.2f} 是多空分水岭")
print(f"  3. 年度低点 ${year_low:.2f} 是最后防线")

print("\n" + "="*70)
print("   分析完成!")
print("="*70)

# 保存数据
df.to_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\SMCI_longterm.csv')
print(f"\n详细数据已保存: SMCI_longterm.csv")
