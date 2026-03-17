"""
快速测试脚本 - 使用模拟数据验证系统
无需下载真实数据即可测试回测逻辑
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backtest.engine import VectorizedBacktester
from config import BACKTEST_CONFIG


def generate_mock_data(n_stocks=10, n_days=500, start_date='2020-01-01'):
    """
    生成模拟股票数据
    
    Returns:
        price_data: MultiIndex DataFrame (Date, Ticker)
    """
    np.random.seed(42)
    
    dates = pd.date_range(start=start_date, periods=n_days, freq='B')  # 工作日
    tickers = [f'STOCK{i:02d}' for i in range(n_stocks)]
    
    data = []
    for ticker in tickers:
        # 生成随机游走价格
        returns = np.random.normal(0.0005, 0.02, n_days)  # 平均日收益0.05%，波动2%
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'Date': dates,
            'Ticker': ticker,
            'Open': prices * (1 + np.random.normal(0, 0.001, n_days)),
            'High': prices * (1 + abs(np.random.normal(0, 0.01, n_days))),
            'Low': prices * (1 - abs(np.random.normal(0, 0.01, n_days))),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, n_days)
        })
        data.append(df)
    
    combined = pd.concat(data, ignore_index=True)
    combined.set_index(['Date', 'Ticker'], inplace=True)
    
    return combined


def generate_mock_signals(price_data, rebalance_dates, n_positions=5):
    """
    生成随机交易信号（用于测试）
    """
    tickers = price_data.index.get_level_values(1).unique()
    
    signals = []
    for date in rebalance_dates:
        # 随机选n只股票
        selected = np.random.choice(tickers, size=min(n_positions, len(tickers)), replace=False)
        weight = 1.0 / len(selected)
        signal = pd.Series(weight, index=selected)
        signal.name = date
        signals.append(signal)
    
    signal_df = pd.DataFrame(signals).T
    signal_df.columns = rebalance_dates
    return signal_df.T


def quick_test():
    """快速测试回测引擎"""
    print("="*60)
    print("   快速测试 - 模拟数据回测")
    print("="*60)
    print()
    
    # 生成模拟数据
    print("生成模拟数据...")
    price_data = generate_mock_data(n_stocks=20, n_days=500)
    print(f"  股票数量: 20")
    print(f"  交易日数: 500")
    print(f"  数据形状: {price_data.shape}")
    
    # 生成调仓日期（每月）
    dates = price_data.index.get_level_values(0).unique()
    rebalance_dates = dates[::21].tolist()[:20]  # 约每月调仓，共20次
    print(f"  调仓次数: {len(rebalance_dates)}")
    
    # 生成信号
    print("\n生成随机交易信号...")
    signal_df = generate_mock_signals(price_data, rebalance_dates, n_positions=5)
    
    # 运行回测
    print("\n运行回测...")
    backtester = VectorizedBacktester(BACKTEST_CONFIG)
    
    results = backtester.run(
        price_data=price_data,
        signal_df=signal_df,
        rebalance_dates=rebalance_dates,
        position_sizing='equal'
    )
    
    # 输出结果
    print("\n" + backtester.generate_report())
    
    # 绘制图表
    try:
        backtester.plot_results(save_path=r'C:\Users\nono\.openclaw\workspace\us_stock_quant\mock_test_result.png')
    except Exception as e:
        print(f"图表生成失败（可能缺少GUI）: {e}")
    
    print("\n✓ 快速测试完成！")
    print("  如果以上结果正常，说明回测引擎工作正常")
    print("  可以运行 main.py 进行真实数据回测")
    
    return results


if __name__ == '__main__':
    quick_test()
