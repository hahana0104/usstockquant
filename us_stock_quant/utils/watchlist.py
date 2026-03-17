"""
自定义股票池模块
支持添加、删除、保存个人关注的股票
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional
import os
import streamlit as st


class WatchlistManager:
    """股票池管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'data', 'user_settings.db')
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 股票池表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT UNIQUE,
                    name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            ''')
            
            # 用户设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_stock(self, ticker: str, name: str = None, notes: str = None) -> bool:
        """添加股票到股票池"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO watchlist (ticker, name, notes)
                    VALUES (?, ?, ?)
                ''', (ticker.upper(), name, notes))
                conn.commit()
            return True
        except:
            return False
    
    def remove_stock(self, ticker: str) -> bool:
        """从股票池移除股票"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker.upper(),))
                conn.commit()
            return True
        except:
            return False
    
    def get_watchlist(self) -> pd.DataFrame:
        """获取股票池列表"""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('''
                SELECT ticker, name, added_at, notes FROM watchlist
                ORDER BY added_at DESC
            ''', conn)
        return df
    
    def get_tickers(self) -> List[str]:
        """获取股票代码列表"""
        df = self.get_watchlist()
        return df['ticker'].tolist() if not df.empty else []
    
    def is_in_watchlist(self, ticker: str) -> bool:
        """检查股票是否在股票池中"""
        tickers = self.get_tickers()
        return ticker.upper() in tickers
    
    def save_setting(self, key: str, value: str):
        """保存用户设置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now()))
            conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> str:
        """获取用户设置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM user_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
        return row[0] if row else default
    
    def get_theme(self) -> str:
        """获取主题设置"""
        return self.get_setting('theme', 'light')
    
    def set_theme(self, theme: str):
        """设置主题"""
        self.save_setting('theme', theme)
    
    def get_language(self) -> str:
        """获取语言设置"""
        return self.get_setting('language', 'zh_CN')
    
    def set_language(self, lang: str):
        """设置语言"""
        self.save_setting('language', lang)
