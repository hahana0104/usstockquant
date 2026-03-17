"""
实时数据模块 - 获取实时行情
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List
from datetime import datetime
import streamlit as st


class RealtimeData:
    """实时数据获取"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = None
    
    @st.cache_data(ttl=60)  # 缓存60秒
    def get_stock_quote(_self, ticker: str) -> Dict:
        """获取股票实时报价和基本面数据"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="5d")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100 if prev_price > 0 else 0
            
            # 计算52周高低点
            hist_1y = stock.history(period="1y")
            week_52_high = hist_1y['High'].max() if not hist_1y.empty else None
            week_52_low = hist_1y['Low'].min() if not hist_1y.empty else None
            
            # 计算均线
            ma20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else None
            ma50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None
            
            return {
                # 基本信息
                'ticker': ticker,
                'name': info.get('shortName', info.get('longName', ticker)),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                
                # 价格数据
                'price': current_price,
                'change': change,
                'change_pct': change_pct,
                'open': hist['Open'].iloc[-1],
                'high': hist['High'].iloc[-1],
                'low': hist['Low'].iloc[-1],
                'prev_close': prev_price,
                'volume': hist['Volume'].iloc[-1],
                'avg_volume': info.get('averageVolume', 0),
                
                # 估值指标
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'pb_ratio': info.get('priceToBook'),
                'ps_ratio': info.get('priceToSalesTrailing12Months'),
                'peg_ratio': info.get('pegRatio'),
                'ev_ebitda': info.get('enterpriseToEbitda'),
                
                # 盈利能力
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'gross_margin': info.get('grossMargins'),
                'operating_margin': info.get('operatingMargins'),
                'profit_margin': info.get('profitMargins'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                
                # 财务健康
                'debt_to_equity': info.get('debtToEquityRatio'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),
                
                # 股息
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                
                # 技术指标
                'week_52_high': week_52_high,
                'week_52_low': week_52_low,
                'ma20': ma20,
                'ma50': ma50,
                'beta': info.get('beta'),
                
                # 分析师预期
                'target_high': info.get('targetHighPrice'),
                'target_low': info.get('targetLowPrice'),
                'target_mean': info.get('targetMeanPrice'),
                'recommendation': info.get('recommendationKey'),
                'num_analysts': info.get('numberOfAnalystOpinions'),
                
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
        except Exception as e:
            return {'error': str(e), 'ticker': ticker}
    
    @st.cache_data(ttl=60)
    def get_market_indices(_self) -> pd.DataFrame:
        """获取大盘指数"""
        indices = {
            '^GSPC': '标普500',
            '^DJI': '道琼斯',
            '^IXIC': '纳斯达克',
            '^VIX': 'VIX恐慌指数'
        }
        
        data = []
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change_pct = ((current - prev) / prev) * 100 if prev > 0 else 0
                    
                    data.append({
                        '指数': name,
                        '代码': symbol,
                        '现价': current,
                        '涨跌': change_pct
                    })
            except:
                continue
        
        return pd.DataFrame(data)
    
    @st.cache_data(ttl=300)  # 缓存5分钟
    def get_hot_stocks(_self, limit: int = 10) -> pd.DataFrame:
        """获取热门股票（成交量最大）"""
        # 使用一些大盘股作为代表
        tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'CRM']
        
        data = []
        for ticker in tickers:
            try:
                quote = _self.get_stock_quote(ticker)
                if quote and 'error' not in quote:
                    data.append({
                        '股票': quote['name'],
                        '代码': ticker,
                        '价格': quote['price'],
                        '涨跌': quote['change_pct'],
                        '成交量': quote['volume']
                    })
            except:
                continue
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('成交量', ascending=False).head(limit)
        return df
    
    def get_portfolio_status(self, positions: Dict[str, int]) -> pd.DataFrame:
        """获取持仓状态"""
        data = []
        total_value = 0
        
        for ticker, shares in positions.items():
            try:
                quote = self.get_stock_quote(ticker)
                if quote and 'error' not in quote:
                    value = quote['price'] * shares
                    total_value += value
                    data.append({
                        '代码': ticker,
                        '持仓': shares,
                        '现价': quote['price'],
                        '市值': value,
                        '涨跌': quote['change_pct']
                    })
            except:
                continue
        
        df = pd.DataFrame(data)
        if not df.empty and total_value > 0:
            df['占比'] = (df['市值'] / total_value * 100).round(2)
        
        return df
