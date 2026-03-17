"""
数据库模块 - 保存回测历史
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
import os


class BacktestDatabase:
    """回测数据库"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用项目目录下的data文件夹
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'data', 'backtest_history.db')
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 回测记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    strategy TEXT,
                    strategy_params TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    tickers TEXT,
                    initial_capital REAL,
                    commission REAL,
                    total_return REAL,
                    annual_return REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 权益曲线表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equity_curves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backtest_id INTEGER,
                    date TEXT,
                    equity REAL,
                    cash REAL,
                    positions INTEGER,
                    FOREIGN KEY (backtest_id) REFERENCES backtests(id)
                )
            ''')
            
            # 交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backtest_id INTEGER,
                    date TEXT,
                    ticker TEXT,
                    action TEXT,
                    shares INTEGER,
                    price REAL,
                    amount REAL,
                    FOREIGN KEY (backtest_id) REFERENCES backtests(id)
                )
            ''')
            
            conn.commit()
    
    def save_backtest(self, name: str, strategy: str, strategy_params: Dict,
                     start_date: str, end_date: str, tickers: List[str],
                     initial_capital: float, commission: float,
                     metrics: Dict, equity_curve: pd.DataFrame,
                     trades: pd.DataFrame) -> int:
        """保存回测结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入回测记录
            cursor.execute('''
                INSERT INTO backtests 
                (name, strategy, strategy_params, start_date, end_date, tickers,
                 initial_capital, commission, total_return, annual_return,
                 max_drawdown, sharpe_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, strategy, json.dumps(strategy_params),
                start_date, end_date, json.dumps(tickers),
                initial_capital, commission,
                metrics.get('total_return', 0),
                metrics.get('annual_return', 0),
                metrics.get('max_drawdown', 0),
                metrics.get('sharpe_ratio', 0)
            ))
            
            backtest_id = cursor.lastrowid
            
            # 保存权益曲线
            if not equity_curve.empty:
                equity_data = []
                for _, row in equity_curve.iterrows():
                    equity_data.append((
                        backtest_id,
                        str(row.get('Date', '')),
                        float(row.get('Equity', 0)),
                        float(row.get('Cash', 0)),
                        int(row.get('Positions', 0))
                    ))
                
                cursor.executemany('''
                    INSERT INTO equity_curves 
                    (backtest_id, date, equity, cash, positions)
                    VALUES (?, ?, ?, ?, ?)
                ''', equity_data)
            
            # 保存交易记录
            if not trades.empty:
                trades_data = []
                for _, row in trades.iterrows():
                    trades_data.append((
                        backtest_id,
                        str(row.get('Date', '')),
                        str(row.get('Ticker', '')),
                        str(row.get('Action', '')),
                        int(row.get('Shares', 0)),
                        float(row.get('Price', 0)),
                        float(row.get('Cost', row.get('Proceeds', 0)))
                    ))
                
                cursor.executemany('''
                    INSERT INTO trades 
                    (backtest_id, date, ticker, action, shares, price, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', trades_data)
            
            conn.commit()
            return backtest_id
    
    def get_backtest_list(self, limit: int = 50) -> pd.DataFrame:
        """获取回测列表"""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT id, name, strategy, start_date, end_date,
                       total_return, annual_return, max_drawdown, 
                       sharpe_ratio, created_at
                FROM backtests
                ORDER BY created_at DESC
                LIMIT ?
            ''', conn, params=(limit,))
        return df
    
    def get_backtest_detail(self, backtest_id: int) -> Dict:
        """获取回测详情"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本信息
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM backtests WHERE id = ?
            ''', (backtest_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            backtest_info = dict(zip(columns, row))
            
            # 解析JSON字段
            backtest_info['strategy_params'] = json.loads(backtest_info.get('strategy_params', '{}'))
            backtest_info['tickers'] = json.loads(backtest_info.get('tickers', '[]'))
            
            # 权益曲线
            equity_df = pd.read_sql_query('''
                SELECT date, equity, cash, positions FROM equity_curves
                WHERE backtest_id = ? ORDER BY date
            ''', conn, params=(backtest_id,))
            
            # 交易记录
            trades_df = pd.read_sql_query('''
                SELECT date, ticker, action, shares, price, amount FROM trades
                WHERE backtest_id = ? ORDER BY date
            ''', conn, params=(backtest_id,))
            
            return {
                'info': backtest_info,
                'equity_curve': equity_df,
                'trades': trades_df
            }
    
    def delete_backtest(self, backtest_id: int):
        """删除回测记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM trades WHERE backtest_id = ?', (backtest_id,))
            cursor.execute('DELETE FROM equity_curves WHERE backtest_id = ?', (backtest_id,))
            cursor.execute('DELETE FROM backtests WHERE id = ?', (backtest_id,))
            conn.commit()
    
    def get_comparison_data(self, backtest_ids: List[int]) -> pd.DataFrame:
        """获取对比数据"""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(backtest_ids))
            df = pd.read_sql_query(f'''
                SELECT id, name, strategy, total_return, annual_return,
                       max_drawdown, sharpe_ratio, created_at
                FROM backtests
                WHERE id IN ({placeholders})
            ''', conn, params=backtest_ids)
        return df
