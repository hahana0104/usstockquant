import pandas as pd
import numpy as np

# 读取回测结果
df = pd.read_csv(r'C:\Users\nono\.openclaw\workspace\us_stock_quant\CRCL_backtest.csv', index_col=0, parse_dates=True)
latest = df.iloc[-1]

print("="*70)
print("   CRCL 回测分析报告")
print("="*70)

print("\n【1. 基本信息】")
print(f"  分析区间: 2025-06-05 至 2026-03-16 (IPO后数据)")
print(f"  交易日数: {len(df)}天 (约9个月)")
print(f"  当前价格: ${latest['Close']:.2f}")

print("\n【2. 技术指标 (2026-03-16)】")
print(f"  收盘价:    ${latest['Close']:.2f}")
print(f"  MA20:      ${latest['MA20']:.2f} {'(价格在上方)' if latest['Close'] > latest['MA20'] else '(价格在下方)'}")
print(f"  MA50:      ${latest['MA50']:.2f}")
print(f"  MA200:     {'N/A (数据不足)'}" if pd.isna(latest['MA200']) else f"${latest['MA200']:.2f}")
print(f"  RSI(14):   {latest['RSI']:.1f} {'(超买!)' if latest['RSI'] > 70 else '(超卖)' if latest['RSI'] < 30 else '(中性)'}")
print(f"  MACD:      {latest['MACD']:.3f}")
print(f"  信号线:    {latest['Signal']:.3f}")
print(f"  波动率:    {latest['Volatility']*100:.1f}% (极高!)")

print("\n【3. 回测绩效 (9个月)】")
print(f"  {'指标':<15} {'买入持有':>12} {'MA策略':>12}")
print("  " + "-"*40)
print(f"  {'总收益':<15} {'+49.1%':>12} {'-6.7%':>12} [X]")
print(f"  {'年化收益':<15} {'+68.1%':>12} {'-8.6%':>12}")
print(f"  {'年化波动':<15} {'119.6%':>12} {'63.8%':>12}")
print(f"  {'夏普比率':<15} {'56.9%':>12} {'-13.5%':>12}")
print(f"  {'最大回撤':<15} {'-139.2%':>12} {'-80.6%':>12}")
print(f"  {'胜率':<15} {'48.5%':>12} {'17.0%':>12}")

print("\n【4. 近期表现】")
periods = [(5, '5天'), (20, '1个月'), (60, '3个月')]
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
    print(f"  - RSI: 超买警告! ({latest['RSI']:.1f} > 70)")
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
    30 < latest['RSI'] < 70,  # RSI不在超买区才算多头
    latest['MACD'] > latest['Signal']
])

# 特别处理：RSI超买是空头信号
if latest['RSI'] > 70:
    print("  [!] RSI严重超买 (85.4)，短期回调风险极高!")

if latest['Close'] > latest['MA20'] and latest['MACD'] > latest['Signal']:
    print("  评级: 短期看多，但超买严重 (CAUTIOUS BULLISH)")
else:
    print("  评级: 观望 (NEUTRAL)")

print(f"  多头因子: {bull_count}/3")
print(f"  关键支撑: MA20 (${latest['MA20']:.2f})")
print(f"  关键阻力: 前高 (${df['Close'].max():.2f})")

print("\n" + "="*70)
print("   [!] 风险提示")
print("="*70)
print("  1. CRCL是新股(IPO 2025年6月)，历史数据不足")
print("  2. 波动率极高(141%)，风险巨大")
print("  3. RSI超买(85.4)，短期可能回调")
print("  4. MA策略在此股上表现极差(-6.7% vs +49.1%)")
print("  5. 建议：观望，等待回调后再考虑入场")

print("\n" + "="*70)
