"""
美股三因子量化策略配置
Quality + Value + Momentum
"""

# ========== 数据配置 ==========
DATA_CONFIG = {
    'start_date': '2015-01-01',  # 回测开始时间
    'end_date': '2026-03-09',    # 回测结束时间
    'benchmark': 'SPY',          # 基准：标普500 ETF
    'universe': 'sp500',         # 股票池：sp500 / nasdaq100 / custom
    'min_price': 5,              # 最小股价（过滤低价股）
    'min_volume': 1000000,       # 最小日均成交量
}

# ========== 因子配置 ==========
FACTOR_CONFIG = {
    # Quality 因子权重
    'quality_weight': 0.4,
    'roe_threshold': 0.15,       # ROE > 15%
    'roe_lookback': 3,           # 看过去3年平均ROE
    
    # Value 因子权重
    'value_weight': 0.3,
    'pe_percentile': 0.5,        # PE < 行业中位数
    
    # Momentum 因子权重
    'momentum_weight': 0.3,
    'momentum_lookback': 126,    # 6个月（约126个交易日）
    'momentum_top_pct': 0.3,     # 取前30%
}

# ========== 策略配置 ==========
STRATEGY_CONFIG = {
    'rebalance_freq': 'ME',      # 调仓频率：ME=月末, W=周, QE=季末
    'rebalance_day': 1,          # 每月第1个交易日
    'num_positions': 20,         # 持仓数量
    'position_sizing': 'equal',  # 仓位分配：equal=等权, mktcap=市值加权
    'max_sector_pct': 0.25,      # 单一行业最大25%
    'stop_loss': 0.15,           # 止损15%
    'take_profit': 0.30,         # 止盈30%
}

# ========== 回测配置 ==========
BACKTEST_CONFIG = {
    'initial_capital': 100000,   # 初始资金10万美元
    'commission': 0.001,         # 手续费0.1%
    'slippage': 0.001,           # 滑点0.1%
    'borrow_rate': 0.02,         # 融券费率（如做空）
}

# S&P 500 成分股（扩展至100只）
SP500_TICKERS = [
    # 科技巨头 (10)
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'AVGO', 'ORCL',
    # 金融 (10)
    'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'SPGI', 'GS', 'MS', 'C',
    # 医疗健康 (10)
    'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY',
    # 消费 (10)
    'WMT', 'PG', 'COST', 'KO', 'PEP', 'MCD', 'HD', 'NKE', 'DIS', 'LOW',
    # 能源 (6)
    'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY',
    # 工业 (8)
    'UPS', 'HON', 'RTX', 'CAT', 'GE', 'BA', 'LMT', 'DE',
    # 通信 (6)
    'VZ', 'T', 'CMCSA', 'TMUS', 'NFLX', 'VZ',
    # 科技硬件/半导体 (10)
    'TXN', 'QCOM', 'ADBE', 'AMD', 'INTC', 'CRM', 'ACN', 'IBM', 'NOW', 'INTU',
    # 其他消费 (8)
    'PM', 'MO', 'EL', 'TJX', 'SBUX', 'BKNG', 'TGT', 'DG',
    # 公用事业/材料 (12)
    'NEE', 'LIN', 'APD', 'SHW', 'FCX', 'NEM', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE',
    # 汽车/交通 (6)
    'F', 'GM', 'UBER', 'LYFT', 'CSX', 'UNP',
    # 其他 (4)
    'AMGN', 'GILD', 'AMT', 'PLD'
]

# 行业分类（用于行业分散）
SECTOR_MAP = {
    'AAPL': 'Technology', 'MSFT': 'Technology', 'AMZN': 'Consumer Discretionary',
    'NVDA': 'Technology', 'GOOGL': 'Communication Services', 'META': 'Communication Services',
    'GOOG': 'Communication Services', 'TSLA': 'Consumer Discretionary', 'UNH': 'Health Care',
    'JPM': 'Financials', 'V': 'Financials', 'JNJ': 'Health Care', 'XOM': 'Energy',
    'WMT': 'Consumer Staples', 'AVGO': 'Technology', 'MA': 'Financials', 'PG': 'Consumer Staples',
    'HD': 'Consumer Discretionary', 'CVX': 'Energy', 'MRK': 'Health Care', 'LLY': 'Health Care',
    'ABBV': 'Health Care', 'PEP': 'Consumer Staples', 'KO': 'Consumer Staples',
    'COST': 'Consumer Staples', 'TMO': 'Health Care', 'ABT': 'Health Care',
    'MCD': 'Consumer Discretionary', 'ACN': 'Technology', 'WFC': 'Financials',
    'DHR': 'Health Care', 'DIS': 'Communication Services', 'LIN': 'Materials',
    'VZ': 'Communication Services', 'TXN': 'Technology', 'ADBE': 'Technology',
    'PM': 'Consumer Staples', 'NEE': 'Utilities', 'BMY': 'Health Care',
    'RTX': 'Industrials', 'HON': 'Industrials', 'QCOM': 'Technology',
    'SPGI': 'Financials', 'LOW': 'Consumer Discretionary', 'UPS': 'Industrials',
    'NKE': 'Consumer Discretionary', 'ORCL': 'Technology', 'UNP': 'Industrials',
    'AMGN': 'Health Care'
}
