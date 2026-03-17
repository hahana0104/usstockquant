import pandas as pd
import numpy as np

# 读取分析结果
df = pd.read_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\SMCI_analysis.csv', index_col=0, parse_dates=True)
latest = df.iloc[-1]
current_price = latest['Close']

print("="*70)
print("   SMCI (Super Micro Computer) 技术分析报告")
print("="*70)

print("\n【1. 基本信息】")
print(f"  分析区间: 2024-03-18 至 2026-03-16")
print(f"  交易日数: 500天")
print(f"  当前价格: ${current_price:.2f}")

# 近期高低点
recent_60d = df.tail(60)
recent_high = recent_60d['High'].max()
recent_low = recent_60d['Low'].min()
recent_high_date = recent_60d['High'].idxmax()
recent_low_date = recent_60d['Low'].idxmin()

# Ensure dates are datetime objects
if isinstance(recent_high_date, str):
    recent_high_date = pd.to_datetime(recent_high_date)
if isinstance(recent_low_date, str):
    recent_low_date = pd.to_datetime(recent_low_date)

print(f"  60日高点: ${recent_high:.2f} ({recent_high_date.strftime('%Y-%m-%d')})")
print(f"  60日低点: ${recent_low:.2f} ({recent_low_date.strftime('%Y-%m-%d')})")

print("\n【2. 支撑位 (Support Levels)】")
print(f"  {'级别':<15} {'价格':>10} {'距离':>8} {'说明':<20}")
print("  " + "-"*60)

# 计算斐波那契回撤
diff = recent_high - recent_low
fib_618 = recent_high - diff * 0.618
fib_786 = recent_high - diff * 0.786
fib_100 = recent_low

supports = [
    ('MA50', latest['MA50'], '中期支撑'),
    ('斐波那契61.8%', fib_618, '强支撑'),
    ('布林带下轨', latest['BB_Lower'], '20日标准差'),
    ('斐波那契78.6%', fib_786, '强支撑'),
    ('近期低点', recent_low, pd.to_datetime(recent_low_date).strftime('%Y-%m-%d')),
]

for name, price, note in supports:
    if not np.isnan(price) and price < current_price:
        dist = (current_price - price) / current_price * 100
        print(f"  {name:<15} ${price:>9.2f} -{dist:>6.1f}%  {note}")

print("\n【3. 压力位 (Resistance Levels)】")
print(f"  {'级别':<15} {'价格':>10} {'距离':>8} {'说明':<20}")
print("  " + "-"*60)

fib_50 = recent_high - diff * 0.5
fib_382 = recent_high - diff * 0.382
fib_236 = recent_high - diff * 0.236

resistances = [
    ('MA5', latest['MA5'], '短期压力'),
    ('斐波那契50%', fib_50, '心理关口'),
    ('MA10', latest['MA10'], '短期压力'),
    ('MA20', latest['MA20'], '中期压力'),
    ('斐波那契38.2%', fib_382, '回调阻力'),
    ('布林带上轨', latest['BB_Upper'], '20日标准差'),
    ('近期高点', recent_high, pd.to_datetime(recent_high_date).strftime('%Y-%m-%d')),
]

for name, price, note in resistances:
    if not np.isnan(price) and price > current_price:
        dist = (price - current_price) / current_price * 100
        print(f"  {name:<15} ${price:>9.2f} +{dist:>6.1f}%  {note}")

print("\n【4. 当前技术指标】")
print(f"  收盘价:     ${current_price:.2f}")
print(f"  MA5:        ${latest['MA5']:.2f}  [{'上方' if current_price > latest['MA5'] else '下方'}]")
print(f"  MA20:       ${latest['MA20']:.2f}  [{'上方' if current_price > latest['MA20'] else '下方'}]")
print(f"  MA50:       ${latest['MA50']:.2f}  [{'上方' if current_price > latest['MA50'] else '下方'}]")
print(f"  MA200:      ${latest['MA200']:.2f}  [{'上方' if current_price > latest['MA200'] else '下方'}]")
print(f"  RSI(14):    {latest['RSI']:.1f}  [{'超买' if latest['RSI'] > 70 else '超卖' if latest['RSI'] < 30 else '中性'}]")
print(f"  MACD:       {latest['MACD']:.3f}  [{'多头' if latest['MACD'] > latest['Signal'] else '空头'}]")
print(f"  布林带:     ${latest['BB_Lower']:.2f} - ${latest['BB_Middle']:.2f} - ${latest['BB_Upper']:.2f}")
print(f"  ATR(14):    ${latest['ATR']:.2f} (日均波幅${latest['ATR']:.2f})")

print("\n【5. 多空评分】")

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
if 50 < latest['RSI'] < 70: bull_score += 1
elif latest['RSI'] < 50: bear_score += 1
elif latest['RSI'] > 70: bear_score += 1

if latest['MACD'] > latest['Signal']: bull_score += 1
else: bear_score += 1

# 布林带
if current_price > latest['BB_Middle']: bull_score += 1
else: bear_score += 1

total = bull_score + bear_score
bull_pct = bull_score / total * 100

print(f"  多头因子: {bull_score}/{total} ({bull_pct:.0f}%)")
print(f"  空头因子: {bear_score}/{total} ({100-bull_pct:.0f}%)")

print("\n【6. 短期走势预测 (1-5天)】")

atr = latest['ATR']

if bull_pct >= 60:
    trend = "偏多震荡"
    up_target = current_price + atr * 2
    down_target = current_price - atr * 1
elif bull_pct <= 40:
    trend = "偏空震荡"
    up_target = current_price + atr * 1
    down_target = current_price - atr * 2
else:
    trend = "横盘震荡"
    up_target = current_price + atr * 1.5
    down_target = current_price - atr * 1.5

print(f"  趋势判断: {trend}")
print(f"  上方目标: ${up_target:.2f} (+{(up_target/current_price-1)*100:.1f}%)")
print(f"  下方目标: ${down_target:.2f} ({(down_target/current_price-1)*100:.1f}%)")
print(f"  关键阻力: 斐波那契38.2% ${fib_382:.2f}")
print(f"  关键支撑: 斐波那契61.8% ${fib_618:.2f}")

print("\n【7. 操作建议】")

if bull_pct >= 60:
    action = "逢低做多"
    stop_loss = fib_618
    take_profit = fib_382
elif bull_pct <= 40:
    action = "逢高做空/观望"
    stop_loss = fib_382
    take_profit = fib_618
else:
    action = "区间操作/观望"
    stop_loss = current_price - atr * 2
    take_profit = current_price + atr * 2

print(f"  建议操作: {action}")
print(f"  入场区间: ${current_price - atr:.2f} - ${current_price + atr:.2f}")
print(f"  止损位:   ${stop_loss:.2f}")
print(f"  目标位:   ${take_profit:.2f}")

print("\n【8. 关键位总结】")
print(f"  最强阻力: 近期高点 ${recent_high:.2f}")
print(f"  关键阻力: 斐波那契38.2% ${fib_382:.2f}")
print(f"  当前价格: ${current_price:.2f}")
print(f"  关键支撑: 斐波那契61.8% ${fib_618:.2f}")
print(f"  最强支撑: 近期低点 ${recent_low:.2f}")

print("\n" + "="*70)
