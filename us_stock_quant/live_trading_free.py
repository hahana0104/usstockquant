#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途实盘交易 + yfinance 数据源
策略计算用免费数据，交易执行走富途
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# 免费数据源
import yfinance as yf

from futu import *
from config import DATA_CONFIG, FACTOR_CONFIG, STRATEGY_CONFIG, SP500_TICKERS, SECTOR_MAP
from strategies.factors import ThreeFactorModel


class FreeDataSource:
    """免费数据源 (yfinance)"""
    
    def __init__(self, cache_dir=None):
        self.cache = {}
        
    def get_prices(self, tickers: List[str], period="1y") -> pd.DataFrame:
        """获取历史价格"""
        print(f"[Data] Downloading from Yahoo Finance ({len(tickers)} stocks)...")
        
        # yfinance 批量下载
        data = yf.download(
            tickers=' '.join(tickers),
            period=period,
            interval="1d",
            progress=False,
            threads=True
        )
        
        if len(tickers) == 1:
            # 单只股票格式处理
            df = pd.DataFrame({
                'Open': data['Open'],
                'High': data['High'],
                'Low': data['Low'],
                'Close': data['Close'],
                'Volume': data['Volume']
            })
            df.index.name = 'Date'
            return {tickers[0]: df}
        
        # 多只股票
        result = {}
        for ticker in tickers:
            try:
                df = pd.DataFrame({
                    'Open': data['Open'][ticker],
                    'High': data['High'][ticker],
                    'Low': data['Low'][ticker],
                    'Close': data['Close'][ticker],
                    'Volume': data['Volume'][ticker]
                })
                df = df.dropna()
                if len(df) > 50:  # 至少50天数据
                    result[ticker] = df
            except:
                continue
        
        print(f"[Data] Successfully loaded {len(result)} stocks")
        return result
    
    def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """获取实时价格 (Yahoo Finance, 15分钟延迟)"""
        print(f"[Data] Fetching live prices for {len(tickers)} stocks...")
        prices = {}
        
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                # 尝试获取实时报价
                hist = t.history(period="1d", interval="1m")
                if not hist.empty:
                    last_price = hist['Close'].iloc[-1]
                    prices[ticker] = float(last_price)
                else:
                    #  fallback 到日数据
                    info = t.info
                    prices[ticker] = info.get('regularMarketPrice', info.get('previousClose', 100.0))
            except Exception as e:
                print(f"  [WARN] {ticker}: {str(e)[:30]}")
                prices[ticker] = 100.0  # 默认价格
        
        print(f"[OK] Got prices for {len(prices)} stocks")
        return prices
    
    def get_quote_table(self, tickers: List[str]) -> pd.DataFrame:
        """获取完整报价表 (含涨跌幅)"""
        data = []
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                info = t.info
                hist = t.history(period="5d")
                
                if len(hist) >= 2:
                    last_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change_pct = (last_close - prev_close) / prev_close * 100
                else:
                    last_close = info.get('regularMarketPrice', 0)
                    prev_close = info.get('previousClose', 0)
                    change_pct = info.get('regularMarketChangePercent', 0)
                
                data.append({
                    'Ticker': ticker,
                    'Price': last_close,
                    'Change': change_pct,
                    'Volume': info.get('regularMarketVolume', 0),
                    'MarketCap': info.get('marketCap', 0),
                    'PE': info.get('trailingPE', 0),
                })
            except:
                continue
        
        return pd.DataFrame(data)


class FutuTrader:
    """富途交易器 (只用于下单)"""
    
    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.trade_ctx = None
        self.trd_env = TrdEnv.SIMULATE  # 默认模拟盘
        
    def connect(self):
        """连接 OpenD (只连交易端口)"""
        print("[1/3] Connecting to OpenD Trade API...")
        self.trade_ctx = OpenSecTradeContext(
            host=self.host,
            port=self.port,
            security_firm=SecurityFirm.FUTUSECURITIES,
            filter_trdmarket=TrdMarket.US
        )
        print(f"[OK] Trade API connected")
        return True
    
    def set_env(self, env='SIMULATE'):
        """设置环境"""
        self.trd_env = TrdEnv.SIMULATE if env == 'SIMULATE' else TrdEnv.REAL
        print(f"[INFO] Environment: {env}")
    
    def get_account_info(self):
        """获取账户信息"""
        ret, data = self.trade_ctx.accinfo_query(trd_env=self.trd_env)
        if ret == RET_OK:
            def safe_float(val):
                try:
                    return float(val) if val not in [None, 'N/A', ''] else 0.0
                except:
                    return 0.0
            
            return {
                'cash': safe_float(data.get('cash', [0])[0] if 'cash' in data.columns else 0),
                'market_val': safe_float(data.get('market_val', [0])[0] if 'market_val' in data.columns else 0),
                'total_assets': safe_float(data.get('total_assets', [0])[0] if 'total_assets' in data.columns else 0),
                'us_cash': safe_float(data.get('us_cash', [0])[0] if 'us_cash' in data.columns else 0),
                'power': safe_float(data.get('power', [0])[0] if 'power' in data.columns else 0),
            }
        return None
    
    def get_positions(self):
        """获取持仓"""
        ret, data = self.trade_ctx.position_list_query(trd_env=self.trd_env)
        if ret == RET_OK:
            if data.empty:
                return pd.DataFrame()
            return pd.DataFrame({
                'code': data.get('code', []),
                'name': data.get('stock_name', []),
                'qty': data.get('qty', []),
                'avg_cost': data.get('cost_price', []),
                'market_price': data.get('nominal_price', []),
                'market_val': data.get('market_val', []),
            })
        return None
    
    def place_order(self, code: str, qty: int, price: float, side: str):
        """下单"""
        trd_side = TrdSide.BUY if side == 'BUY' else TrdSide.SELL
        
        # 确保 code 格式正确
        if not code.startswith('US.'):
            code = f"US.{code}"
        
        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=qty,
            code=code,
            trd_side=trd_side,
            order_type=OrderType.NORMAL,
            trd_env=self.trd_env
        )
        
        if ret == RET_OK:
            order_id = data.get('order_id', [None])[0] if 'order_id' in data.columns else None
            print(f"[OK] Order: {side} {qty} x {code} @ ${price:.2f} (ID: {order_id})")
            return order_id
        else:
            print(f"[ERR] Order failed: {data}")
            return None
    
    def close(self):
        if self.trade_ctx:
            self.trade_ctx.close()
            print("[BYE] Disconnected")


class LiveStrategyRunner:
    """实盘策略运行器"""
    
    def __init__(self, trader: FutuTrader, data_source: FreeDataSource):
        self.trader = trader
        self.data = data_source
        self.factor_model = ThreeFactorModel(FACTOR_CONFIG)
    
    def run_strategy(self, tickers: List[str]) -> List[str]:
        """运行策略选股"""
        print("\n[2/3] Running strategy...")
        
        # 获取历史数据
        price_dict = self.data.get_prices(tickers, period="1y")
        
        if not price_dict:
            print("[ERR] No price data available")
            return []
        
        # 构建最新价格表
        latest_data = []
        for ticker, df in price_dict.items():
            if len(df) > 0:
                latest = df.iloc[-1]
                latest_data.append({
                    'Ticker': ticker,
                    'Open': latest['Open'],
                    'High': latest['High'],
                    'Low': latest['Low'],
                    'Close': latest['Close'],
                    'Volume': latest['Volume'],
                    'Returns_1M': df['Close'].pct_change(21).iloc[-1] if len(df) > 21 else 0,
                    'Returns_3M': df['Close'].pct_change(63).iloc[-1] if len(df) > 63 else 0,
                    'Returns_6M': df['Close'].pct_change(126).iloc[-1] if len(df) > 126 else 0,
                    'Volatility': df['Close'].pct_change().std() * np.sqrt(252) if len(df) > 20 else 0.2,
                })
        
        price_df = pd.DataFrame(latest_data).set_index('Ticker')
        
        # 模拟基本面数据（简化版）
        fundamentals = pd.DataFrame(index=price_df.index)
        fundamentals['ROE'] = 0.15 + np.random.normal(0, 0.05, len(fundamentals))  # 模拟ROE
        fundamentals['PE'] = 20 + np.random.normal(0, 10, len(fundamentals))  # 模拟PE
        fundamentals['PB'] = 2 + np.random.normal(0, 1, len(fundamentals))  # 模拟PB
        fundamentals['Sector'] = [SECTOR_MAP.get(t, 'Technology') for t in fundamentals.index]
        
        # 计算因子
        quality_score = self.factor_model.calculate_quality_score(fundamentals, price_df)
        value_score = self.factor_model.calculate_value_score(fundamentals)
        
        # 动量用实际收益率
        momentum_score = price_df['Returns_6M'] if 'Returns_6M' in price_df.columns else pd.Series(0, index=price_df.index)
        momentum_score = (momentum_score - momentum_score.min()) / (momentum_score.max() - momentum_score.min() + 0.001)
        
        # 合成
        combined_score = self.factor_model.combine_factors(quality_score, value_score, momentum_score)
        
        # 选股
        selected = self.factor_model.select_stocks(
            combined_score, fundamentals,
            n=STRATEGY_CONFIG['num_positions'],
            max_sector_pct=STRATEGY_CONFIG['max_sector_pct']
        )
        
        print(f"[OK] Selected {len(selected)} stocks")
        print(f"     Top 5: {', '.join(selected[:5])}")
        
        return selected, price_df
    
    def generate_orders(self, current_positions: pd.DataFrame, 
                       target_tickers: List[str],
                       price_df: pd.DataFrame,
                       account_info: Dict) -> List[Dict]:
        """生成调仓指令"""
        orders = []
        
        # 当前持仓
        current_codes = set()
        if not current_positions.empty and 'code' in current_positions.columns:
            current_codes = set([c.replace('US.', '') for c in current_positions['code']])
        
        target_codes = set(target_tickers)
        
        # 卖出的
        sell_codes = current_codes - target_codes
        for code in sell_codes:
            pos = current_positions[current_positions['code'] == f"US.{code}"]
            if not pos.empty:
                qty = int(pos['qty'].values[0])
                if qty > 0:
                    orders.append({'code': code, 'side': 'SELL', 'qty': qty, 'reason': 'Rebalance'})
        
        # 买入的
        buy_codes = target_codes - current_codes
        available_cash = account_info.get('us_cash', account_info.get('cash', 100000))
        position_value = available_cash / len(target_tickers) if target_tickers else 0
        
        for code in buy_codes:
            if code in price_df.index:
                price = price_df.loc[code, 'Close']
                qty = int(position_value / price)
                if qty > 0:
                    orders.append({
                        'code': code,
                        'side': 'BUY',
                        'qty': qty,
                        'price': price,
                        'reason': 'New target'
                    })
        
        return orders
    
    def execute_orders(self, orders: List[Dict], dry_run=True):
        """执行订单"""
        print(f"\n{'='*60}")
        print(f"ORDERS ({'DRY RUN' if dry_run else 'LIVE'})")
        print(f"{'='*60}")
        
        if not orders:
            print("No orders to execute")
            return 0
        
        for order in orders:
            code = order['code']
            side = order['side']
            qty = order['qty']
            price = order.get('price', 0)
            
            print(f"{side:4} {qty:5} x {code:6} @ ${price:>8.2f} | {order['reason']}")
            
            if not dry_run:
                self.trader.place_order(code, qty, price, side)
        
        return len(orders)


def show_live_prices(data_source: FreeDataSource, tickers: List[str]):
    """显示实时价格表"""
    print("\n" + "-"*70)
    print("LIVE MARKET PRICES (Yahoo Finance, delayed 15min)")
    print("-"*70)
    
    quotes = data_source.get_quote_table(tickers[:20])  # 显示前20只
    
    if not quotes.empty:
        # 按涨跌幅排序
        quotes = quotes.sort_values('Change', ascending=False)
        
        print(f"{'Ticker':<8} {'Price':>10} {'Change%':>10} {'Volume':>15} {'PE':>8}")
        print("-"*70)
        
        for _, row in quotes.iterrows():
            change_str = f"{row['Change']:+.2f}%"
            price_str = f"${row['Price']:.2f}"
            vol_str = f"{row['Volume']/1e6:.1f}M" if row['Volume'] > 1e6 else f"{row['Volume']/1e3:.0f}K"
            pe_str = f"{row['PE']:.1f}" if row['PE'] > 0 else "N/A"
            
            # 涨跌颜色标记 (模拟)
            marker = "▲" if row['Change'] > 0 else "▼" if row['Change'] < 0 else "-"
            
            print(f"{row['Ticker']:<8} {price_str:>10} {change_str:>9} {marker} {vol_str:>13} {pe_str:>8}")
    
    print("-"*70)
    return quotes


def main():
    """主程序"""
    print("="*60)
    print("   FUTU LIVE TRADING")
    print("   Free Data (Yahoo) + Futu Execution")
    print("="*60)
    
    # 初始化
    data_source = FreeDataSource()
    trader = FutuTrader(host='127.0.0.1', port=11111)
    
    # 股票池
    tickers = SP500_TICKERS[:30]  # 先用30只测试
    
    try:
        # === 模式1: 只看实时行情 ===
        show_live_prices(data_source, tickers)
        
        # === 模式2: 连接富途交易 ===
        print("\n[1/3] Connecting to OpenD Trade API...")
        trader.connect()
        trader.set_env('REAL')  # 实盘模式 (改回 SIMULATE 可切回模拟)
        
        # 获取账户信息
        print("\n[Account Info]")
        account = trader.get_account_info()
        if account:
            print(f"  Cash: ${account.get('us_cash', account.get('cash', 0)):,.2f}")
            print(f"  Assets: ${account.get('total_assets', 0):,.2f}")
        
        positions = trader.get_positions()
        print(f"  Positions: {len(positions) if positions is not None else 'N/A'}")
        
        # 运行策略
        runner = LiveStrategyRunner(trader, data_source)
        selected, price_df = runner.run_strategy(tickers)
        
        if not selected:
            print("\n[ERR] Strategy returned no stocks")
            return
        
        # 显示选中股票的实时价格
        print("\n[Selected Stocks Live Prices]")
        selected_quotes = data_source.get_current_prices(selected)
        for code, price in list(selected_quotes.items())[:10]:
            print(f"  {code:<6} ${price:>8.2f}")
        
        # 生成并执行订单
        orders = runner.generate_orders(positions, selected, price_df, account or {})
        
        # 确认是否执行
        if orders:
            print(f"\n[!] 即将执行 {len(orders)} 笔实盘订单")
            print("[!] 确认执行? (Ctrl+C 取消, 回车继续)")
            try:
                input()
                runner.execute_orders(orders, dry_run=False)  # 实盘下单
            except KeyboardInterrupt:
                print("\n[!] 已取消")
                runner.execute_orders(orders, dry_run=True)  # 仅预览
        else:
            print("\n[No orders needed]")
        
        print("\n" + "="*60)
        print("Done!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        trader.close()


if __name__ == '__main__':
    main()
