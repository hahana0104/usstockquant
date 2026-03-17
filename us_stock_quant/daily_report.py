#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日量化日报生成器
自动分析持仓并生成简洁报告
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


class DailyReport:
    """每日报告生成器"""
    
    def __init__(self):
        self.data_source = FreeDataSource()
        self.factor_model = ThreeFactorModel(FACTOR_CONFIG)
        
    def run(self):
        """生成完整报告"""
        report_lines = []
        report_lines.append(f"【量化日报 {datetime.now().strftime('%Y-%m-%d')}】")
        report_lines.append("")
        
        # 连接富途获取持仓
        try:
            query = FutuQuery()
            query.connect()
            positions = query.get_positions()
            query.close()
        except:
            positions = None
        
        # 1. 持仓分析
        if positions is not None and not positions.empty:
            report_lines.append("【你的持仓】")
            for _, pos in positions.iterrows():
                code = pos['code'].replace('US.', '')
                qty = int(pos.get('qty', 0))
                price = float(pos.get('nominal_price', 0))
                cost = float(pos.get('cost_price', 0))
                pl_pct = ((price / cost) - 1) * 100 if cost else 0
                report_lines.append(f"{code:<6} ${price:>7.2f}  {pl_pct:>+6.1f}%")
            report_lines.append("")
        
        # 2. 策略选股
        report_lines.append("【策略选股Top10】")
        try:
            tickers = SP500_TICKERS[:50]
            price_dict = self.data_source.get_prices(tickers, period="3mo")
            
            # 简化计算
            latest_data = []
            for ticker, df in price_dict.items():
                if len(df) >= 30:
                    returns = df['Close'].pct_change(63).iloc[-1]  # 3月动量
                    latest_data.append({'Ticker': ticker, 'Returns': returns, 'Price': df['Close'].iloc[-1]})
            
            df = pd.DataFrame(latest_data).set_index('Ticker')
            df['Score'] = (df['Returns'] - df['Returns'].min()) / (df['Returns'].max() - df['Returns'].min())
            top10 = df.nlargest(10, 'Score')
            
            for i, (ticker, row) in enumerate(top10.iterrows(), 1):
                report_lines.append(f"{i:2}. {ticker:<6} ${row['Price']:>7.2f}  得分{row['Score']:.2f}")
        except Exception as e:
            report_lines.append(f"[获取数据失败: {e}]")
        
        report_lines.append("")
        report_lines.append("【操作建议】")
        report_lines.append("📊 策略基于Quality+Value+Momentum因子计算")
        report_lines.append("⚠️  免责声明:仅供参考，不构成投资建议")
        
        return "\n".join(report_lines)


class FreeDataSource:
    def get_prices(self, tickers, period="3mo"):
        data = yf.download(tickers=' '.join(tickers[:30]), period=period, interval="1d", progress=False, threads=True)
        result = {}
        for ticker in tickers[:30]:
            try:
                if len(tickers) == 1:
                    df = data
                else:
                    df = pd.DataFrame({'Close': data['Close'][ticker]})
                df = df.dropna()
                if len(df) > 20:
                    result[ticker] = df
            except:
                continue
        return result


class FutuQuery:
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
        return True
    
    def get_positions(self):
        ret, data = self.trade_ctx.position_list_query(trd_env=TrdEnv.REAL)
        if ret == RET_OK:
            if data.empty:
                return pd.DataFrame()
            return pd.DataFrame({
                'code': data.get('code', []),
                'qty': data.get('qty', []),
                'cost_price': data.get('cost_price', []),
                'nominal_price': data.get('nominal_price', []),
            })
        return None
    
    def close(self):
        if self.trade_ctx:
            self.trade_ctx.close()


if __name__ == '__main__':
    report = DailyReport()
    print(report.run())
