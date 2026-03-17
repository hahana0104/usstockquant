"""
三因子计算模块
Quality + Value + Momentum
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats


class ThreeFactorModel:
    """
    三因子模型：质量(Quality) + 价值(Value) + 动量(Momentum)
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.quality_weight = config.get('quality_weight', 0.4)
        self.value_weight = config.get('value_weight', 0.3)
        self.momentum_weight = config.get('momentum_weight', 0.3)
        
    def calculate_quality_score(self, fundamentals: pd.DataFrame, 
                               price_data: pd.DataFrame) -> pd.Series:
        """
        计算质量因子得分
        
        指标：
        1. ROE (Return on Equity) - 40%
        2. 利润增长率 - 30%
        3. 财务健康度（债务权益比、流动比率）- 30%
        """
        scores = pd.Series(index=fundamentals.index, dtype=float)
        
        # 1. ROE 得分 (40%)
        roe = fundamentals['ROE']
        roe_score = self._normalize_factor(roe, higher_better=True)
        
        # 过滤ROE为负的股票（质量差）
        roe_score[roe <= 0] = np.nan
        
        # 2. 利润增长率得分 (30%)
        profit_growth = fundamentals.get('RevenueGrowth', pd.Series(index=fundamentals.index))
        profit_score = self._normalize_factor(profit_growth, higher_better=True)
        profit_score[profit_growth <= 0] = np.nan
        
        # 3. 财务健康度得分 (30%)
        # 低债务权益比更好
        debt_equity = fundamentals.get('DebtToEquity', pd.Series(index=fundamentals.index))
        debt_score = self._normalize_factor(debt_equity, higher_better=False)
        
        # 高流动比率更好
        current_ratio = fundamentals.get('CurrentRatio', pd.Series(index=fundamentals.index))
        current_score = self._normalize_factor(current_ratio, higher_better=True)
        
        health_score = (debt_score.fillna(0.5) + current_score.fillna(0.5)) / 2
        
        # 综合质量得分
        quality_score = (
            0.4 * roe_score.fillna(0) +
            0.3 * profit_score.fillna(0.3) +  # 增长数据可能缺失，给予中等分
            0.3 * health_score
        )
        
        # ROE为负的股票，质量得分设为0
        quality_score[roe <= 0] = 0
        
        return quality_score
    
    def calculate_value_score(self, fundamentals: pd.DataFrame) -> pd.Series:
        """
        计算价值因子得分
        
        指标：
        1. PE (市盈率) - 越低越好
        2. 如果有PB数据也纳入
        """
        scores = pd.Series(index=fundamentals.index, dtype=float)
        
        # PE 得分 - 低PE更好，但PE为负（亏损）的股票排除
        pe = fundamentals['PE']
        
        # 过滤极端值和负值
        pe_filtered = pe.copy()
        pe_filtered[pe_filtered <= 0] = np.nan
        pe_filtered[pe_filtered > 100] = 100  # 封顶100倍
        
        # 行业中性化：按行业分组计算分位数
        sectors = fundamentals.get('Sector', pd.Series(index=fundamentals.index, dtype=str))
        
        value_score = pd.Series(index=fundamentals.index, dtype=float)
        
        for sector in sectors.dropna().unique():
            mask = sectors == sector
            sector_pe = pe_filtered[mask]
            
            if len(sector_pe) > 3:
                # 行业内的PE排名，越低分越高
                ranks = sector_pe.rank(pct=True, ascending=True)
                value_score[mask] = ranks
            else:
                # 行业内股票太少，用全局
                value_score[mask] = pe_filtered[mask].rank(pct=True, ascending=True)
        
        # PE为负的股票，价值得分设为0
        value_score[pe <= 0] = 0
        
        return value_score.fillna(0.3)
    
    def calculate_momentum_score(self, price_data: pd.DataFrame, 
                                current_date: pd.Timestamp,
                                lookback: int = 126) -> pd.Series:
        """
        计算动量因子得分
        
        使用过去N天的收益率排名
        同时考虑波动率调整（夏普比率思想）
        """
        # 获取截止到current_date的价格数据
        try:
            prices = price_data.loc[:current_date]
        except:
            # 如果索引不是MultiIndex，重新处理
            if 'Ticker' in price_data.columns:
                prices = price_data.set_index(['Date', 'Ticker'])['Close']
            else:
                prices = price_data['Close']
        
        # 展开为宽表
        if isinstance(prices.index, pd.MultiIndex):
            price_table = prices.unstack(level='Ticker')
        else:
            price_table = prices
        
        # 计算动量（过去lookback天的收益）
        momentum_returns = price_table.pct_change(lookback).iloc[-1]
        
        # 计算波动率（过去63天）
        daily_returns = price_table.pct_change()
        volatility = daily_returns.iloc[-63:].std() * np.sqrt(252)
        
        # 风险调整动量（夏普比率近似）
        adj_momentum = momentum_returns / (volatility + 0.01)  # 加0.01避免除0
        
        # 转换为0-1分数
        momentum_score = self._normalize_factor(adj_momentum, higher_better=True)
        
        # 动量为负的股票，得分降低
        momentum_score[momentum_returns < 0] = momentum_score[momentum_returns < 0] * 0.5
        
        return momentum_score
    
    def combine_factors(self, quality_score: pd.Series,
                       value_score: pd.Series,
                       momentum_score: pd.Series) -> pd.Series:
        """
        合成三因子得分
        """
        # 确保索引一致
        common_index = quality_score.index.intersection(
            value_score.index
        ).intersection(momentum_score.index)
        
        quality = quality_score.reindex(common_index)
        value = value_score.reindex(common_index)
        momentum = momentum_score.reindex(common_index)
        
        # 加权合成
        combined_score = (
            self.quality_weight * quality +
            self.value_weight * value +
            self.momentum_weight * momentum
        )
        
        return combined_score.sort_values(ascending=False)
    
    def select_stocks(self, combined_score: pd.Series,
                     fundamentals: pd.DataFrame,
                     n: int = 20,
                     max_sector_pct: float = 0.25) -> List[str]:
        """
        根据综合得分选股，控制行业集中度
        
        Args:
            combined_score: 综合因子得分
            fundamentals: 基本面数据（包含Sector）
            n: 选股数量
            max_sector_pct: 单一行业最大占比
        """
        selected = []
        sector_counts = {}
        max_per_sector = int(n * max_sector_pct)
        
        sectors = fundamentals.get('Sector', pd.Series(index=fundamentals.index, dtype=str))
        
        for ticker in combined_score.index:
            if len(selected) >= n:
                break
            
            sector = sectors.get(ticker, 'Unknown')
            sector_counts[sector] = sector_counts.get(sector, 0)
            
            if sector_counts[sector] < max_per_sector:
                selected.append(ticker)
                sector_counts[sector] += 1
        
        return selected
    
    def _normalize_factor(self, series: pd.Series, higher_better: bool = True) -> pd.Series:
        """
        将因子值标准化为0-1分位数
        
        Args:
            series: 因子值序列
            higher_better: 是否越高越好
        """
        # 移除NaN
        valid = series.dropna()
        
        if len(valid) == 0:
            return pd.Series(0.5, index=series.index)
        
        # 计算分位数排名
        ranks = valid.rank(pct=True)
        
        if not higher_better:
            ranks = 1 - ranks
        
        # 映射回原索引
        result = pd.Series(index=series.index, dtype=float)
        result[valid.index] = ranks
        
        return result.fillna(0.5)
    
    def get_factor_exposure(self, selected_stocks: List[str],
                           fundamentals: pd.DataFrame,
                           price_data: pd.DataFrame) -> pd.DataFrame:
        """
        获取选中股票的风格因子暴露
        """
        data = []
        
        for ticker in selected_stocks:
            if ticker not in fundamentals.index:
                continue
                
            fund = fundamentals.loc[ticker]
            
            data.append({
                'Ticker': ticker,
                'Sector': fund.get('Sector', 'Unknown'),
                'ROE': fund.get('ROE'),
                'PE': fund.get('PE'),
                'MarketCap': fund.get('MarketCap'),
                'Quality_Score': None,  # 需要重新计算
                'Value_Score': None,
                'Momentum_Score': None,
            })
        
        return pd.DataFrame(data)
