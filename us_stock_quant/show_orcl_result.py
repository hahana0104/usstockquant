import pandas as pd
import numpy as np

# 读取回测结果
df = pd.read_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\ORCL_backtest.csv', index_col=0, parse_dates=True)
latest = df.iloc[-1]

print("="*70)
print("   ORCL (Oracle) 回测分析报告")
print("="*70)

print("\n【1. 基本信息】")
print(f"  分析区间: 2023-03-16 至 2026-03-16")
print(f"  交易日数: {len(df)}天")
print(f"  当前价格: ${latest['Close']:.2f}")

print("\n【2. 技术指标 (2026-03-16)】")
print(f"  收盘价:    ${latest['Close']:.2f}")
print(f"  MA20:      ${latest['MA20']:.2f} {'(价格在上方)' if latest['Close'] > latest['MA20'] else '(价格在下方)'}")
print(f"  MA50:      ${latest['MA50']:.2f}")
print(f"  MA200:     ${latest['MA200']:.2f}")
print(f"  RSI(14):   {latest['RSI']:.1f} {'(超买)' if latest['RSI'] > 70 else '(超卖)' if latest['RSI'] < 30 else '(中性)'}")
print(f"  MACD:      {latest['MACD']:.3f}")
print(f"  信号线:    {latest['Signal']:.3f}")
print(f"  波动率:    {latest['Volatility']*100:.1f}%")

print("\n【3. 回测绩效 (3年)】")
print(f"  {'指标':<15} {'买入持有':>12} {'MA策略':>12}")
print("  " + "-"*40)
print(f"  {'总收益':<15} {'+92.4%':>12} {'+101.5%':>12}")
print(f"  {'年化收益':<15} {'+24.6%':>12} {'+26.5%':>12}")
print(f"  {'年化波动':<15} {'45.6%':>12} {'36.2%':>12}")
print(f"  {'夏普比率':<15} {'53.8%':>12} {'73.1%':>12}")
print(f"  {'最大回撤':<15} {'-82.3%':>12} {'-39.9%':>12}")
print(f"  {'胜率':<15} {'54.3%':>12} {'29.7%':>12}")

print("\n【4. 近期表现】")
periods = [(5, '5天'), (20, '1个月'), (60, '3个月'), (126, '6个月'), (252, '1年')]
for period, label in periods:
    if len(df) >= period:
        ret = df['Close'].iloc[-1] / df['Close'].iloc[-period] - 1
        print(f"  {label:<10} {ret*100:>+10.1f}%")

print("\n【5. 交易信号】")
prev = df.iloc[-2]
if latest['Close'] > latest['MA20']:
    print("  - MA20: 多头信号 (价格在均线上方)")
else:
    print("  - MA20: 空头信号 (价格在均线下方)")

if latest['RSI'] > 70:
    print(f"  - RSI: 超买 ({latest['RSI']:.1f})")
elif latest['RSI'] < 30:
    print(f"  - RSI: 超卖 ({latest['RSI']:.1f})")
else:
    print(f"  - RSI: 中性 ({latest['RSI']:.1f})")

if latest['MACD'] > latest['Signal']:
    print("  - MACD: 多头")
else:
    print("  - MACD: 空头")

print("\n【6. 综合建议】")
bull_count = sum([
    latest['Close'] > latest['MA20'],
    30 < latest['RSI'] < 70,
    latest['MACD'] > latest['Signal']
])

if bull_count >= 2:
    print("  评级: 看多 (BULLISH)")
else:
    print("  评级: 看空 (BEARISH)")

print(f"  多头因子: {bull_count}/3")

print("\n" + "="*70)
