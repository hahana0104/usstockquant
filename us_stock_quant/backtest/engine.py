"""
向量化回测引擎 - 修复版
快速回测多因子策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class VectorizedBacktester:
    """向量化回测引擎"""
    
    def __init__(self, config: Dict):
        self.initial_capital = config.get('initial_capital', 100000)
        self.commission = config.get('commission', 0.001)
        self.slippage = config.get('slippage', 0.001)
        self.equity_curve = []
        self.trades = []
        
    def run(self, price_data: pd.DataFrame,
            signal_df: pd.DataFrame,
            rebalance_dates: List[pd.Timestamp],
            position_sizing: str = 'equal') -> Dict:
        """运行回测"""
        print("开始回测...")
        
        # 准备价格数据 - 使用调整后收盘价
        prices = price_data['Close'].unstack(level='Ticker')
        
        # 统一索引格式 - 去掉时区，只保留日期
        prices.index = pd.to_datetime(prices.index).tz_localize(None)
        signal_df.index = pd.to_datetime(signal_df.index).tz_localize(None)
        rebalance_dates = [pd.to_datetime(d).tz_localize(None) if hasattr(d, 'tz_localize') else pd.to_datetime(d) for d in rebalance_dates]
        
        # 初始化
        capital = self.initial_capital
        current_positions = {}  # {ticker: shares}
        equity_curve = []
        trades = []
        
        all_dates = prices.index
        
        for i, date in enumerate(all_dates):
            # 计算当日持仓市值
            portfolio_value = capital
            for ticker, shares in list(current_positions.items()):
                if ticker in prices.columns and pd.notna(prices.loc[date, ticker]):
                    portfolio_value += shares * prices.loc[date, ticker]
                else:
                    # 价格缺失，保持前值
                    pass
            
            # 记录权益曲线
            equity_curve.append({
                'Date': date,
                'Equity': portfolio_value,
                'Cash': capital,
                'Positions': len(current_positions)
            })
            
            # 检查是否调仓日
            is_rebalance = date in rebalance_dates
            has_signal = date in signal_df.index
            
            if is_rebalance and has_signal:
                # 获取当日信号
                signals = signal_df.loc[date].dropna()
                if len(signals) == 0:
                    continue
                    
                target_tickers = signals.index.tolist()
                target_weights = signals.values
                
                # 归一化权重
                target_weights = target_weights / target_weights.sum()
                
                # 先全部卖出当前持仓
                for ticker in list(current_positions.keys()):
                    if ticker in prices.columns and pd.notna(prices.loc[date, ticker]):
                        price = prices.loc[date, ticker] * (1 - self.slippage)
                        shares = current_positions[ticker]
                        proceeds = shares * price * (1 - self.commission)
                        capital += proceeds
                        
                        trades.append({
                            'Date': date,
                            'Ticker': ticker,
                            'Action': 'SELL',
                            'Shares': shares,
                            'Price': price,
                            'Proceeds': proceeds
                        })
                        
                        del current_positions[ticker]
                
                # 按目标权重买入新持仓
                for ticker, weight in zip(target_tickers, target_weights):
                    if ticker not in prices.columns or pd.isna(prices.loc[date, ticker]):
                        continue
                    
                    price = prices.loc[date, ticker] * (1 + self.slippage)
                    target_value = portfolio_value * weight
                    
                    if capital >= target_value * (1 + self.commission) and price > 0:
                        shares_to_buy = int(target_value / price)
                        
                        if shares_to_buy > 0:
                            cost = shares_to_buy * price * (1 + self.commission)
                            
                            if capital >= cost:
                                capital -= cost
                                current_positions[ticker] = shares_to_buy
                                
                                trades.append({
                                    'Date': date,
                                    'Ticker': ticker,
                                    'Action': 'BUY',
                                    'Shares': shares_to_buy,
                                    'Price': price,
                                    'Cost': cost
                                })
        
        # 计算最终价值
        final_value = capital
        last_date = all_dates[-1] if len(all_dates) > 0 else None
        if last_date:
            for ticker, shares in current_positions.items():
                if ticker in prices.columns and pd.notna(prices.loc[last_date, ticker]):
                    final_value += shares * prices.loc[last_date, ticker]
        
        self.equity_curve = pd.DataFrame(equity_curve)
        self.trades = pd.DataFrame(trades)
        
        # 计算绩效指标
        metrics = self._calculate_metrics()
        
        print(f"✓ 回测完成")
        print(f"  初始资金: ${self.initial_capital:,.0f}")
        print(f"  最终权益: ${final_value:,.0f}")
        print(f"  总收益率: {(final_value/self.initial_capital - 1)*100:.2f}%")
        
        return {
            'equity_curve': self.equity_curve,
            'trades': self.trades,
            'metrics': metrics,
            'final_value': final_value
        }
    
    def _calculate_metrics(self) -> Dict:
        """计算绩效指标"""
        if len(self.equity_curve) == 0:
            return {}
        
        equity = self.equity_curve['Equity']
        returns = equity.pct_change().dropna()
        
        if len(returns) == 0 or equity.iloc[0] == 0:
            return {}
        
        # 总收益
        total_return = (equity.iloc[-1] / self.initial_capital - 1)
        
        # 年化收益
        n_years = len(equity) / 252
        annual_return = (1 + total_return) ** (1/n_years) - 1 if n_years > 0 else 0
        
        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率
        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 卡尔玛比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 胜率
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        
        # 盈亏比
        avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 1
        profit_factor = avg_win / avg_loss if avg_loss != 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'trading_days': len(equity)
        }
    
    def plot_results(self, benchmark: pd.Series = None, save_path: str = None):
        """绘制回测结果"""
        if len(self.equity_curve) == 0:
            print("没有数据可以绘图")
            return
            
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 准备数据 - 统一时间戳格式，去除时区
        equity_df = self.equity_curve.copy()
        equity_df['Date'] = pd.to_datetime(equity_df['Date']).dt.tz_localize(None)
        equity_df = equity_df.set_index('Date')
        equity = equity_df['Equity']
        
        # 1. 权益曲线
        ax1 = axes[0]
        normalized = equity / self.initial_capital
        ax1.plot(normalized.index, normalized.values, label='Strategy', linewidth=1.5, color='blue')
        
        if benchmark is not None:
            # 统一 benchmark 时间戳格式
            benchmark_copy = benchmark.copy()
            benchmark_copy.index = pd.to_datetime(benchmark_copy.index).tz_localize(None)
            bench_aligned = benchmark_copy.reindex(equity.index, method='ffill')
            if len(bench_aligned) > 0 and bench_aligned.iloc[0] != 0:
                bench_normalized = bench_aligned / bench_aligned.iloc[0]
                ax1.plot(bench_aligned.index, bench_normalized.values, 
                        label='Benchmark (SPY)', linewidth=1.5, alpha=0.7, color='orange')
        
        ax1.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
        ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Normalized Value')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 2. 回撤
        ax2 = axes[1]
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100
        ax2.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.4)
        ax2.plot(drawdown.index, drawdown.values, color='darkred', linewidth=1)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_title('Drawdown (%)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Drawdown %')
        ax2.grid(True, alpha=0.3)
        
        # 3. 持仓数量
        ax3 = axes[2]
        positions = equity_df['Positions']
        ax3.step(positions.index, positions.values, color='green', linewidth=1.5, where='post')
        ax3.set_title('Number of Positions', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Positions')
        ax3.set_xlabel('Date')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        
        plt.show()
    
    def generate_report(self) -> str:
        """生成文字报告"""
        metrics = self._calculate_metrics()
        
        if not metrics:
            return "无法生成报告：没有回测数据"
        
        report = f"""
{'='*60}
           回测绩效报告
{'='*60}

基本参数:
  初始资金:    ${self.initial_capital:>15,.0f}
  手续费率:    {self.commission*100:>15.2f}%
  滑点:        {self.slippage*100:>15.2f}%

收益指标:
  总收益率:    {metrics.get('total_return', 0)*100:>15.2f}%
  年化收益:    {metrics.get('annual_return', 0)*100:>15.2f}%
  年化波动:    {metrics.get('annual_volatility', 0)*100:>15.2f}%

风险指标:
  最大回撤:    {metrics.get('max_drawdown', 0)*100:>15.2f}%
  夏普比率:    {metrics.get('sharpe_ratio', 0):>15.2f}
  卡尔玛比率:  {metrics.get('calmar_ratio', 0):>15.2f}

交易统计:
  交易天数:    {metrics.get('trading_days', 0):>15,}
  胜率:        {metrics.get('win_rate', 0)*100:>15.2f}%
  盈亏比:      {metrics.get('profit_factor', 0):>15.2f}

{'='*60}
"""
        return report
