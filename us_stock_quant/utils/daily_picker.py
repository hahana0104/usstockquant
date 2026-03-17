"""
每日选股推荐模块
基于策略给出今日推荐股票
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict
import streamlit as st

from config import SP500_TICKERS, FACTOR_CONFIG
from strategies.factors import ThreeFactorModel
from strategies.all_strategies import get_strategy
from data.data_loader import DataLoader


class DailyStockPicker:
    """每日选股推荐"""
    
    def __init__(self):
        self.loader = DataLoader()
    
    @st.cache_data(ttl=3600)  # 缓存1小时
    def get_daily_picks(_self, strategy_type: str = 'three_factor', 
                        num_stocks: int = 10,
                        tickers: List[str] = None) -> pd.DataFrame:
        """获取今日选股推荐"""
        
        if tickers is None:
            tickers = SP500_TICKERS[:50]  # 默认前50只
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6个月数据
        
        try:
            # 下载数据
            price_data = _self.loader.download_prices(
                tickers=tickers,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
            
            if price_data.empty:
                return pd.DataFrame()
            
            # 根据策略类型选股
            if strategy_type == 'three_factor':
                picks = _self._pick_by_three_factor(price_data, tickers, num_stocks)
            elif strategy_type == 'ma_cross':
                picks = _self._pick_by_ma(price_data, tickers, num_stocks)
            elif strategy_type == 'rsi':
                picks = _self._pick_by_rsi(price_data, tickers, num_stocks)
            elif strategy_type == 'macd':
                picks = _self._pick_by_macd(price_data, tickers, num_stocks)
            else:
                picks = _self._pick_by_momentum(price_data, tickers, num_stocks)
            
            return picks
            
        except Exception as e:
            st.error(f"选股出错: {str(e)}")
            return pd.DataFrame()
    
    def _pick_by_three_factor(self, price_data, tickers, num_stocks):
        """三因子选股"""
        fundamentals = self.loader.download_fundamentals(tickers)
        factor_model = ThreeFactorModel(FACTOR_CONFIG)
        
        quality_score = factor_model.calculate_quality_score(fundamentals, price_data) if not fundamentals.empty else pd.Series(0.5, index=tickers)
        value_score = factor_model.calculate_value_score(fundamentals) if not fundamentals.empty else pd.Series(0.5, index=tickers)
        momentum_score = factor_model.calculate_momentum_score(price_data, datetime.now())
        
        combined = factor_model.combine_factors(quality_score, value_score, momentum_score)
        selected = factor_model.select_stocks(combined, 
            fundamentals if not fundamentals.empty else pd.DataFrame(index=combined.index),
            n=num_stocks)
        
        # 构建推荐列表
        picks = []
        for ticker in selected:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="5d")
                
                if hist.empty:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
                
                picks.append({
                    '排名': len(picks) + 1,
                    '代码': ticker,
                    '名称': info.get('shortName', ticker),
                    '现价': current_price,
                    '涨跌': change_pct,
                    '市值(B)': info.get('marketCap', 0) / 1e9,
                    'PE': info.get('trailingPE'),
                    'PB': info.get('priceToBook'),
                    'ROE': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None,
                    '综合得分': combined.get(ticker, 0),
                    '质量': quality_score.get(ticker, 0),
                    '价值': value_score.get(ticker, 0),
                    '动量': momentum_score.get(ticker, 0),
                })
            except:
                continue
        
        return pd.DataFrame(picks)
    
    def _pick_by_ma(self, price_data, tickers, num_stocks):
        """均线策略选股"""
        picks = []
        
        for ticker in tickers:
            try:
                if ticker not in price_data['Close'].columns:
                    continue
                
                prices = price_data['Close'][ticker].dropna()
                if len(prices) < 50:
                    continue
                
                ma20 = prices.rolling(20).mean().iloc[-1]
                ma50 = prices.rolling(50).mean().iloc[-1]
                current_price = prices.iloc[-1]
                
                # 金叉信号：短期均线上穿长期均线
                signal_strength = 0
                if ma20 > ma50 and current_price > ma20:
                    signal_strength = (current_price / ma20 - 1) * 100
                
                if signal_strength > 0:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    picks.append({
                        '排名': 0,  # 稍后排序
                        '代码': ticker,
                        '名称': info.get('shortName', ticker),
                        '现价': current_price,
                        'MA20': ma20,
                        'MA50': ma50,
                        '信号强度': signal_strength,
                        '市值(B)': info.get('marketCap', 0) / 1e9,
                    })
            except:
                continue
        
        # 按信号强度排序
        picks_df = pd.DataFrame(picks)
        if not picks_df.empty:
            picks_df = picks_df.sort_values('信号强度', ascending=False).head(num_stocks)
            picks_df['排名'] = range(1, len(picks_df) + 1)
        
        return picks_df
    
    def _pick_by_rsi(self, price_data, tickers, num_stocks):
        """RSI策略选股 - 找超卖股票"""
        picks = []
        
        for ticker in tickers:
            try:
                if ticker not in price_data['Close'].columns:
                    continue
                
                prices = price_data['Close'][ticker].dropna()
                if len(prices) < 14:
                    continue
                
                # 计算RSI
                delta = prices.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                # RSI < 40 视为超卖买入机会
                if current_rsi < 40:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    current_price = prices.iloc[-1]
                    
                    picks.append({
                        '排名': 0,
                        '代码': ticker,
                        '名称': info.get('shortName', ticker),
                        '现价': current_price,
                        'RSI': current_rsi,
                        '超卖程度': 40 - current_rsi,
                        '市值(B)': info.get('marketCap', 0) / 1e9,
                    })
            except:
                continue
        
        picks_df = pd.DataFrame(picks)
        if not picks_df.empty:
            picks_df = picks_df.sort_values('超卖程度', ascending=False).head(num_stocks)
            picks_df['排名'] = range(1, len(picks_df) + 1)
        
        return picks_df
    
    def _pick_by_macd(self, price_data, tickers, num_stocks):
        """MACD策略选股"""
        picks = []
        
        for ticker in tickers:
            try:
                if ticker not in price_data['Close'].columns:
                    continue
                
                prices = price_data['Close'][ticker].dropna()
                if len(prices) < 26:
                    continue
                
                exp1 = prices.ewm(span=12).mean()
                exp2 = prices.ewm(span=26).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9).mean()
                
                # MACD金叉
                if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    current_price = prices.iloc[-1]
                    
                    picks.append({
                        '排名': 0,
                        '代码': ticker,
                        '名称': info.get('shortName', ticker),
                        '现价': current_price,
                        'MACD': macd.iloc[-1],
                        '信号线': signal.iloc[-1],
                        '金叉强度': macd.iloc[-1] - signal.iloc[-1],
                        '市值(B)': info.get('marketCap', 0) / 1e9,
                    })
            except:
                continue
        
        picks_df = pd.DataFrame(picks)
        if not picks_df.empty:
            picks_df = picks_df.sort_values('金叉强度', ascending=False).head(num_stocks)
            picks_df['排名'] = range(1, len(picks_df) + 1)
        
        return picks_df
    
    def _pick_by_momentum(self, price_data, tickers, num_stocks):
        """动量选股 - 近3个月涨幅最大"""
        picks = []
        
        for ticker in tickers:
            try:
                if ticker not in price_data['Close'].columns:
                    continue
                
                prices = price_data['Close'][ticker].dropna()
                if len(prices) < 60:
                    continue
                
                momentum = (prices.iloc[-1] / prices.iloc[-60] - 1) * 100
                
                if momentum > 0:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    current_price = prices.iloc[-1]
                    
                    picks.append({
                        '排名': 0,
                        '代码': ticker,
                        '名称': info.get('shortName', ticker),
                        '现价': current_price,
                        '3月涨幅': momentum,
                        '市值(B)': info.get('marketCap', 0) / 1e9,
                    })
            except:
                continue
        
        picks_df = pd.DataFrame(picks)
        if not picks_df.empty:
            picks_df = picks_df.sort_values('3月涨幅', ascending=False).head(num_stocks)
            picks_df['排名'] = range(1, len(picks_df) + 1)
        
        return picks_df
