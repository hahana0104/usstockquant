import yfinance as yf
import pandas as pd
from datetime import datetime

print("="*60)
print("   持仓监控")
print("   " + datetime.now().strftime('%Y-%m-%d %H:%M'))
print("="*60)

# 你的持仓
positions = [
    {'ticker': 'NVDL', 'shares': 20, 'cost': 36.0},
    {'ticker': 'ACN', 'shares': 13, 'cost': 196.79},
    {'ticker': 'NVDA', 'shares': 10, 'cost': 164.0},
    {'ticker': 'SMCI', 'shares': 20, 'cost': 35.0},
]

total_value = 0
total_cost = 0

print(f"\n{'股票':<8} {'持仓':>6} {'成本':>10} {'现价':>10} {'市值':>12} {'盈亏':>10}")
print("-"*60)

for pos in positions:
    try:
        ticker = yf.Ticker(pos['ticker'])
        data = ticker.history(period='1d')
        current_price = data['Close'].iloc[-1]
        
        market_value = pos['shares'] * current_price
        cost_value = pos['shares'] * pos['cost']
        pnl = market_value - cost_value
        pnl_pct = (current_price / pos['cost'] - 1) * 100
        
        total_value += market_value
        total_cost += cost_value
        
        pnl_str = f"+${pnl:.0f}" if pnl >= 0 else f"-${abs(pnl):.0f}"
        
        print(f"{pos['ticker']:<8} {pos['shares']:>6} ${pos['cost']:>9.2f} ${current_price:>9.2f} ${market_value:>10.0f} {pnl_str:>9} ({pnl_pct:+.1f}%)")
    except Exception as e:
        print(f"{pos['ticker']:<8} 获取失败")

total_pnl = total_value - total_cost
print("-"*60)
print(f"{'合计':<8} {'':>6} {'':>10} {'':>10} ${total_value:>10.0f} {'+$'+str(int(total_pnl)) if total_pnl > 0 else '-$'+str(int(abs(total_pnl))):>9}")

print("\n" + "="*60)
