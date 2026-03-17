"""
工具函数集合
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import json


def get_sector_performance(price_data: pd.DataFrame, sector_map: Dict) -> pd.DataFrame:
    """
    计算各行业表现
    
    Args:
        price_data: MultiIndex DataFrame with Close prices
        sector_map: {ticker: sector}
    """
    # 展开价格
    prices = price_data['Close'].unstack(level='Ticker')
    
    # 计算各行业等权收益
    sector_returns = {}
    sectors = set(sector_map.values())
    
    for sector in sectors:
        tickers = [t for t, s in sector_map.items() if s == sector and t in prices.columns]
        if tickers:
            sector_prices = prices[tickers]
            sector_return = sector_prices.pct_change().mean(axis=1).cumsum()
            sector_returns[sector] = sector_return
    
    return pd.DataFrame(sector_returns)


def calculate_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """计算收益相关性矩阵"""
    return returns.corr()


def get_drawdown_periods(equity_curve: pd.Series, threshold: float = -0.1) -> pd.DataFrame:
    """
    识别回撤期间
    
    Returns:
        DataFrame with start, end, depth of each drawdown
    """
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax
    
    periods = []
    in_drawdown = False
    start_date = None
    max_drawdown = 0
    
    for date, dd in drawdown.items():
        if dd < 0 and not in_drawdown:
            in_drawdown = True
            start_date = date
            max_drawdown = dd
        elif in_drawdown:
            if dd < max_drawdown:
                max_drawdown = dd
            if dd >= 0:
                # 回撤结束
                periods.append({
                    'Start': start_date,
                    'End': date,
                    'Depth': max_drawdown,
                    'Duration': (date - start_date).days
                })
                in_drawdown = False
                max_drawdown = 0
    
    return pd.DataFrame(periods)


def analyze_factor_returns(price_data: pd.DataFrame, 
                          factor_values: pd.Series,
                          n_quantiles: int = 5) -> pd.DataFrame:
    """
    因子分组收益分析
    
    将股票按因子值分为n组，看每组后续收益
    """
    prices = price_data['Close'].unstack(level='Ticker')
    forward_returns = prices.pct_change(21).shift(-21)  # 21天后收益
    
    # 按因子分位数分组
    quantiles = pd.qcut(factor_values, n_quantiles, labels=False, duplicates='drop')
    
    results = []
    for q in range(n_quantiles):
        tickers_in_q = quantiles[quantiles == q].index
        avg_return = forward_returns[tickers_in_q].mean(axis=1).mean()
        results.append({
            'Quantile': q + 1,
            'AvgForwardReturn': avg_return,
            'NumStocks': len(tickers_in_q)
        })
    
    return pd.DataFrame(results)


def rolling_sharpe(returns: pd.Series, window: int = 63) -> pd.Series:
    """滚动夏普比率"""
    rolling_mean = returns.rolling(window).mean() * 252
    rolling_std = returns.rolling(window).std() * np.sqrt(252)
    return rolling_mean / rolling_std


def save_results(results: Dict, filepath: str):
    """保存回测结果"""
    output = {
        'metrics': results['metrics'],
        'final_value': results['final_value'],
        'config': {
            'initial_capital': results.get('initial_capital'),
            'commission': results.get('commission'),
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"结果已保存: {filepath}")


class RiskMetrics:
    """风险指标计算"""
    
    @staticmethod
    def var(returns: pd.Series, confidence: float = 0.05) -> float:
        """Value at Risk (历史法)"""
        return np.percentile(returns, confidence * 100)
    
    @staticmethod
    def cvar(returns: pd.Series, confidence: float = 0.05) -> float:
        """Conditional VaR (Expected Shortfall)"""
        var = RiskMetrics.var(returns, confidence)
        return returns[returns <= var].mean()
    
    @staticmethod
    def beta(returns: pd.Series, market_returns: pd.Series) -> float:
        """Beta系数"""
        covariance = returns.cov(market_returns)
        market_variance = market_returns.var()
        return covariance / market_variance if market_variance != 0 else 0
    
    @staticmethod
    def alpha(returns: pd.Series, market_returns: pd.Series, risk_free: float = 0.02) -> float:
        """Alpha (年化)"""
        beta = RiskMetrics.beta(returns, market_returns)
        avg_return = returns.mean() * 252
        market_avg = market_returns.mean() * 252
        return avg_return - (risk_free + beta * (market_avg - risk_free))
    
    @staticmethod
    def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """信息比率"""
        active_return = (returns - benchmark_returns).mean() * 252
        tracking_error = (returns - benchmark_returns).std() * np.sqrt(252)
        return active_return / tracking_error if tracking_error != 0 else 0
