"""
策略模块 - 支持多种策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}
    
    @abstractmethod
    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号
        
        Returns:
            DataFrame with columns: signal (1=buy, -1=sell, 0=hold)
        """
        pass
    
    @abstractmethod
    def get_params_config(self) -> Dict:
        """获取参数配置说明"""
        pass


class ThreeFactorStrategy(BaseStrategy):
    """三因子策略 (Quality + Value + Momentum)"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'quality_weight': 0.4,
            'value_weight': 0.3,
            'momentum_weight': 0.3,
            'num_positions': 20,
            'rebalance_freq': 'ME'
        }
        default_params.update(params or {})
        super().__init__("三因子策略 (QVM)", default_params)
    
    def generate_signals(self, price_data: pd.DataFrame, 
                        fundamentals: pd.DataFrame = None,
                        rebalance_dates: List = None) -> pd.DataFrame:
        """生成三因子信号"""
        pass
    
    def get_params_config(self) -> Dict:
        """返回参数配置"""
        return {
            'quality_weight': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.4, 'label': '质量因子权重'},
            'value_weight': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.3, 'label': '价值因子权重'},
            'momentum_weight': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.3, 'label': '动量因子权重'},
            'num_positions': {'type': 'int', 'min': 5, 'max': 50, 'default': 20, 'label': '持仓数量'},
        }


class MAStrategy(BaseStrategy):
    """均线策略 (MA Crossover)"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'fast_period': 20,
            'slow_period': 50,
            'ticker': None  # 单股票策略
        }
        default_params.update(params or {})
        super().__init__("均线交叉策略 (MA)", default_params)
    
    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """生成MA交叉信号"""
        df = price_data.copy()
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        
        if 'Close' in df.columns:
            df['MA_fast'] = df['Close'].rolling(fast).mean()
            df['MA_slow'] = df['Close'].rolling(slow).mean()
            
            # 金叉买入，死叉卖出
            df['signal'] = 0
            df.loc[df['MA_fast'] > df['MA_slow'], 'signal'] = 1
            df.loc[df['MA_fast'] <= df['MA_slow'], 'signal'] = 0
            
            # 产生交易信号的位置
            df['position'] = df['signal'].shift(1).fillna(0)
        
        return df
    
    def get_params_config(self) -> Dict:
        return {
            'fast_period': {'type': 'int', 'min': 5, 'max': 60, 'default': 20, 'label': '短期均线'},
            'slow_period': {'type': 'int', 'min': 20, 'max': 200, 'default': 50, 'label': '长期均线'},
        }


class RSIStrategy(BaseStrategy):
    """RSI策略 (超买超卖)"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'period': 14,
            'oversold': 30,
            'overbought': 70,
        }
        default_params.update(params or {})
        super().__init__("RSI策略", default_params)
    
    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """生成RSI信号"""
        df = price_data.copy()
        period = self.params['period']
        oversold = self.params['oversold']
        overbought = self.params['overbought']
        
        if 'Close' in df.columns:
            # 计算RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # RSI < 30 买入, RSI > 70 卖出
            df['signal'] = 0
            df.loc[df['RSI'] < oversold, 'signal'] = 1
            df.loc[df['RSI'] > overbought, 'signal'] = 0
            df['position'] = df['signal'].fillna(method='ffill').fillna(0)
        
        return df
    
    def get_params_config(self) -> Dict:
        return {
            'period': {'type': 'int', 'min': 5, 'max': 30, 'default': 14, 'label': 'RSI周期'},
            'oversold': {'type': 'int', 'min': 10, 'max': 40, 'default': 30, 'label': '超卖阈值'},
            'overbought': {'type': 'int', 'min': 60, 'max': 90, 'default': 70, 'label': '超买阈值'},
        }


class MACDStrategy(BaseStrategy):
    """MACD策略 (金叉死叉)"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'fast': 12,
            'slow': 26,
            'signal': 9,
        }
        default_params.update(params or {})
        super().__init__("MACD策略", default_params)
    
    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """生成MACD信号"""
        df = price_data.copy()
        fast = self.params['fast']
        slow = self.params['slow']
        signal_period = self.params['signal']
        
        if 'Close' in df.columns:
            exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
            exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
            
            # MACD上穿信号线买入，下穿卖出
            df['signal'] = 0
            df.loc[df['MACD'] > df['Signal'], 'signal'] = 1
            df['position'] = df['signal'].shift(1).fillna(0)
        
        return df
    
    def get_params_config(self) -> Dict:
        return {
            'fast': {'type': 'int', 'min': 5, 'max': 20, 'default': 12, 'label': '快线周期'},
            'slow': {'type': 'int', 'min': 20, 'max': 50, 'default': 26, 'label': '慢线周期'},
            'signal': {'type': 'int', 'min': 5, 'max': 15, 'default': 9, 'label': '信号线周期'},
        }


class BollingerStrategy(BaseStrategy):
    """布林带策略"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'period': 20,
            'std_dev': 2,
        }
        default_params.update(params or {})
        super().__init__("布林带策略", default_params)
    
    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """生成布林带信号"""
        df = price_data.copy()
        period = self.params['period']
        std_dev = self.params['std_dev']
        
        if 'Close' in df.columns:
            df['MA'] = df['Close'].rolling(period).mean()
            df['STD'] = df['Close'].rolling(period).std()
            df['Upper'] = df['MA'] + (df['STD'] * std_dev)
            df['Lower'] = df['MA'] - (df['STD'] * std_dev)
            
            # 触及下轨买入，触及上轨卖出
            df['signal'] = 0
            df.loc[df['Close'] < df['Lower'], 'signal'] = 1  # 超卖买入
            df.loc[df['Close'] > df['Upper'], 'signal'] = 0  # 超买卖出
            df['position'] = df['signal'].fillna(method='ffill').fillna(0)
        
        return df
    
    def get_params_config(self) -> Dict:
        return {
            'period': {'type': 'int', 'min': 10, 'max': 50, 'default': 20, 'label': '周期'},
            'std_dev': {'type': 'float', 'min': 1, 'max': 3, 'default': 2, 'label': '标准差倍数'},
        }


# 策略注册表
STRATEGY_REGISTRY = {
    'three_factor': ThreeFactorStrategy,
    'ma_cross': MAStrategy,
    'rsi': RSIStrategy,
    'macd': MACDStrategy,
    'bollinger': BollingerStrategy,
}

def get_strategy(name: str, params: Dict = None) -> BaseStrategy:
    """获取策略实例"""
    if name in STRATEGY_REGISTRY:
        return STRATEGY_REGISTRY[name](params)
    raise ValueError(f"Unknown strategy: {name}")

def get_strategy_list() -> List[Dict]:
    """获取策略列表"""
    return [
        {'id': 'three_factor', 'name': '三因子策略 (QVM)', 'desc': '质量+价值+动量'},
        {'id': 'ma_cross', 'name': '均线交叉策略', 'desc': 'MA金叉买入，死叉卖出'},
        {'id': 'rsi', 'name': 'RSI策略', 'desc': '超卖买入，超买卖出'},
        {'id': 'macd', 'name': 'MACD策略', 'desc': 'MACD金叉买入，死叉卖出'},
        {'id': 'bollinger', 'name': '布林带策略', 'desc': '触及下轨买入，上轨卖出'},
    ]
