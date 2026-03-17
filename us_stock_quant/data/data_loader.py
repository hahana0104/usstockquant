"""
美股数据获取模块
使用 yfinance 获取免费数据
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import pickle
import os
from datetime import datetime, timedelta


class DataLoader:
    """美股数据加载器"""
    
    def __init__(self, cache_dir: str = './data/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def download_prices(self, tickers: List[str], start: str, end: str, 
                       interval: str = '1d') -> pd.DataFrame:
        """
        下载股票价格和成交量数据
        
        Returns:
            DataFrame with MultiIndex (Date, Ticker)
            Columns: Open, High, Low, Close, Adj Close, Volume
        """
        print(f"正在下载 {len(tickers)} 只股票数据...")
        
        all_data = []
        failed_tickers = []
        
        for i, ticker in enumerate(tickers):
            try:
                # 尝试从缓存加载
                cache_file = os.path.join(self.cache_dir, f"{ticker}_{start}_{end}.pkl")
                
                if os.path.exists(cache_file):
                    df = pd.read_pickle(cache_file)
                else:
                    stock = yf.Ticker(ticker)
                    df = stock.history(start=start, end=end, interval=interval)
                    
                    if len(df) > 0:
                        df.to_pickle(cache_file)
                
                if len(df) > 0:
                    df['Ticker'] = ticker
                    df.reset_index(inplace=True)
                    all_data.append(df)
                    
                if (i + 1) % 10 == 0:
                    print(f"  已处理 {i+1}/{len(tickers)}")
                    
            except Exception as e:
                failed_tickers.append(ticker)
                print(f"  下载失败 {ticker}: {str(e)[:50]}")
        
        if failed_tickers:
            print(f"下载失败的股票: {failed_tickers}")
        
        if not all_data:
            raise ValueError("没有成功下载任何数据")
        
        # 合并数据
        combined = pd.concat(all_data, ignore_index=True)
        
        # 设置索引
        if 'Date' in combined.columns:
            combined['Date'] = pd.to_datetime(combined['Date'])
            combined.set_index(['Date', 'Ticker'], inplace=True)
        elif 'Datetime' in combined.columns:
            combined['Datetime'] = pd.to_datetime(combined['Datetime'])
            combined.set_index(['Datetime', 'Ticker'], inplace=True)
        
        print(f"✓ 成功获取 {len(combined.index.get_level_values(1).unique())} 只股票数据")
        return combined
    
    def download_fundamentals(self, tickers: List[str]) -> pd.DataFrame:
        """
        下载基本面数据（ROE, PE等）
        
        Returns:
            DataFrame with Ticker index
            Columns: ROE, NetIncome, TotalEquity, PE, Sector, MarketCap
        """
        print(f"正在获取 {len(tickers)} 只股票基本面数据...")
        
        fundamentals = []
        
        for i, ticker in enumerate(tickers):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # 获取财务报表
                balance_sheet = stock.balance_sheet
                income_stmt = stock.income_stmt
                
                # 计算ROE = Net Income / Average Shareholder Equity
                roe = None
                if not income_stmt.empty and not balance_sheet.empty:
                    try:
                        net_income = income_stmt.loc['Net Income'].iloc[0] if 'Net Income' in income_stmt.index else None
                        total_equity = balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else None
                        
                        if net_income is not None and total_equity is not None and total_equity != 0:
                            roe = net_income / total_equity
                    except:
                        pass
                
                # 直接使用报告的ROE
                if roe is None:
                    roe = info.get('returnOnEquity')
                
                fund_data = {
                    'Ticker': ticker,
                    'ROE': roe,
                    'PE': info.get('trailingPE') or info.get('forwardPE'),
                    'MarketCap': info.get('marketCap'),
                    'Sector': info.get('sector'),
                    'Industry': info.get('industry'),
                    'RevenueGrowth': info.get('revenueGrowth'),
                    'ProfitMargin': info.get('profitMargins'),
                    'DebtToEquity': info.get('debtToEquity'),
                    'CurrentRatio': info.get('currentRatio'),
                    'DividendYield': info.get('dividendYield'),
                }
                
                fundamentals.append(fund_data)
                
                if (i + 1) % 10 == 0:
                    print(f"  已获取 {i+1}/{len(tickers)}")
                    
            except Exception as e:
                print(f"  获取失败 {ticker}: {str(e)[:50]}")
        
        df = pd.DataFrame(fundamentals)
        if not df.empty:
            df.set_index('Ticker', inplace=True)
        
        print(f"✓ 成功获取 {len(df)} 只股票基本面数据")
        return df
    
    def download_benchmark(self, ticker: str = 'SPY', start: str = None, end: str = None) -> pd.Series:
        """下载基准数据"""
        try:
            bench = yf.download(ticker, start=start, end=end, progress=False)
            return bench['Adj Close']
        except:
            # 备选：使用 yf.Ticker
            t = yf.Ticker(ticker)
            hist = t.history(start=start, end=end)
            return hist['Close'] if 'Close' in hist.columns else hist['Adj Close']
    
    def get_sp500_list(self) -> List[str]:
        """获取S&P 500成分股列表（使用维基百科）"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            df = tables[0]
            return df['Symbol'].tolist()
        except:
            print("无法获取S&P 500列表，使用默认列表")
            from config import SP500_TICKERS
            return SP500_TICKERS
    
    def get_nasdaq100_list(self) -> List[str]:
        """获取NASDAQ 100成分股列表"""
        try:
            url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
            tables = pd.read_html(url)
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    return table[col].tolist()
            raise ValueError("未找到股票代码列")
        except:
            # 默认NASDAQ 100列表
            return ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'AVGO', 'PEP',
                   'COST', 'CSCO', 'TMUS', 'ADBE', 'TXN', 'CMCSA', 'NFLX', 'QCOM', 'HON', 'AMGN',
                   'INTU', 'SBUX', 'INTC', 'AMD', 'MDLZ', 'GILD', 'ADI', 'BKNG', 'AMAT', 'ADP',
                   'VRTX', 'PANW', 'ISRG', 'REGN', 'LRCX', 'MU', 'SNPS', 'KLAC', 'CDNS', 'CSX',
                   'MAR', 'PYPL', 'ASML', 'ORLY', 'CTAS', 'NXPI', 'MELI', 'ABNB', 'MRVL', 'FTNT']


class FactorData:
    """因子数据计算"""
    
    @staticmethod
    def calculate_momentum(price_data: pd.DataFrame, lookback: int = 126) -> pd.DataFrame:
        """
        计算动量因子
        
        Args:
            price_data: MultiIndex DataFrame (Date, Ticker), Close列
            lookback: 回望期（交易日），默认126天≈6个月
        """
        # 展开价格数据
        prices = price_data['Close'].unstack(level='Ticker')
        
        # 计算收益率 (t / t-lookback) - 1
        momentum = prices.pct_change(lookback)
        
        # 重新堆叠
        momentum = momentum.stack()
        momentum.name = 'Momentum'
        
        return momentum.to_frame()
    
    @staticmethod
    def calculate_volatility(price_data: pd.DataFrame, lookback: int = 63) -> pd.DataFrame:
        """计算波动率因子（标准差）"""
        prices = price_data['Close'].unstack(level='Ticker')
        returns = prices.pct_change()
        volatility = returns.rolling(lookback).std() * np.sqrt(252)  # 年化波动率
        
        volatility = volatility.stack()
        volatility.name = 'Volatility'
        
        return volatility.to_frame()
    
    @staticmethod
    def calculate_returns(price_data: pd.DataFrame) -> pd.DataFrame:
        """计算日收益率"""
        prices = price_data['Close'].unstack(level='Ticker')
        returns = prices.pct_change()
        
        returns = returns.stack()
        returns.name = 'Daily_Return'
        
        return returns.to_frame()
