#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途实盘交易适配器
连接三因子策略与 Futu OpenD
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

from futu import *

# 导入策略模块
from config import DATA_CONFIG, FACTOR_CONFIG, STRATEGY_CONFIG, BACKTEST_CONFIG, SP500_TICKERS, SECTOR_MAP
from data.data_loader import DataLoader
from strategies.factors import ThreeFactorModel


class FutuTrader:
    """富途实盘交易器"""
    
    def __init__(self, host='127.0.0.1', quote_port=11111, trade_port=11111):
        self.host = host
        self.quote_port = quote_port
        self.trade_port = trade_port
        
        self.quote_ctx = None
        self.trade_ctx = None
        self.trd_env = TrdEnv.SIMULATE  # 默认模拟盘，确认后再切实盘
        
    def connect(self):
        """连接 OpenD"""
        print("[1/3] Connecting to OpenD...")
        self.quote_ctx = OpenQuoteContext(host=self.host, port=self.quote_port)
        print(f"[OK] Quote API connected ({self.host}:{self.quote_port})")
        
        self.trade_ctx = OpenSecTradeContext(
            host=self.host,
            port=self.trade_port,
            security_firm=SecurityFirm.FUTUSECURITIES,
            filter_trdmarket=TrdMarket.US
        )
        print(f"[OK] Trade API connected")
        return True
    
    def set_env(self, env='SIMULATE'):
        """设置交易环境"""
        self.trd_env = TrdEnv.SIMULATE if env == 'SIMULATE' else TrdEnv.REAL
        print(f"[INFO] Trade environment: {env}")
    
    def get_account_info(self):
        """获取账户资金"""
        ret, data = self.trade_ctx.accinfo_query(trd_env=self.trd_env)
        if ret == RET_OK:
            # 安全解析数值，处理 N/A
            def safe_float(val):
                if val is None or val == 'N/A' or val == '':
                    return 0.0
                try:
                    return float(val)
                except:
                    return 0.0
            
            result = {}
            for col in ['cash', 'market_val', 'total_assets', 'power', 'us_cash', 'max_withdrawal']:
                if col in data.columns:
                    val = data[col].values[0] if len(data[col]) > 0 else 0
                    result[col] = safe_float(val)
                else:
                    result[col] = 0.0
            return result
        else:
            print(f"[ERR] Account query failed: {data}")
            return None
    
    def get_positions(self):
        """获取持仓"""
        ret, data = self.trade_ctx.position_list_query(trd_env=self.trd_env)
        if ret == RET_OK:
            if data.empty:
                return pd.DataFrame()
            # 标准化列名
            positions = pd.DataFrame({
                'code': data.get('code', []),
                'name': data.get('stock_name', []),
                'qty': data.get('qty', []),
                'avg_cost': data.get('cost_price', []),
                'market_price': data.get('nominal_price', []),
                'market_val': data.get('market_val', []),
                'pl_ratio': data.get('pl_ratio', []),
            })
            return positions
        else:
            print(f"[ERR] Position query failed: {data}")
            return None
    
    def get_orders(self):
        """获取订单列表"""
        ret, data = self.trade_ctx.order_list_query(trd_env=self.trd_env)
        if ret == RET_OK:
            return data
        else:
            print(f"[ERR] Order list failed: {data}")
            return None
    
    def place_order(self, code: str, qty: int, price: float, side: str, 
                   order_type=OrderType.NORMAL):
        """下单"""
        trd_side = TrdSide.BUY if side == 'BUY' else TrdSide.SELL
        
        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=qty,
            code=code,
            trd_side=trd_side,
            order_type=order_type,
            trd_env=self.trd_env
        )
        
        if ret == RET_OK:
            order_id = data.get('order_id', [None])[0] if 'order_id' in data.columns else None
            print(f"[OK] Order placed: {side} {qty} x {code} @ ${price:.2f} (ID: {order_id})")
            return order_id
        else:
            print(f"[ERR] Order failed: {data}")
            return None
    
    def get_price(self, code: str):
        """获取实时价格"""
        ret, data = self.quote_ctx.get_stock_quote([code])
        if ret == RET_OK:
            return {
                'code': code,
                'last_price': float(data['last_price'].values[0]),
                'open': float(data['open_price'].values[0]),
                'high': float(data['high_price'].values[0]),
                'low': float(data['low_price'].values[0]),
                'prev_close': float(data['prev_close_price'].values[0]),
            }
        else:
            print(f"[ERR] Price query failed: {data}")
            return None
    
    def get_prices(self, codes: List[str]):
        """批量获取价格 (先订阅再查询)"""
        # 1. 先订阅
        sub_codes = codes if isinstance(codes, list) else [codes]
        ret_sub, _ = self.quote_ctx.subscribe(sub_codes, [SubType.QUOTE])
        
        # 2. 等待一小会儿让数据推送
        import time
        time.sleep(0.5)
        
        # 3. 查询价格
        ret, data = self.quote_ctx.get_stock_quote(codes)
        if ret == RET_OK:
            prices = {}
            for _, row in data.iterrows():
                prices[row['code']] = {
                    'last': float(row['last_price']),
                    'open': float(row['open_price']),
                    'high': float(row['high_price']),
                    'low': float(row['low_price']),
                }
            return prices
        else:
            print(f"[WARN] Price query failed: {data}")
            print("[INFO] Using mock prices for demo")
            # 返回模拟价格用于测试
            return {code: {'last': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0} for code in codes}
    
    def close(self):
        """关闭连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        print("[BYE] Disconnected from OpenD")


class LiveStrategyRunner:
    """实盘策略运行器"""
    
    def __init__(self, trader: FutuTrader):
        self.trader = trader
        self.factor_model = ThreeFactorModel(FACTOR_CONFIG)
        self.target_positions = {}  # 目标持仓
        
    def get_live_data(self, tickers: List[str]):
        """从富途获取实时数据"""
        print(f"[2/3] Fetching live data for {len(tickers)} stocks...")
        
        # 获取实时价格
        prices = self.trader.get_prices([f"US.{t}" for t in tickers])
        
        # 构建价格DataFrame (简化处理，用当前价作为OHLC)
        price_data = {}
        for ticker in tickers:
            code = f"US.{ticker}"
            if code in prices:
                p = prices[code]
                price_data[ticker] = pd.Series({
                    'Open': p['open'],
                    'High': p['high'],
                    'Low': p['low'],
                    'Close': p['last'],
                    'Volume': 0,  # 实盘可不关注
                })
        
        df = pd.DataFrame(price_data).T
        df.index.name = 'Ticker'
        return df
    
    def calculate_signals(self, price_data: pd.DataFrame, fundamentals: pd.DataFrame = None):
        """计算交易信号"""
        print("[3/3] Calculating factor signals...")
        
        tickers = price_data.index.tolist()
        
        # 使用默认基本面（简化版）
        if fundamentals is None or fundamentals.empty:
            fundamentals = pd.DataFrame(index=tickers)
            fundamentals['ROE'] = 0.15  # 默认中等质量
            fundamentals['PE'] = 20
            fundamentals['PB'] = 2
            fundamentals['Sector'] = [SECTOR_MAP.get(t, 'Unknown') for t in tickers]
        
        # 计算因子得分
        quality_score = self.factor_model.calculate_quality_score(fundamentals, price_data)
        value_score = self.factor_model.calculate_value_score(fundamentals)
        
        # 动量因子（用当前价格 vs 需要历史数据，这里简化）
        momentum_score = pd.Series(0.5, index=tickers)
        
        # 合成
        combined_score = self.factor_model.combine_factors(
            quality_score, value_score, momentum_score
        )
        
        # 选股
        selected = self.factor_model.select_stocks(
            combined_score,
            fundamentals,
            n=STRATEGY_CONFIG['num_positions'],
            max_sector_pct=STRATEGY_CONFIG['max_sector_pct']
        )
        
        return selected, combined_score
    
    def generate_orders(self, current_positions: pd.DataFrame, 
                       target_tickers: List[str],
                       account_info: Dict) -> List[Dict]:
        """生成调仓指令"""
        orders = []
        
        # 当前持仓代码
        current_codes = set()
        if not current_positions.empty:
            current_codes = set(current_positions['code'].str.replace('US.', '').tolist())
        
        target_codes = set(target_tickers)
        
        # 需要卖出的
        sell_codes = current_codes - target_codes
        for code in sell_codes:
            pos_row = current_positions[current_positions['code'] == f"US.{code}"]
            if not pos_row.empty:
                qty = int(pos_row['qty'].values[0])
                if qty > 0:
                    orders.append({
                        'code': f"US.{code}",
                        'side': 'SELL',
                        'qty': qty,
                        'reason': 'Rebalance - not in target list'
                    })
        
        # 需要买入的（新目标不在当前持仓中）
        buy_codes = target_codes - current_codes
        
        # 计算每只股票的仓位（等权）
        available_cash = account_info.get('us_cash', account_info.get('cash', 0))
        position_value = available_cash / len(target_tickers) if target_tickers else 0
        
        for code in buy_codes:
            # 获取当前价
            price_info = self.trader.get_price(f"US.{code}")
            if price_info:
                price = price_info['last_price']
                qty = int(position_value / price)
                if qty > 0:
                    orders.append({
                        'code': f"US.{code}",
                        'side': 'BUY',
                        'qty': qty,
                        'price': price,
                        'reason': 'Rebalance - new target'
                    })
        
        return orders
    
    def execute_rebalance(self, orders: List[Dict], dry_run=True):
        """执行调仓"""
        print(f"\n{'='*60}")
        print(f"REBALANCE ORDERS ({'DRY RUN' if dry_run else 'LIVE'})")
        print(f"{'='*60}")
        
        for order in orders:
            code = order['code']
            side = order['side']
            qty = order['qty']
            price = order.get('price', 0)
            
            print(f"{side:4} {qty:4} x {code:12} @ ${price:.2f} | {order['reason']}")
            
            if not dry_run:
                # 实盘下单
                order_id = self.trader.place_order(code, qty, price, side)
                if order_id:
                    print(f"     -> Order ID: {order_id}")
        
        return len(orders)


def main():
    """主程序：连接实盘并运行策略"""
    print("="*60)
    print("   FUTU LIVE TRADING - Three Factor Strategy")
    print("   Quality + Value + Momentum")
    print("="*60)
    
    # 1. 连接交易器
    trader = FutuTrader(host='127.0.0.1', quote_port=11111, trade_port=11111)
    trader.connect()
    
    try:
        # 2. 设置环境（先模拟盘测试）
        trader.set_env('SIMULATE')  # 确认没问题后改为 'REAL'
        
        # 3. 获取账户信息
        print("\n[Account Status]")
        account = trader.get_account_info()
        if account:
            print(f"  Cash (USD): ${account.get('us_cash', account.get('cash', 0)):,.2f}")
            print(f"  Market Value: ${account.get('market_val', 0):,.2f}")
            print(f"  Total Assets: ${account.get('total_assets', 0):,.2f}")
        
        # 4. 获取当前持仓
        print("\n[Current Positions]")
        positions = trader.get_positions()
        if positions is not None:
            if positions.empty:
                print("  No positions")
            else:
                print(positions.to_string(index=False))
        
        # 5. 运行策略生成信号
        runner = LiveStrategyRunner(trader)
        
        # 使用 S&P 500 前30只做选股池
        tickers = SP500_TICKERS[:30]
        
        # 获取实时价格数据
        price_data = runner.get_live_data(tickers)
        
        # 计算信号
        selected_tickers, scores = runner.calculate_signals(price_data)
        
        print(f"\n[Strategy Output]")
        print(f"  Selected: {len(selected_tickers)} stocks")
        print(f"  Tickers: {', '.join(selected_tickers[:10])}")
        
        # 显示得分最高的10只
        print(f"\n[Top 10 by Score]")
        top10 = scores.nlargest(10)
        for ticker, score in top10.items():
            print(f"  {ticker:6} | Score: {score:.3f}")
        
        # 6. 生成调仓指令
        orders = runner.generate_orders(positions, selected_tickers, account)
        
        # 7. 执行（默认先模拟）
        if orders:
            runner.execute_rebalance(orders, dry_run=True)  # 改为 False 则实盘下单
        else:
            print("\n[No orders needed]")
        
        print("\n" + "="*60)
        print("Strategy check completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        trader.close()


if __name__ == '__main__':
    main()
