"""
美股三因子量化策略 - 完整整合版
Quality + Value + Momentum
一键运行，无需额外依赖检查
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============ 配置 ============
CONFIG = {
    'start_date': '2015-01-01',
    'end_date': '2026-03-09',
    'initial_capital': 100000,
    'commission': 0.001,
    'slippage': 0.001,
    'num_positions': 20,
    'rebalance_freq': 'ME',  # ME=月末
    'quality_weight': 0.4,
    'value_weight': 0.3,
    'momentum_weight': 0.3,
    'benchmark': 'SPY'
}

TICKERS = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'UNH', 'JPM',
    'V', 'JNJ', 'XOM', 'WMT', 'MA', 'PG', 'HD', 'CVX', 'MRK', 'LLY',
    'ABBV', 'PEP', 'KO', 'COST', 'TMO', 'ABT', 'MCD', 'ACN', 'WFC', 'DHR'
]

# ============ 数据获取 ============
class DataLoader:
    def __init__(self):
        self.cache = {}
    
    def download_prices(self, tickers, start, end):
        """下载价格数据"""
        print(f"下载 {len(tickers)} 只股票数据...")
        all_data = []
        
        for i, ticker in enumerate(tickers):
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(start=start, end=end, auto_adjust=True)
                if len(df) > 0:
                    df['Ticker'] = ticker
                    df.reset_index(inplace=True)
                    # 统一时区处理
                    if hasattr(df['Date'].dtype, 'tz') and df['Date'].dtype.tz is not None:
                        df['Date'] = df['Date'].dt.tz_localize(None)
                    all_data.append(df)
                if (i + 1) % 10 == 0:
                    print(f"  已下载 {i+1}/{len(tickers)}")
            except Exception as e:
                print(f"  {ticker} 下载失败: {e}")
        
        if not all_data:
            raise ValueError("没有下载到任何数据")
        
        combined = pd.concat(all_data, ignore_index=True)
        combined.set_index(['Date', 'Ticker'], inplace=True)
        print(f"✓ 成功获取 {len(all_data)} 只股票")
        return combined
    
    def download_fundamentals(self, tickers):
        """下载基本面数据"""
        print(f"获取 {len(tickers)} 只股票基本面数据...")
        data = []
        
        for i, ticker in enumerate(tickers):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                data.append({
                    'Ticker': ticker,
                    'ROE': info.get('returnOnEquity'),
                    'PE': info.get('trailingPE') or info.get('forwardPE'),
                    'MarketCap': info.get('marketCap'),
                    'Sector': info.get('sector'),
                    'RevenueGrowth': info.get('revenueGrowth'),
                })
                if (i + 1) % 10 == 0:
                    print(f"  已获取 {i+1}/{len(tickers)}")
            except:
                pass
        
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('Ticker', inplace=True)
        print(f"✓ 成功获取 {len(df)} 只股票基本面")
        return df

# ============ 因子计算 ============
class FactorModel:
    def __init__(self, config):
        self.config = config
    
    def calc_quality(self, fundamentals):
        """质量因子: ROE"""
        roe = fundamentals.get('ROE', pd.Series())
        score = pd.Series(0.5, index=roe.index)
        
        # ROE越高越好，负值设为0
        valid_roe = roe[roe > 0].dropna()
        if len(valid_roe) > 0:
            ranks = valid_roe.rank(pct=True)
            score.update(ranks)
        
        score[roe <= 0] = 0
        return score
    
    def calc_value(self, fundamentals):
        """价值因子: PE越低越好"""
        pe = fundamentals.get('PE', pd.Series())
        score = pd.Series(0.5, index=pe.index)
        
        # PE越低越好，负值设为0
        valid_pe = pe[pe > 0].dropna()
        valid_pe = valid_pe[valid_pe < 100]  # 过滤极端值
        
        if len(valid_pe) > 0:
            # 越低排名越高
            ranks = valid_pe.rank(pct=True, ascending=False)
            score.update(ranks)
        
        score[pe <= 0] = 0
        return score
    
    def calc_momentum(self, price_data, current_date):
        """动量因子: 126天(6个月)收益"""
        prices = price_data['Close'].unstack(level='Ticker')
        
        # 获取当前日期之前的数据
        valid_prices = prices[prices.index <= current_date]
        if len(valid_prices) < 130:
            return pd.Series(0.5, index=prices.columns)
        
        # 计算126天收益
        past_price = valid_prices.iloc[-130]
        current_price = valid_prices.iloc[-1]
        momentum = (current_price - past_price) / past_price
        
        # 收益越高越好
        score = momentum.rank(pct=True).fillna(0.5)
        score[momentum < 0] = score[momentum < 0] * 0.5  # 负收益惩罚
        
        return score
    
    def combine(self, quality, value, momentum):
        """合成三因子"""
        common = quality.index.intersection(value.index).intersection(momentum.index)
        
        combined = (
            self.config['quality_weight'] * quality.reindex(common, fill_value=0.5) +
            self.config['value_weight'] * value.reindex(common, fill_value=0.5) +
            self.config['momentum_weight'] * momentum.reindex(common, fill_value=0.5)
        )
        
        return combined.sort_values(ascending=False)
    
    def select_stocks(self, combined_score, n=20):
        """选股"""
        return combined_score.head(n).index.tolist()

# ============ 回测引擎 ============
class Backtester:
    def __init__(self, config):
        self.config = config
        self.initial_capital = config['initial_capital']
        self.commission = config['commission']
        self.slippage = config['slippage']
    
    def run(self, prices_df, signals_df, rebalance_dates):
        """运行回测"""
        print("\n开始回测...")
        
        # 展开价格数据
        prices = prices_df['Close'].unstack(level='Ticker')
        prices.index = pd.to_datetime(prices.index).tz_localize(None)
        
        # 确保信号索引也是无时区的datetime
        signals_df.index = pd.to_datetime(signals_df.index).tz_localize(None)
        
        capital = self.initial_capital
        positions = {}  # {ticker: shares}
        equity_curve = []
        
        all_dates = prices.index
        
        for date in all_dates:
            # 计算当前市值
            portfolio_value = capital
            for ticker, shares in list(positions.items()):
                if ticker in prices.columns and pd.notna(prices.loc[date, ticker]):
                    portfolio_value += shares * prices.loc[date, ticker]
            
            # 记录
            equity_curve.append({
                'Date': date,
                'Equity': portfolio_value,
                'Cash': capital,
                'Positions': len(positions)
            })
            
            # 检查是否调仓日
            date_normalized = pd.Timestamp(date).normalize()
            is_rebalance = any(abs((d - date_normalized).days) <= 1 for d in rebalance_dates)
            
            if is_rebalance and date_normalized in signals_df.index:
                signal = signals_df.loc[date_normalized]
                signal = signal[signal > 0]
                
                if len(signal) == 0:
                    continue
                
                # 卖出所有
                for ticker in list(positions.keys()):
                    if ticker in prices.columns and pd.notna(prices.loc[date, ticker]):
                        price = prices.loc[date, ticker] * (1 - self.slippage)
                        capital += positions[ticker] * price * (1 - self.commission)
                    del positions[ticker]
                
                # 买入新持仓（等权）
                weight = 1.0 / len(signal)
                for ticker in signal.index:
                    if ticker in prices.columns and pd.notna(prices.loc[date, ticker]):
                        price = prices.loc[date, ticker] * (1 + self.slippage)
                        target_value = portfolio_value * weight
                        shares = int(target_value / price)
                        
                        if shares > 0 and capital >= shares * price * (1 + self.commission):
                            cost = shares * price * (1 + self.commission)
                            capital -= cost
                            positions[ticker] = shares
        
        # 最终价值
        final_value = capital
        if len(all_dates) > 0:
            last_date = all_dates[-1]
            for ticker, shares in positions.items():
                if ticker in prices.columns and pd.notna(prices.loc[last_date, ticker]):
                    final_value += shares * prices.loc[last_date, ticker]
        
        self.equity_curve = pd.DataFrame(equity_curve)
        self.final_value = final_value
        
        return self.equity_curve, final_value
    
    def report(self):
        """生成报告"""
        if len(self.equity_curve) == 0:
            return "无数据"
        
        equity = self.equity_curve['Equity']
        returns = equity.pct_change().dropna()
        
        total_return = (self.final_value / self.initial_capital - 1) * 100
        n_years = len(equity) / 252
        annual_return = ((1 + total_return/100) ** (1/n_years) - 1) * 100 if n_years > 0 else 0
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe = (annual_return - 2) / volatility if volatility > 0 else 0
        
        cummax = equity.cummax()
        max_dd = ((equity - cummax) / cummax).min() * 100
        
        report = f"""
{'='*50}
        回测绩效报告
{'='*50}
初始资金:     ${self.initial_capital:,.0f}
最终权益:     ${self.final_value:,.0f}
总收益率:     {total_return:.2f}%
年化收益:     {annual_return:.2f}%
年化波动:     {volatility:.2f}%
最大回撤:     {max_dd:.2f}%
夏普比率:     {sharpe:.2f}
交易天数:     {len(equity)}
{'='*50}
"""
        return report
    
    def plot(self, save_path=None):
        """绘图"""
        import matplotlib.pyplot as plt
        
        if len(self.equity_curve) == 0:
            print("无数据绘图")
            return
        
        df = self.equity_curve.set_index('Date')
        equity = df['Equity']
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 9))
        
        # 权益曲线
        ax1 = axes[0]
        ax1.plot(equity.index, equity.values / self.initial_capital, linewidth=1)
        ax1.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
        ax1.set_title('Equity Curve')
        ax1.set_ylabel('Normalized')
        ax1.grid(True, alpha=0.3)
        
        # 回撤
        ax2 = axes[1]
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100
        ax2.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.4)
        ax2.set_title('Drawdown (%)')
        ax2.set_ylabel('%')
        ax2.grid(True, alpha=0.3)
        
        # 持仓
        ax3 = axes[2]
        ax3.plot(df.index, df['Positions'], linewidth=1, color='green')
        ax3.set_title('Number of Positions')
        ax3.set_ylabel('Count')
        ax3.set_xlabel('Date')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"图表保存: {save_path}")
        
        plt.show()

# ============ 主程序 ============
def main():
    print("="*50)
    print("   美股三因子量化策略")
    print("   Quality + Value + Momentum")
    print("="*50)
    
    # 1. 下载数据
    loader = DataLoader()
    price_data = loader.download_prices(TICKERS, CONFIG['start_date'], CONFIG['end_date'])
    fundamentals = loader.download_fundamentals(TICKERS)
    
    # 2. 计算因子并生成信号
    print("\n计算三因子信号...")
    model = FactorModel(CONFIG)
    
    # 生成调仓日期
    rebalance_dates = pd.date_range(
        start=CONFIG['start_date'], 
        end=CONFIG['end_date'], 
        freq=CONFIG['rebalance_freq']
    )
    print(f"调仓次数: {len(rebalance_dates)}")
    
    # 预计算基本面因子（不随时间变化）
    quality_score = model.calc_quality(fundamentals)
    value_score = model.calc_value(fundamentals)
    
    # 为每个调仓日计算信号
    all_signals = []
    
    for i, date in enumerate(rebalance_dates):
        if i % 12 == 0:
            print(f"  处理 {date.strftime('%Y-%m')} ({i+1}/{len(rebalance_dates)})")
        
        try:
            momentum_score = model.calc_momentum(price_data, date)
            combined = model.combine(quality_score, value_score, momentum_score)
            selected = model.select_stocks(combined, CONFIG['num_positions'])
            
            # 等权信号
            weight = 1.0 / len(selected)
            signal = pd.Series(weight, index=selected)
            signal.name = date
            all_signals.append(signal)
        except:
            pass
    
    # 构建信号矩阵
    all_tickers = set()
    for s in all_signals:
        all_tickers.update(s.index)
    
    signal_data = []
    for s in all_signals:
        row = pd.Series(0.0, index=all_tickers, dtype=float)
        row[s.index] = s.values
        signal_data.append(row)
    
    signal_df = pd.DataFrame(signal_data, index=[s.name for s in all_signals])
    print(f"信号矩阵: {signal_df.shape}")
    
    # 3. 回测
    backtester = Backtester(CONFIG)
    equity_curve, final_value = backtester.run(price_data, signal_df, rebalance_dates)
    
    # 4. 输出结果
    print(backtester.report())
    
    # 保存结果
    equity_curve.to_csv('equity_curve.csv', index=False)
    print("\n权益曲线已保存: equity_curve.csv")
    
    # 绘图
    try:
        backtester.plot(save_path='backtest_result.png')
    except Exception as e:
        print(f"绘图失败: {e}")
    
    print("\n✓ 完成!")

if __name__ == '__main__':
    main()
