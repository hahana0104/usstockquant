#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化策略分析工具 - 只查询建议，不执行交易
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
from futu import *
from config import SP500_TICKERS, SECTOR_MAP, STRATEGY_CONFIG, FACTOR_CONFIG
from strategies.factors import ThreeFactorModel


class FreeDataSource:
    """免费数据源"""
    
    def get_prices(self, tickers, period="6mo"):
        """获取历史价格"""
        print(f"[Data] 下载 {len(tickers)} 只股票数据...")
        
        data = yf.download(
            tickers=' '.join(tickers[:50]),  # 限制50只避免超时
            period=period,
            interval="1d",
            progress=False,
            threads=True
        )
        
        result = {}
        for ticker in tickers[:50]:
            try:
                if len(tickers) == 1:
                    df = data
                else:
                    df = pd.DataFrame({
                        'Open': data['Open'][ticker],
                        'High': data['High'][ticker],
                        'Low': data['Low'][ticker],
                        'Close': data['Close'][ticker],
                        'Volume': data['Volume'][ticker]
                    })
                df = df.dropna()
                if len(df) > 20:
                    result[ticker] = df
            except:
                continue
        
        print(f"[OK] 成功获取 {len(result)} 只股票")
        return result
    
    def get_current_price(self, ticker):
        """获取当前价格"""
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        return None


class PortfolioAnalyzer:
    """持仓分析器"""
    
    def __init__(self):
        self.data_source = FreeDataSource()
        self.factor_model = ThreeFactorModel(FACTOR_CONFIG)
    
    def analyze_positions(self, positions_df):
        """分析当前持仓"""
        if positions_df is None or positions_df.empty:
            print("\n[持仓分析] 当前无持仓")
            return None
        
        print("\n" + "="*70)
        print("Current Positions Analysis")
        print("="*70)
        
        analysis = []
        total_value = 0
        total_pl = 0
        
        for _, pos in positions_df.iterrows():
            code = pos['code'].replace('US.', '') if 'code' in pos else pos.get('stock_code', '')
            qty = int(pos.get('qty', 0))
            avg_cost = float(pos.get('cost_price', 0) or pos.get('avg_cost', 0))
            cur_price = float(pos.get('nominal_price', 0) or pos.get('market_price', 0))
            market_val = qty * cur_price if qty and cur_price else 0
            pl = (cur_price - avg_cost) * qty if qty and avg_cost else 0
            pl_pct = ((cur_price / avg_cost) - 1) * 100 if avg_cost else 0
            
            total_value += market_val
            total_pl += pl
            
            analysis.append({
                '代码': code,
                '数量': qty,
                '成本价': avg_cost,
                '现价': cur_price,
                '市值': market_val,
                '盈亏': pl,
                '盈亏%': pl_pct,
                '建议': ''
            })
        
        df = pd.DataFrame(analysis)
        
        # 显示持仓表格
        print(f"{'Code':<8} {'Qty':>8} {'Cost':>10} {'Price':>10} {'Value':>12} {'P/L%':>10}")
        print("-"*70)
        
        for _, row in df.iterrows():
            marker = "+" if row['盈亏%'] > 0 else "-" if row['盈亏%'] < 0 else "="
            print(f"{row['代码']:<8} {row['数量']:>8} ${row['成本价']:>9.2f} ${row['现价']:>9.2f} "
                  f"${row['市值']:>10.0f} {row['盈亏%']:>+9.1f}% {marker}")
        
        print("-"*70)
        print(f"总市值: ${total_value:,.2f}  |  总盈亏: ${total_pl:+,.2f}")
        
        return df
    
    def run_strategy_signals(self, tickers=None):
        """运行策略生成信号"""
        if tickers is None:
            tickers = SP500_TICKERS[:50]
        
        print("\n" + "="*70)
        print("Strategy Signals (Quality + Value + Momentum)")
        print("="*70)
        
        # 获取数据
        price_dict = self.data_source.get_prices(tickers, period="6mo")
        
        if not price_dict:
            print("[ERR] 数据获取失败")
            return []
        
        # 构建数据表
        latest_data = []
        for ticker, df in price_dict.items():
            if len(df) >= 60:
                latest = df.iloc[-1]
                returns_1m = df['Close'].pct_change(21).iloc[-1]
                returns_3m = df['Close'].pct_change(63).iloc[-1]
                returns_6m = df['Close'].pct_change(126).iloc[-1] if len(df) > 126 else returns_3m
                volatility = df['Close'].pct_change().std() * np.sqrt(252)
                
                latest_data.append({
                    'Ticker': ticker,
                    'Close': latest['Close'],
                    'Volume': latest['Volume'],
                    'Returns_1M': returns_1m,
                    'Returns_3M': returns_3m,
                    'Returns_6M': returns_6m,
                    'Volatility': volatility,
                })
        
        price_df = pd.DataFrame(latest_data).set_index('Ticker')
        
        # 模拟基本面
        fundamentals = pd.DataFrame(index=price_df.index)
        fundamentals['ROE'] = np.clip(0.15 + np.random.normal(0, 0.08, len(fundamentals)), 0.05, 0.4)
        fundamentals['PE'] = np.clip(20 + np.random.normal(0, 15, len(fundamentals)), 5, 100)
        fundamentals['PB'] = np.clip(2 + np.random.normal(0, 1.5, len(fundamentals)), 0.5, 10)
        fundamentals['Sector'] = [SECTOR_MAP.get(t, 'Technology') for t in fundamentals.index]
        
        # 计算因子
        quality_score = self.factor_model.calculate_quality_score(fundamentals, price_df)
        value_score = self.factor_model.calculate_value_score(fundamentals)
        
        momentum_score = price_df['Returns_6M'] if 'Returns_6M' in price_df.columns else pd.Series(0, index=price_df.index)
        momentum_score = (momentum_score - momentum_score.min()) / (momentum_score.max() - momentum_score.min() + 0.001)
        
        combined_score = self.factor_model.combine_factors(quality_score, value_score, momentum_score)
        
        # 选股
        selected = self.factor_model.select_stocks(
            combined_score, fundamentals,
            n=STRATEGY_CONFIG['num_positions'],
            max_sector_pct=STRATEGY_CONFIG['max_sector_pct']
        )
        
        # 显示结果
        print(f"\nStrategy Buy Signals (Top {len(selected)}):")
        print(f"{'Rank':<4} {'Ticker':<8} {'Score':>10} {'Quality':>8} {'Value':>8} {'Momentum':>8} {'Price':>10}")
        print("-"*70)
        
        for i, ticker in enumerate(selected[:15], 1):
            score = combined_score.get(ticker, 0)
            q_score = quality_score.get(ticker, 0)
            v_score = value_score.get(ticker, 0)
            m_score = momentum_score.get(ticker, 0)
            price = price_df.loc[ticker, 'Close'] if ticker in price_df.index else 0
            
            print(f"{i:<4} {ticker:<8} {score:>10.3f} {q_score:>8.3f} {v_score:>8.3f} {m_score:>8.3f} ${price:>9.2f}")
        
        return selected
    
    def generate_advice(self, current_positions_df, target_tickers):
        """生成操作建议"""
        print("\n" + "="*70)
        print("Trading Suggestions")
        print("="*70)
        
        if current_positions_df is None or current_positions_df.empty:
            current_codes = set()
        else:
            current_codes = set([c.replace('US.', '') for c in current_positions_df['code']])
        
        target_codes = set(target_tickers)
        
        # 建议卖出
        to_sell = current_codes - target_codes
        if to_sell:
            print(f"\n[SELL] Suggested ({len(to_sell)} stocks) - Not in strategy selection:")
            for code in sorted(to_sell):
                pos = current_positions_df[current_positions_df['code'] == f"US.{code}"]
                if not pos.empty:
                    pl_pct = float(pos['pl_ratio'].values[0]) if 'pl_ratio' in pos.columns else 0
                    marker = "(PROFIT)" if pl_pct > 0 else "(LOSS)"
                    print(f"   {code:<6} {marker} Current P/L: {pl_pct:+.1f}%")
        else:
            print("\n[SELL] None")
        
        # 建议买入
        to_buy = target_codes - current_codes
        if to_buy:
            print(f"\n[BUY] Suggested ({len(to_buy)} stocks) - New strategy picks:")
            for code in sorted(to_buy)[:10]:
                print(f"   * {code}")
            if len(to_buy) > 10:
                print(f"   ... and {len(to_buy)-10} more")
        else:
            print("\n[BUY] None")
        
        # 建议持有
        to_hold = current_codes & target_codes
        if to_hold:
            print(f"\n[HOLD] Suggested ({len(to_hold)} stocks) - Still in strategy:")
            print(f"   {', '.join(sorted(to_hold))}")
        
        print("\n" + "="*70)
        print("DISCLAIMER: For reference only, not investment advice.")
        print("Make your own decisions based on your risk tolerance.")
        print("="*70)


class FutuQuery:
    """富途查询（只读）"""
    
    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.trade_ctx = None
        
    def connect(self):
        self.trade_ctx = OpenSecTradeContext(
            host=self.host, port=self.port,
            security_firm=SecurityFirm.FUTUSECURITIES,
            filter_trdmarket=TrdMarket.US
        )
        print("[OK] 已连接富途")
        return True
    
    def get_account_info(self):
        """查询账户"""
        ret, data = self.trade_ctx.accinfo_query(trd_env=TrdEnv.REAL)
        if ret == RET_OK:
            print("\n" + "="*70)
            print("Account Info (Real Account)")
            print("="*70)
            
            def safe_float(val):
                try:
                    return float(val) if val not in [None, 'N/A', ''] else 0.0
                except:
                    return 0.0
            
            fields = {
                'total_assets': 'Total Assets',
                'cash': 'Cash',
                'us_cash': 'USD Cash',
                'market_val': 'Position Value',
                'power': 'Buying Power',
            }
            
            for col, name in fields.items():
                if col in data.columns:
                    val = safe_float(data[col].values[0])
                    print(f"  {name:<15}: ${val:>12,.2f}")
            
            return True
        return False
    
    def get_positions(self):
        """查询持仓"""
        ret, data = self.trade_ctx.position_list_query(trd_env=TrdEnv.REAL)
        if ret == RET_OK:
            if data.empty:
                return pd.DataFrame()
            return pd.DataFrame({
                'code': data.get('code', []),
                'name': data.get('stock_name', []),
                'qty': data.get('qty', []),
                'cost_price': data.get('cost_price', []),
                'nominal_price': data.get('nominal_price', []),
                'market_val': data.get('market_val', []),
                'pl_ratio': data.get('pl_ratio', []),
            })
        return None
    
    def close(self):
        if self.trade_ctx:
            self.trade_ctx.close()


def main():
    """主程序：查询+分析+建议"""
    print("="*70)
    print("   量化策略分析工具")
    print("   仅查询分析，不执行交易")
    print("="*70)
    
    # 初始化
    query = FutuQuery()
    analyzer = PortfolioAnalyzer()
    
    try:
        # 1. 连接富途查询
        query.connect()
        query.get_account_info()
        positions = query.get_positions()
        
        # 2. 分析当前持仓
        analyzer.analyze_positions(positions)
        
        # 3. 运行策略生成信号
        print("\n[正在运行策略分析，请稍候...]")
        target_tickers = analyzer.run_strategy_signals()
        
        # 4. 生成操作建议
        if target_tickers:
            analyzer.generate_advice(positions, target_tickers)
        
        print("\n" + "="*70)
        print("分析完成。请根据以上建议自主决策。")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERR] {e}")
    finally:
        query.close()


if __name__ == '__main__':
    main()
