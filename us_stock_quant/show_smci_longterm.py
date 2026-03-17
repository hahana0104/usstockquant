import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\SMCI_longterm.csv', index_col=0, parse_dates=True)

# 删除NaN值
df = df.dropna(subset=['Close'])

if len(df) == 0:
    print("没有有效数据")
    exit()

latest = df.iloc[-1]
current_price = latest['Close']

print("="*70)
print("   SMCI 中长期走势分析报告")
print("="*70)

print("\n【1. 基本信息】")
print(f"  上市日期: 2007-03-29")
print(f"  分析区间: 2007-03-29 至 2026-03-16")
print(f"  历史长度: {len(df)}天 ({len(df)/252:.1f}年)")
print(f"  当前价格: ${current_price:.2f}")

# 历史高低点
all_time_high = df['High'].max()
all_time_low = df['Low'].min()
ath_date = pd.to_datetime(df['High'].idxmax())
atl_date = pd.to_datetime(df['Low'].idxmin())
year_high = df.tail(252)['High'].max()
year_low = df.tail(252)['Low'].min()

print(f"\n  历史最高价: ${all_time_high:.2f} ({ath_date.strftime('%Y-%m-%d')})")
print(f"  历史最低价: ${all_time_low:.2f} ({atl_date.strftime('%Y-%m-%d')})")
print(f"  年度最高价: ${year_high:.2f}")
print(f"  年度最低价: ${year_low:.2f}")
print(f"  从高点回撤: {(current_price/all_time_high-1)*100:.1f}%")
print(f"  从低点涨幅: {(current_price/all_time_low-1)*100:.1f}%")

# 计算长期均线
df['MA50'] = df['Close'].rolling(window=50).mean()
df['MA100'] = df['Close'].rolling(window=100).mean()
df['MA200'] = df['Close'].rolling(window=200).mean()

latest = df.iloc[-1]

print("\n【2. 长期趋势状态】")

# 年线判断
if current_price > latest['MA200']:
    print(f"  年线(MA200): ${latest['MA200']:.2f}  [价格在上方 - 牛市格局]")
    trend_200 = "BULL"
else:
    print(f"  年线(MA200): ${latest['MA200']:.2f}  [价格在下方 - 熊市格局]")
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

# 大周期斐波那契
price_range = all_time_high - all_time_low
fib_0 = all_time_high
fib_236 = all_time_high - price_range * 0.236
fib_382 = all_time_high - price_range * 0.382
fib_50 = all_time_high - price_range * 0.5
fib_618 = all_time_high - price_range * 0.618
fib_786 = all_time_high - price_range * 0.786
fib_100 = all_time_low

print("\n【3. 长期支撑压力位】")

print("\n  === 长期支撑位 ===")
supports = [
    ('年线MA200', latest['MA200']),
    ('年度低点', year_low),
    ('斐波那契61.8%', fib_618),
    ('斐波那契78.6%', fib_786),
    ('历史最低点', all_time_low),
]

for name, price in supports:
    if not np.isnan(price) and price < current_price:
        dist = (current_price - price) / current_price * 100
        print(f"  {name:<15} ${price:>10.2f}  (-{dist:>5.1f}%)")

print("\n  === 长期压力位 ===")
resistances = [
    ('斐波那契38.2%', fib_382),
    ('斐波那契23.6%', fib_236),
    ('年度高点', year_high),
    ('历史最高点', all_time_high),
]

for name, price in resistances:
    if price > current_price:
        dist = (price - current_price) / current_price * 100
        print(f"  {name:<15} ${price:>10.2f}  (+{dist:>5.1f}%)")

# 阶段涨跌幅
print("\n【4. 阶段涨跌幅】")
ret_1m = df['Close'].iloc[-1] / df['Close'].iloc[-21] - 1 if len(df) > 21 else 0
ret_3m = df['Close'].iloc[-1] / df['Close'].iloc[-63] - 1 if len(df) > 63 else 0
ret_6m = df['Close'].iloc[-1] / df['Close'].iloc[-126] - 1 if len(df) > 126 else 0
ret_1y = df['Close'].iloc[-1] / df['Close'].iloc[-252] - 1 if len(df) > 252 else 0
ret_3y = df['Close'].iloc[-1] / df['Close'].iloc[-756] - 1 if len(df) > 756 else 0

print(f"  近1个月: {ret_1m*100:+.1f}%")
print(f"  近3个月: {ret_3m*100:+.1f}%")
print(f"  近6个月: {ret_6m*100:+.1f}%")
print(f"  近1年:   {ret_1y*100:+.1f}%")
print(f"  近3年:   {ret_3y*100:+.1f}%")

# 位置评估
position = (current_price - all_time_low) / (all_time_high - all_time_low)

print("\n【5. 位置评估】")
print(f"  当前在历史区间位置: {position*100:.1f}%")

if position > 0.7:
    print("  评估: 高位区域 (>70%) - 风险大于机会")
elif position < 0.3:
    print("  评估: 低位区域 (<30%) - 机会大于风险")
else:
    print("  评估: 中位区域 (30%-70%) - 等待方向")

# 中长期多空评分
print("\n【6. 中长期多空评分】")

bull_score = 0
bear_score = 0

if trend_200 == "BULL": bull_score += 2
else: bear_score += 2

if trend_100 == "BULL": bull_score += 1
else: bear_score += 1

if trend_50 == "BULL": bull_score += 1
else: bear_score += 1

if ret_1y > 0: bull_score += 1
else: bear_score += 1

if position < 0.5: bull_score += 1
else: bear_score += 1

total = bull_score + bear_score
bull_pct = bull_score / total * 100

print(f"  多头因子: {bull_score}/{total} ({bull_pct:.0f}%)")
print(f"  空头因子: {bear_score}/{total} ({100-bull_pct:.0f}%)")

# 中长期目标
print("\n【7. 中长期目标价 (6-12个月)】")

if bull_pct >= 60:
    trend_view = "牛市延续"
    target_up = fib_236
    target_down = fib_618
elif bull_pct <= 40:
    trend_view = "熊市延续"
    target_up = fib_50
    target_down = fib_786
else:
    trend_view = "震荡筑底"
    target_up = fib_382
    target_down = fib_618

print(f"  趋势判断: {trend_view}")
print(f"  乐观目标: ${target_up:.2f} ({(target_up/current_price-1)*100:+.1f}%)")
print(f"  中性目标: ${fib_50:.2f} ({(fib_50/current_price-1)*100:+.1f}%)")
print(f"  悲观目标: ${target_down:.2f} ({(target_down/current_price-1)*100:+.1f}%)")

# 投资建议
print("\n" + "="*70)
print("   中长期投资建议")
print("="*70)

if bull_pct >= 60:
    advice = "长期持有/逢低加仓"
    entry = f"${fib_50:.2f}以下"
    stop = f"${fib_618:.2f}"
    target = f"${fib_236:.2f}"
elif bull_pct <= 40:
    advice = "逢高减仓/观望等待"
    entry = "观望"
    stop = f"${fib_50:.2f}"
    target = f"${fib_786:.2f}"
else:
    advice = "区间内高抛低吸"
    entry = f"${fib_618:.2f}-${fib_50:.2f}区间"
    stop = f"${fib_786:.2f}"
    target = f"${fib_382:.2f}"

print(f"\n  投资策略: {advice}")
print(f"  建议入场: {entry}")
print(f"  止损位:   {stop}")
print(f"  目标位:   {target}")

print(f"\n  关键观察点:")
print(f"  1. 年线 {latest['MA200']:.2f} 是多空分水岭")
print(f"  2. 斐波那契50%位 {fib_50:.2f} 是核心关口")
print(f"  3. 从高点已回撤 {(current_price/all_time_high-1)*100:.1f}%，估值是否合理")

print("\n" + "="*70)
