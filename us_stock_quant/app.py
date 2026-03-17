"""
美股量化交易系统 V2.0 - 增强版
支持多策略、历史保存、实时数据、报告导出
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# 导入模块
from config import DATA_CONFIG, FACTOR_CONFIG, STRATEGY_CONFIG, BACKTEST_CONFIG, SP500_TICKERS
from data.data_loader import DataLoader
from strategies.factors import ThreeFactorModel
from strategies.all_strategies import get_strategy, get_strategy_list
from backtest.engine import VectorizedBacktester
from utils.database import BacktestDatabase
from utils.report_generator import generate_html_report
from utils.realtime_data import RealtimeData
from utils.analysis_generator import generate_backtest_analysis, get_strategy_recommendation
from utils.daily_picker import DailyStockPicker

# 页面配置
st.set_page_config(
    page_title="美股量化交易系统 V2.0",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据库
if 'db' not in st.session_state:
    st.session_state.db = BacktestDatabase()

if 'realtime' not in st.session_state:
    st.session_state.realtime = RealtimeData()

if 'picker' not in st.session_state:
    st.session_state.picker = DailyStockPicker()

# CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def get_rebalance_dates(start_date, end_date, freq='M'):
    """生成调仓日期"""
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    adjusted_dates = []
    for d in dates:
        if d.dayofweek == 5:
            d = d + timedelta(days=2)
        elif d.dayofweek == 6:
            d = d + timedelta(days=1)
        adjusted_dates.append(d)
    return adjusted_dates

def display_metrics(metrics, initial_capital, final_value, compact=False):
    """显示绩效指标"""
    total_return = (final_value / initial_capital - 1) * 100 if initial_capital > 0 else 0
    
    if compact:
        cols = st.columns(4)
        with cols[0]:
            st.metric("总收益", f"{total_return:.2f}%")
        with cols[1]:
            st.metric("年化", f"{metrics.get('annual_return', 0)*100:.2f}%")
        with cols[2]:
            st.metric("回撤", f"{metrics.get('max_drawdown', 0)*100:.2f}%")
        with cols[3]:
            st.metric("夏普", f"{metrics.get('sharpe_ratio', 0):.2f}")
    else:
        cols = st.columns(4)
        with cols[0]:
            st.metric("总收益率", f"{total_return:.2f}%")
        with cols[1]:
            st.metric("年化收益", f"{metrics.get('annual_return', 0)*100:.2f}%")
        with cols[2]:
            st.metric("最大回撤", f"{metrics.get('max_drawdown', 0)*100:.2f}%")
        with cols[3]:
            st.metric("夏普比率", f"{metrics.get('sharpe_ratio', 0):.2f}")
        
        cols2 = st.columns(4)
        with cols2[0]:
            st.metric("年化波动", f"{metrics.get('annual_volatility', 0)*100:.2f}%")
        with cols2[1]:
            st.metric("卡尔玛比率", f"{metrics.get('calmar_ratio', 0):.2f}")
        with cols2[2]:
            st.metric("胜率", f"{metrics.get('win_rate', 0)*100:.2f}%")
        with cols2[3]:
            st.metric("盈亏比", f"{metrics.get('profit_factor', 0):.2f}")

# ==================== 页面功能 ====================

def backtest_page():
    """回测页面"""
    st.markdown('<p class="main-header">📈 策略回测</p>', unsafe_allow_html=True)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 策略配置")
        
        # 策略选择
        strategy_list = get_strategy_list()
        strategy_options = {s['name']: s['id'] for s in strategy_list}
        selected_strategy_name = st.selectbox("选择策略", list(strategy_options.keys()), index=0)
        selected_strategy = strategy_options[selected_strategy_name]
        
        # 策略参数
        strategy_obj = get_strategy(selected_strategy)
        params_config = strategy_obj.get_params_config() or {}
        
        strategy_params = {}
        if params_config:
            st.subheader("策略参数")
            for param_name, config in params_config.items():
                if config and isinstance(config, dict):
                    if config.get('type') == 'float':
                        strategy_params[param_name] = st.slider(
                            config.get('label', param_name),
                            float(config.get('min', 0)), 
                            float(config.get('max', 1)), 
                            float(config.get('default', 0.5)),
                            step=0.05
                        )
                    elif config.get('type') == 'int':
                        strategy_params[param_name] = st.slider(
                            config.get('label', param_name),
                            int(config.get('min', 0)), 
                            int(config.get('max', 100)), 
                            int(config.get('default', 10))
                        )
        
        # 其他配置
        st.subheader("回测配置")
        
        stock_pool = st.selectbox("股票池", ["标普500前30", "标普500前50", "自定义"], index=0)
        if stock_pool == "自定义":
            custom_tickers = st.text_area("输入股票代码", "AAPL, MSFT, NVDA")
            tickers = [t.strip().upper() for t in custom_tickers.split(',') if t.strip()]
        else:
            num = 30 if "30" in stock_pool else 50
            tickers = SP500_TICKERS[:num]
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始", datetime(2022, 1, 1))
        with col2:
            end_date = st.date_input("结束", datetime.now())
        
        initial_capital = st.number_input("初始资金", 10000, 1000000, 100000, 10000)
        commission = st.slider("手续费率", 0.0, 1.0, 0.1, 0.05) / 100
        
        backtest_name = st.text_input("回测名称", f"{strategy_obj.name}_{datetime.now().strftime('%m%d')}")
        
        run_button = st.button("🚀 开始回测", type="primary", use_container_width=True)
    
    # 主界面
    if run_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. 下载数据
            status_text.text("正在获取数据...")
            progress_bar.progress(10)
            
            loader = DataLoader()
            price_data = loader.download_prices(
                tickers=tickers,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
            
            if price_data.empty:
                st.error("数据下载失败")
                return
            
            progress_bar.progress(30)
            
            # 2. 生成调仓日期
            rebalance_dates = get_rebalance_dates(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # 3. 生成信号
            status_text.text("正在生成交易信号...")
            progress_bar.progress(40)
            
            all_signals = []
            
            if selected_strategy == 'three_factor':
                # 三因子策略
                fundamentals = loader.download_fundamentals(tickers)
                factor_model = ThreeFactorModel({**FACTOR_CONFIG, **strategy_params})
                
                quality_score = factor_model.calculate_quality_score(fundamentals, price_data) if not fundamentals.empty else pd.Series(0.5, index=tickers)
                value_score = factor_model.calculate_value_score(fundamentals) if not fundamentals.empty else pd.Series(0.5, index=tickers)
                
                for date in rebalance_dates:
                    try:
                        momentum_score = factor_model.calculate_momentum_score(price_data, date)
                        combined = factor_model.combine_factors(quality_score, value_score, momentum_score)
                        selected_stocks = factor_model.select_stocks(combined, 
                            fundamentals if not fundamentals.empty else pd.DataFrame(index=combined.index), 
                            n=strategy_params.get('num_positions', 20))
                        
                        if len(selected_stocks) > 0:
                            weight = 1.0 / len(selected_stocks)
                            signal = pd.Series(weight, index=selected_stocks)
                            signal.name = date
                            all_signals.append(signal)
                    except:
                        continue
            else:
                # 技术指标策略 - 简化版：等权持有所有股票
                for date in rebalance_dates:
                    available_tickers = []
                    for ticker in tickers:
                        try:
                            if ticker in price_data['Close'].columns:
                                prices = price_data['Close'][ticker]
                                if prices.index[0] <= date:
                                    available_tickers.append(ticker)
                        except:
                            continue
                    
                    if available_tickers:
                        weight = 1.0 / len(available_tickers)
                        signal = pd.Series(weight, index=available_tickers)
                        signal.name = date
                        all_signals.append(signal)
            
            if not all_signals:
                st.error("无法生成交易信号")
                return
            
            # 构建信号矩阵
            all_tickers_set = set()
            for s in all_signals:
                all_tickers_set.update(s.index)
            
            signal_data = []
            for s in all_signals:
                row = pd.Series(index=all_tickers_set, dtype=float)
                row[s.index] = s.values
                signal_data.append(row)
            
            signal_df = pd.DataFrame(signal_data, index=[s.name for s in all_signals])
            signal_df.index = pd.to_datetime(signal_df.index)
            signal_df = signal_df.fillna(0)
            
            progress_bar.progress(60)
            
            # 4. 运行回测
            status_text.text("正在运行回测...")
            backtest_config = BACKTEST_CONFIG.copy()
            backtest_config['initial_capital'] = initial_capital
            backtest_config['commission'] = commission
            
            backtester = VectorizedBacktester(backtest_config)
            results = backtester.run(
                price_data=price_data,
                signal_df=signal_df,
                rebalance_dates=rebalance_dates
            )
            
            progress_bar.progress(90)
            
            # 5. 保存到数据库
            backtest_id = st.session_state.db.save_backtest(
                name=backtest_name,
                strategy=selected_strategy_name,
                strategy_params=strategy_params,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                tickers=tickers,
                initial_capital=initial_capital,
                commission=commission,
                metrics=results['metrics'],
                equity_curve=results['equity_curve'],
                trades=results['trades']
            )
            
            progress_bar.progress(100)
            status_text.empty()
            
            # 显示结果
            st.success(f"✅ 回测完成！已保存 (#{backtest_id})")
            
            # 绩效指标
            st.subheader("📊 绩效指标")
            display_metrics(results['metrics'], initial_capital, results['final_value'])
            
            # 图表
            st.subheader("📈 权益曲线")
            fig = go.Figure()
            normalized = results['equity_curve']['Equity'] / initial_capital
            fig.add_trace(go.Scatter(
                x=results['equity_curve']['Date'],
                y=normalized,
                mode='lines',
                name='策略',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_hline(y=1, line_dash="dash", line_color="gray")
            fig.update_layout(height=500, xaxis_title='日期', yaxis_title='净值')
            st.plotly_chart(fig, use_container_width=True)
            
            # 交易记录
            if not results['trades'].empty:
                st.subheader("📝 交易记录")
                st.dataframe(results['trades'], use_container_width=True)
            
            # 下载报告
            backtest_data = st.session_state.db.get_backtest_detail(backtest_id)
            if backtest_data:
                html_report = generate_html_report(backtest_data)
                st.download_button(
                    label="📥 下载报告 (HTML)",
                    data=html_report,
                    file_name=f"report_{backtest_id}.html",
                    mime="text/html"
                )
            
        except Exception as e:
            st.error(f"回测出错: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("👈 在左侧配置参数，点击「开始回测」")

def history_page():
    """历史记录页面"""
    st.markdown('<p class="main-header">📚 回测历史</p>', unsafe_allow_html=True)
    
    history_df = st.session_state.db.get_backtest_list(limit=50)
    
    if history_df.empty:
        st.info("暂无回测记录")
        return
    
    st.subheader("回测记录列表")
    display_df = history_df.copy()
    display_df['总收益'] = (display_df['total_return'] * 100).round(2).astype(str) + '%'
    display_df['年化'] = (display_df['annual_return'] * 100).round(2).astype(str) + '%'
    display_df['回撤'] = (display_df['max_drawdown'] * 100).round(2).astype(str) + '%'
    display_df['夏普'] = display_df['sharpe_ratio'].round(2)
    
    st.dataframe(display_df[['id', 'name', 'strategy', '总收益', '年化', '回撤', '夏普']], use_container_width=True)
    
    # 查看详情
    st.subheader("查看详情")
    backtest_id = st.number_input("输入回测ID", min_value=1, step=1)
    
    if st.button("查看详情", type="primary"):
        backtest_data = st.session_state.db.get_backtest_detail(backtest_id)
        if backtest_data:
            info = backtest_data['info']
            
            st.subheader(f"📋 {info['name']}")
            cols = st.columns(4)
            with cols[0]:
                st.metric("总收益", f"{info['total_return']*100:.2f}%")
            with cols[1]:
                st.metric("年化收益", f"{info['annual_return']*100:.2f}%")
            with cols[2]:
                st.metric("最大回撤", f"{info['max_drawdown']*100:.2f}%")
            with cols[3]:
                st.metric("夏普比率", f"{info['sharpe_ratio']:.2f}")
            
            if not backtest_data['equity_curve'].empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=backtest_data['equity_curve']['date'],
                    y=backtest_data['equity_curve']['equity'],
                    mode='lines',
                    name='权益'
                ))
                fig.update_layout(height=400, title='权益曲线')
                st.plotly_chart(fig, use_container_width=True)
            
            if not backtest_data['trades'].empty:
                st.subheader("📝 交易记录")
                st.dataframe(backtest_data['trades'], use_container_width=True)
            
            html_report = generate_html_report(backtest_data)
            st.download_button(
                label="📥 下载报告",
                data=html_report,
                file_name=f"report_{info['name']}_{info['id']}.html",
                mime="text/html"
            )
        else:
            st.error("未找到该回测记录")

def compare_page():
    """策略对比页面"""
    st.markdown('<p class="main-header">⚖️ 策略对比</p>', unsafe_allow_html=True)
    
    history_df = st.session_state.db.get_backtest_list(limit=100)
    
    if len(history_df) < 2:
        st.info("需要至少2条回测记录才能对比")
        return
    
    options = {f"#{row['id']} {row['name']}": row['id'] for _, row in history_df.iterrows()}
    selected = st.multiselect("选择要对比的回测", list(options.keys()), default=list(options.keys())[:2])
    selected_ids = [options[s] for s in selected]
    
    if len(selected_ids) >= 2 and st.button("开始对比", type="primary"):
        equity_curves = {}
        names = {}
        comparison_data = []
        
        for backtest_id in selected_ids:
            data = st.session_state.db.get_backtest_detail(backtest_id)
            if data:
                info = data['info']
                names[backtest_id] = info['name']
                equity_curves[backtest_id] = data['equity_curve']
                comparison_data.append({
                    '名称': info['name'],
                    '策略': info['strategy'],
                    '总收益': f"{info['total_return']*100:.2f}%",
                    '年化': f"{info['annual_return']*100:.2f}%",
                    '回撤': f"{info['max_drawdown']*100:.2f}%",
                    '夏普': f"{info['sharpe_ratio']:.2f}",
                })
        
        st.subheader("📊 绩效对比")
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
        
        st.subheader("📈 权益曲线对比")
        fig = go.Figure()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, (backtest_id, equity_df) in enumerate(equity_curves.items()):
            if not equity_df.empty:
                normalized = equity_df['equity'] / equity_df['equity'].iloc[0]
                fig.add_trace(go.Scatter(
                    x=equity_df['date'],
                    y=normalized,
                    mode='lines',
                    name=names.get(backtest_id, f'策略{i+1}'),
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        fig.add_hline(y=1, line_dash="dash", line_color="gray")
        fig.update_layout(height=500, xaxis_title='日期', yaxis_title='净值')
        st.plotly_chart(fig, use_container_width=True)

def realtime_page():
    """实时数据页面"""
    st.markdown('<p class="main-header">📡 实时行情</p>', unsafe_allow_html=True)
    
    st.subheader("🌍 大盘指数")
    indices_df = st.session_state.realtime.get_market_indices()
    if not indices_df.empty:
        cols = st.columns(len(indices_df))
        for idx, (_, row) in enumerate(indices_df.iterrows()):
            with cols[idx]:
                st.metric(row['指数'], f"{row['现价']:.2f}", f"{row['涨跌']:.2f}%")
    
    st.subheader("🔥 热门股票")
    hot_df = st.session_state.realtime.get_hot_stocks(limit=10)
    if not hot_df.empty:
        st.dataframe(hot_df, use_container_width=True, hide_index=True)
    
    st.subheader("🔍 股票详情查询")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("输入股票代码", "AAPL", key="ticker_input").upper()
    with col2:
        st.write("")
        st.write("")
        search_clicked = st.button("🔍 查询", type="primary", use_container_width=True)
    
    if search_clicked or 'last_quote' in st.session_state:
        if search_clicked:
            with st.spinner("正在获取数据..."):
                quote = st.session_state.realtime.get_stock_quote(ticker)
                if quote and 'error' not in quote:
                    st.session_state.last_quote = quote
                    st.session_state.last_ticker = ticker
                else:
                    st.error(f"无法获取 {ticker} 的数据")
                    return
        
        if 'last_quote' in st.session_state:
            q = st.session_state.last_quote
            ticker_name = st.session_state.get('last_ticker', ticker)
            
            # 标题
            st.markdown(f"### 📊 {q.get('name', ticker_name)} ({ticker_name})")
            if q.get('sector') and q.get('sector') != 'N/A':
                st.caption(f"🏢 {q.get('sector')} | {q.get('industry', 'N/A')}")
            
            # 价格卡片
            st.markdown("#### 💰 价格信息")
            cols = st.columns(5)
            with cols[0]:
                price_color = "normal" if q.get('change', 0) >= 0 else "inverse"
                st.metric(
                    "当前价格", 
                    f"${q.get('price', 0):.2f}",
                    f"{q.get('change', 0):.2f} ({q.get('change_pct', 0):.2f}%)",
                    delta_color=price_color
                )
            with cols[1]:
                st.metric("今日开盘", f"${q.get('open', 0):.2f}")
            with cols[2]:
                st.metric("今日最高", f"${q.get('high', 0):.2f}")
            with cols[3]:
                st.metric("今日最低", f"${q.get('low', 0):.2f}")
            with cols[4]:
                volume = q.get('volume', 0)
                avg_volume = q.get('avg_volume', 0)
                vol_vs_avg = ((volume / avg_volume - 1) * 100) if avg_volume > 0 else 0
                st.metric("成交量", f"{volume/1e6:.2f}M", f"{vol_vs_avg:.1f}%")
            
            # 估值指标
            st.markdown("#### 📈 估值指标")
            val_cols = st.columns(6)
            
            def format_ratio(val, is_percent=False):
                if val is None or val == 0:
                    return "N/A"
                if is_percent:
                    return f"{val*100:.1f}%"
                return f"{val:.2f}"
            
            with val_cols[0]:
                st.metric("市盈率 (PE)", format_ratio(q.get('pe_ratio')))
            with val_cols[1]:
                st.metric("前瞻PE", format_ratio(q.get('forward_pe')))
            with val_cols[2]:
                st.metric("市净率 (PB)", format_ratio(q.get('pb_ratio')))
            with val_cols[3]:
                st.metric("市销率 (PS)", format_ratio(q.get('ps_ratio')))
            with val_cols[4]:
                st.metric("PEG", format_ratio(q.get('peg_ratio')))
            with val_cols[5]:
                market_cap = q.get('market_cap', 0)
                if market_cap >= 1e12:
                    cap_str = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    cap_str = f"${market_cap/1e9:.1f}B"
                else:
                    cap_str = f"${market_cap/1e6:.1f}M"
                st.metric("市值", cap_str)
            
            # 盈利能力
            st.markdown("#### 💵 盈利能力")
            profit_cols = st.columns(5)
            with profit_cols[0]:
                roe = q.get('roe')
                st.metric("ROE", format_ratio(roe, True) if roe else "N/A")
            with profit_cols[1]:
                roa = q.get('roa')
                st.metric("ROA", format_ratio(roa, True) if roa else "N/A")
            with profit_cols[2]:
                margin = q.get('profit_margin')
                st.metric("净利率", format_ratio(margin, True) if margin else "N/A")
            with profit_cols[3]:
                growth = q.get('revenue_growth')
                st.metric("收入增长", format_ratio(growth, True) if growth else "N/A")
            with profit_cols[4]:
                earn_growth = q.get('earnings_growth')
                st.metric("盈利增长", format_ratio(earn_growth, True) if earn_growth else "N/A")
            
            # 财务健康
            st.markdown("#### 🏦 财务健康")
            fin_cols = st.columns(4)
            with fin_cols[0]:
                debt = q.get('debt_to_equity')
                st.metric("负债权益比", format_ratio(debt) if debt else "N/A")
            with fin_cols[1]:
                current = q.get('current_ratio')
                st.metric("流动比率", format_ratio(current) if current else "N/A")
            with fin_cols[2]:
                cash = q.get('total_cash', 0)
                st.metric("现金", f"${cash/1e9:.1f}B" if cash else "N/A")
            with fin_cols[3]:
                total_debt = q.get('total_debt', 0)
                st.metric("总债务", f"${total_debt/1e9:.1f}B" if total_debt else "N/A")
            
            # 股息信息
            if q.get('dividend_yield') or q.get('dividend_rate'):
                st.markdown("#### 💰 股息信息")
                div_cols = st.columns(3)
                with div_cols[0]:
                    div_yield = q.get('dividend_yield')
                    st.metric("股息率", format_ratio(div_yield, True) if div_yield else "N/A")
                with div_cols[1]:
                    div_rate = q.get('dividend_rate')
                    st.metric("每股股息", f"${div_rate:.2f}" if div_rate else "N/A")
                with div_cols[2]:
                    payout = q.get('payout_ratio')
                    st.metric("派息率", format_ratio(payout, True) if payout else "N/A")
            
            # 技术指标
            st.markdown("#### 📊 技术指标")
            tech_cols = st.columns(5)
            with tech_cols[0]:
                if q.get('week_52_high'):
                    pct_from_high = ((q.get('price', 0) / q.get('week_52_high', 1) - 1) * 100)
                    st.metric("52周高点", f"${q.get('week_52_high'):.2f}", f"{pct_from_high:.1f}%")
                else:
                    st.metric("52周高点", "N/A")
            with tech_cols[1]:
                if q.get('week_52_low'):
                    pct_from_low = ((q.get('price', 0) / q.get('week_52_low', 1) - 1) * 100)
                    st.metric("52周低点", f"${q.get('week_52_low'):.2f}", f"+{pct_from_low:.1f}%")
                else:
                    st.metric("52周低点", "N/A")
            with tech_cols[2]:
                st.metric("MA20", f"${q.get('ma20', 0):.2f}" if q.get('ma20') else "N/A")
            with tech_cols[3]:
                st.metric("MA50", f"${q.get('ma50', 0):.2f}" if q.get('ma50') else "N/A")
            with tech_cols[4]:
                st.metric("Beta", f"{q.get('beta', 0):.2f}" if q.get('beta') else "N/A")
            
            # 分析师预期
            if q.get('target_mean') or q.get('recommendation'):
                st.markdown("#### 👨‍💼 分析师预期")
                analyst_cols = st.columns(4)
                with analyst_cols[0]:
                    target = q.get('target_mean')
                    if target and q.get('price', 0) > 0:
                        upside = ((target / q.get('price') - 1) * 100)
                        st.metric("目标价", f"${target:.2f}", f"{upside:.1f}%")
                    else:
                        st.metric("目标价", "N/A")
                with analyst_cols[1]:
                    st.metric("最高目标", f"${q.get('target_high', 0):.2f}" if q.get('target_high') else "N/A")
                with analyst_cols[2]:
                    st.metric("最低目标", f"${q.get('target_low', 0):.2f}" if q.get('target_low') else "N/A")
                with analyst_cols[3]:
                    rec = q.get('recommendation', 'N/A')
                    rec_emoji = {"buy": "🟢", "strong_buy": "🟢", "hold": "🟡", "sell": "🔴", "strong_sell": "🔴"}
                    st.metric("评级", f"{rec_emoji.get(rec, '⚪')} {rec.upper()}")
            
            st.caption(f"⏰ 数据更新时间: {q.get('timestamp', 'N/A')}")

def main():
    """主函数"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #667eea;">📈 QuantTrader Pro</h2>
            <p style="color: #666; font-size: 0.8rem;">V2.0 增强版</p>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.radio("功能菜单", ["策略回测", "回测历史", "策略对比", "实时行情"], index=0)
        
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.75rem; color: #999;">
            <p><b>V2.0 新特性</b></p>
            <p>✅ 多策略支持</p>
            <p>✅ 历史记录保存</p>
            <p>✅ 策略对比分析</p>
            <p>✅ 实时行情监控</p>
        </div>
        """, unsafe_allow_html=True)
    
    if page == "策略回测":
        backtest_page()
    elif page == "回测历史":
        history_page()
    elif page == "策略对比":
        compare_page()
    elif page == "实时行情":
        realtime_page()

if __name__ == "__main__":
    main()
