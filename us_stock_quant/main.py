"""
美股三因子策略主程序
运行完整回测流程
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from config import DATA_CONFIG, FACTOR_CONFIG, STRATEGY_CONFIG, BACKTEST_CONFIG, SP500_TICKERS
from data.data_loader import DataLoader, FactorData
from strategies.factors import ThreeFactorModel
from backtest.engine import VectorizedBacktester


def get_rebalance_dates(start_date: str, end_date: str, freq: str = 'M', day: int = 1):
    """
    生成调仓日期
    
    Args:
        freq: 'M'=月, 'W'=周, 'Q'=季度
        day: 每月第几个交易日（简化处理为每月第day日）
    """
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # 调整日期（如果是周末，移到下一个周一）
    adjusted_dates = []
    for d in dates:
        if d.dayofweek == 5:  # 周六
            d = d + timedelta(days=2)
        elif d.dayofweek == 6:  # 周日
            d = d + timedelta(days=1)
        adjusted_dates.append(d)
    
    return adjusted_dates


def main():
    """主程序"""
    print("="*60)
    print("   美股三因子量化策略回测系统")
    print("   Quality + Value + Momentum")
    print("="*60)
    print()
    
    # 1. 初始化数据加载器
    print("【1/5】初始化数据加载器...")
    loader = DataLoader(cache_dir=r'C:\Users\nono\.openclaw\workspace\us_stock_quant\data\cache')
    
    # 2. 下载价格数据（使用默认列表）
    print("\n【2/5】下载股票价格数据...")
    tickers = SP500_TICKERS[:30]  # 先用前30只测试，正式运行时去掉[:30]
    
    try:
        price_data = loader.download_prices(
            tickers=tickers,
            start=DATA_CONFIG['start_date'],
            end=DATA_CONFIG['end_date']
        )
    except Exception as e:
        print(f"数据下载失败: {e}")
        print("请检查网络连接或手动下载数据")
        return
    
    # 3. 下载基本面数据
    print("\n【3/5】下载基本面数据...")
    try:
        fundamentals = loader.download_fundamentals(tickers)
    except Exception as e:
        print(f"基本面数据下载失败: {e}")
        fundamentals = pd.DataFrame()
    
    # 4. 计算因子并生成交易信号
    print("\n【4/5】计算三因子并生成交易信号...")
    
    factor_model = ThreeFactorModel(FACTOR_CONFIG)
    
    # 计算质量因子（基本面，不随时间变化或变化慢）
    if not fundamentals.empty:
        quality_score = factor_model.calculate_quality_score(fundamentals, price_data)
        value_score = factor_model.calculate_value_score(fundamentals)
    else:
        print("警告: 基本面数据为空，使用默认得分")
        quality_score = pd.Series(0.5, index=tickers[:len(tickers)])
        value_score = pd.Series(0.5, index=tickers[:len(tickers)])
    
    # 生成调仓日期
    rebalance_dates = get_rebalance_dates(
        DATA_CONFIG['start_date'],
        DATA_CONFIG['end_date'],
        freq=STRATEGY_CONFIG['rebalance_freq'],
        day=STRATEGY_CONFIG['rebalance_day']
    )
    
    print(f"  回测区间: {DATA_CONFIG['start_date']} 至 {DATA_CONFIG['end_date']}")
    print(f"  调仓频率: {STRATEGY_CONFIG['rebalance_freq']} ({len(rebalance_dates)}次)")
    print(f"  持仓数量: {STRATEGY_CONFIG['num_positions']}")
    
    # 为每个调仓日计算动量因子并生成信号
    all_signals = []
    
    for i, date in enumerate(rebalance_dates):
        if i % 6 == 0:  # 每6个月打印一次进度
            print(f"  处理中... {date.strftime('%Y-%m')} ({i+1}/{len(rebalance_dates)})")
        
        try:
            # 计算动量因子（随时间变化）
            momentum_score = factor_model.calculate_momentum_score(
                price_data, date, lookback=FACTOR_CONFIG['momentum_lookback']
            )
            
            # 合成综合得分
            combined_score = factor_model.combine_factors(
                quality_score, value_score, momentum_score
            )
            
            # 选股
            selected = factor_model.select_stocks(
                combined_score,
                fundamentals if not fundamentals.empty else pd.DataFrame(index=combined_score.index),
                n=STRATEGY_CONFIG['num_positions'],
                max_sector_pct=STRATEGY_CONFIG['max_sector_pct']
            )
            
            # 生成等权信号
            if len(selected) > 0:
                weight = 1.0 / len(selected)
                signal = pd.Series(weight, index=selected)
                signal.name = date
                all_signals.append(signal)
                
        except Exception as e:
            print(f"  {date.strftime('%Y-%m')} 处理失败: {str(e)[:50]}")
            continue
    
    if not all_signals:
        print("错误: 没有生成任何交易信号")
        return
    
    # 合并信号 - 构建DataFrame，index=日期，columns=所有出现过的股票
    all_tickers = set()
    for s in all_signals:
        all_tickers.update(s.index)
    
    signal_data = []
    for s in all_signals:
        row = pd.Series(index=all_tickers, dtype=float)
        row[s.index] = s.values
        signal_data.append(row)
    
    signal_df = pd.DataFrame(signal_data, index=[s.name for s in all_signals])
    signal_df.index = pd.to_datetime(signal_df.index)
    signal_df = signal_df.fillna(0)  # 没有信号的股票权重为0
    
    print(f"\n  生成信号矩阵: {signal_df.shape}")
    print(f"  信号日期数量: {len(signal_df)}")
    print(f"  股票数量: {len(signal_df.columns)}")
    print(f"  信号样例（前2行）:\n{signal_df.iloc[:2, :5]}")
    
    # 5. 运行回测
    print("\n【5/5】运行回测...")
    
    backtester = VectorizedBacktester(BACKTEST_CONFIG)
    
    results = backtester.run(
        price_data=price_data,
        signal_df=signal_df,
        rebalance_dates=rebalance_dates,
        position_sizing=STRATEGY_CONFIG['position_sizing']
    )
    
    # 6. 下载基准数据
    print("\n【6/6】下载基准数据...")
    try:
        benchmark = loader.download_benchmark(
            ticker=DATA_CONFIG['benchmark'],
            start=DATA_CONFIG['start_date'],
            end=DATA_CONFIG['end_date']
        )
    except:
        benchmark = None
        print("  基准数据下载失败")
    
    # 7. 输出结果
    print("\n" + "="*60)
    print(results['trades'].head(10).to_string() if not results['trades'].empty else "无交易记录")
    print("\n" + backtester.generate_report())
    
    # 8. 绘制图表
    print("生成图表...")
    try:
        backtester.plot_results(
            benchmark=benchmark,
            save_path=r'C:\Users\nono\.openclaw\workspace\us_stock_quant\backtest_result.png'
        )
    except Exception as e:
        print(f"图表生成失败: {e}")
    
    # 9. 保存结果
    results['equity_curve'].to_csv(
        r'C:\Users\nono\.openclaw\workspace\us_stock_quant\equity_curve.csv', index=False
    )
    results['trades'].to_csv(
        r'C:\Users\nono\.openclaw\workspace\us_stock_quant\trades.csv', index=False
    )
    
    print("\n✓ 回测完成！")
    print("  结果文件:")
    print("  - equity_curve.csv (权益曲线)")
    print("  - trades.csv (交易记录)")
    print("  - backtest_result.png (图表)")
    
    return results


if __name__ == '__main__':
    results = main()
