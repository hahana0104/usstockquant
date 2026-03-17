"""
快速回测分析 - 简化版Web界面
用于快速测试单个股票的策略
"""

import sys
sys.path.insert(0, r'C:\Users\nono\.openclaw\workspace\us_stock_quant')

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="快速回测分析",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ 快速回测分析")
st.markdown("快速测试单个股票的技术指标策略")

# 输入参数
col1, col2, col3 = st.columns(3)
with col1:
    ticker = st.text_input("股票代码", "AAPL").upper()
with col2:
    period = st.selectbox("数据周期", ["1y", "2y", "3y", "5y"], index=2)
with col3:
    strategy = st.selectbox("策略类型", ["MA均线", "RSI超买超卖", "MACD金叉死叉"], index=0)

if st.button("🚀 开始分析", type="primary"):
    with st.spinner("正在获取数据并分析..."):
        try:
            # 下载数据
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                st.error(f"无法获取 {ticker} 的数据")
                st.stop()
            
            # 计算指标
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA50'] = df['Close'].rolling(50).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9).mean()
            
            # 生成交易信号
            if strategy == "MA均线":
                df['Position'] = np.where(df['Close'] > df['MA20'], 1, 0)
                entry_desc = "价格上穿MA20买入，下穿卖出"
            elif strategy == "RSI超买超卖":
                df['Position'] = np.where(df['RSI'] < 30, 1, np.where(df['RSI'] > 70, 0, np.nan))
                df['Position'] = df['Position'].fillna(method='ffill').fillna(0)
                entry_desc = "RSI<30买入，RSI>70卖出"
            else:  # MACD
                df['Position'] = np.where(df['MACD'] > df['Signal'], 1, 0)
                entry_desc = "MACD上穿信号线买入，下穿卖出"
            
            df['Position'] = df['Position'].shift(1).fillna(0)
            df['Returns'] = df['Close'].pct_change()
            df['Strategy'] = df['Position'] * df['Returns']
            
            # 计算累计收益
            df['Cumulative_Market'] = (1 + df['Returns']).cumprod()
            df['Cumulative_Strategy'] = (1 + df['Strategy']).cumprod()
            
            # 绩效指标
            total_return = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100
            market_return = (df['Cumulative_Market'].iloc[-1] - 1) * 100
            
            strategy_returns = df['Strategy'].dropna()
            volatility = strategy_returns.std() * np.sqrt(252) * 100
            sharpe = (strategy_returns.mean() * 252 - 0.02) / (strategy_returns.std() * np.sqrt(252)) if strategy_returns.std() > 0 else 0
            
            # 最大回撤
            cummax = df['Cumulative_Strategy'].cummax()
            drawdown = (df['Cumulative_Strategy'] - cummax) / cummax
            max_dd = drawdown.min() * 100
            
            # 显示结果
            st.success(f"✅ {ticker} 分析完成")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                delta_color = "normal" if total_return > 0 else "inverse"
                st.metric("策略收益率", f"{total_return:.2f}%", delta=f"vs 市场 {market_return:.2f}%", delta_color=delta_color)
            with col2:
                st.metric("年化波动率", f"{volatility:.2f}%")
            with col3:
                st.metric("最大回撤", f"{max_dd:.2f}%")
            with col4:
                st.metric("夏普比率", f"{sharpe:.2f}")
            
            st.caption(f"入场规则: {entry_desc}")
            
            # 价格图表
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.6, 0.2, 0.2],
                subplot_titles=(f'{ticker} 价格与策略', 'RSI', '累计收益对比')
            )
            
            # 主图 - 价格和均线
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'],
                mode='lines', name='收盘价',
                line=dict(color='#1f77b4', width=2)
            ), row=1, col=1)
            
            if strategy == "MA均线":
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['MA20'],
                    mode='lines', name='MA20',
                    line=dict(color='orange', width=1.5)
                ), row=1, col=1)
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['MA50'],
                    mode='lines', name='MA50',
                    line=dict(color='red', width=1.5)
                ), row=1, col=1)
            
            # 标记买卖信号
            buy_signals = df[df['Position'].diff() > 0].index
            sell_signals = df[df['Position'].diff() < 0].index
            
            fig.add_trace(go.Scatter(
                x=buy_signals, y=df.loc[buy_signals, 'Close'],
                mode='markers', name='买入',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=sell_signals, y=df.loc[sell_signals, 'Close'],
                mode='markers', name='卖出',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ), row=1, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(
                x=df.index, y=df['RSI'],
                mode='lines', name='RSI',
                line=dict(color='purple', width=1.5)
            ), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # 累计收益
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Cumulative_Strategy'],
                mode='lines', name='策略',
                line=dict(color='blue', width=2)
            ), row=3, col=1)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Cumulative_Market'],
                mode='lines', name='市场(买入持有)',
                line=dict(color='gray', width=1.5, dash='dash')
            ), row=3, col=1)
            
            fig.update_layout(
                height=800,
                showlegend=True,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 交易统计
            trades = df[df['Position'].diff() != 0]
            num_trades = len(trades)
            
            st.subheader("📊 交易统计")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总交易次数", num_trades)
            with col2:
                days_in_market = (df['Position'] > 0).sum()
                st.metric("持仓天数", f"{days_in_market} ({days_in_market/len(df)*100:.1f}%)")
            with col3:
                win_days = (df['Strategy'] > 0).sum()
                st.metric("盈利天数", f"{win_days} ({win_days/len(df)*100:.1f}%)")
            
        except Exception as e:
            st.error(f"分析出错: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
else:
    st.info("👆 输入股票代码并点击「开始分析」")
