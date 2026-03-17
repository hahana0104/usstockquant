"""
Nono's Quant Lab V3.0
个人定制化量化交易系统
支持多语言、主题切换、自定义股票池
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
st.set_page_config(
    page_title="Nono's Quant Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# 导入模块
from config import SP500_TICKERS, FACTOR_CONFIG, BACKTEST_CONFIG
from data.data_loader import DataLoader
from strategies.factors import ThreeFactorModel
from strategies.all_strategies import get_strategy, get_strategy_list
from backtest.engine import VectorizedBacktester
from utils.database import BacktestDatabase
from utils.report_generator import generate_html_report
from utils.realtime_data import RealtimeData
from utils.analysis_generator import generate_backtest_analysis, get_strategy_recommendation
from utils.daily_picker import DailyStockPicker
from utils.watchlist import WatchlistManager
from utils.i18n import get_text, LANGUAGE_NAMES

# ========== 初始化 ==========
def init_session():
    """初始化session状态"""
    if 'db' not in st.session_state:
        st.session_state.db = BacktestDatabase()
    if 'realtime' not in st.session_state:
        st.session_state.realtime = RealtimeData()
    if 'picker' not in st.session_state:
        st.session_state.picker = DailyStockPicker()
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = WatchlistManager()
    if 'settings_loaded' not in st.session_state:
        # 加载用户设置
        st.session_state.theme = st.session_state.watchlist.get_theme()
        st.session_state.language = st.session_state.watchlist.get_language()
        st.session_state.settings_loaded = True

init_session()

# ========== 多语言支持 ==========
def t(key: str) -> str:
    """获取翻译文本"""
    return get_text(key, st.session_state.language)

# ========== 主题CSS ==========
def apply_theme():
    """应用主题样式"""
    is_dark = st.session_state.theme == 'dark'
    
    if is_dark:
        bg_color = "#0e1117"
        text_color = "#fafafa"
        card_bg = "#262730"
        accent_color = "#ff4b4b"
        input_bg = "#1a1a2e"
        border_color = "#333"
    else:
        bg_color = "#ffffff"
        text_color = "#31333F"
        card_bg = "#f0f2f6"
        accent_color = "#667eea"
        input_bg = "#ffffff"
        border_color = "#ddd"
    
    st.markdown(f"""
    <style>
        /* 全局背景 */
        .stApp {{
            background-color: {bg_color};
        }}
        
        /* 文字颜色 */
        .stApp, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, span, div {{
            color: {text_color} !important;
        }}
        
        /* 侧边栏 */
        section[data-testid="stSidebar"] {{
            background-color: {card_bg};
        }}
        
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {{
            color: {text_color} !important;
        }}
        
        /* 标题样式 */
        .main-header {{
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(90deg, {accent_color} 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            text-align: center;
            color: {text_color};
            opacity: 0.8;
            font-size: 1rem;
            margin-bottom: 2rem;
        }}
        
        /* 品牌徽章 */
        .brand-badge {{
            background: linear-gradient(135deg, {accent_color} 0%, #764ba2 100%);
            color: white !important;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 1rem;
        }}
        
        /* 输入框样式 */
        .stTextInput input, .stNumberInput input, .stDateInput input,
        .stTextArea textarea, .stSelectbox select {{
            background-color: {input_bg};
            color: {text_color};
            border: 1px solid {border_color};
        }}
        
        /* 单选按钮文字 */
        .stRadio label {{
            color: {text_color} !important;
        }}
        
        /* 卡片样式 */
        .feature-card {{
            background: {card_bg};
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border: 1px solid {border_color};
        }}
        
        /* 表格样式 */
        .stDataFrame {{
            background-color: {card_bg};
        }}
        
        /* 按钮样式 */
        .stButton button {{
            background-color: {accent_color};
            color: white;
        }}
        
        /* 进度条 */
        .stProgress > div > div {{
            background-color: {accent_color};
        }}
        
        /* 分割线 */
        hr {{
            border-color: {border_color};
        }}
        
        /* 标签 */
        .stTabs [data-baseweb="tab"] {{
            color: {text_color};
        }}
        
        .metric-positive {{ color: #28a745; }}
        .metric-negative {{ color: #dc3545; }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ========== 工具函数 ==========
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

def display_metrics(metrics, initial_capital, final_value):
    """显示绩效指标"""
    total_return = (final_value / initial_capital - 1) * 100 if initial_capital > 0 else 0
    
    cols = st.columns(4)
    with cols[0]:
        st.metric(t('total_return'), f"{total_return:.2f}%")
    with cols[1]:
        st.metric(t('annual_return'), f"{metrics.get('annual_return', 0)*100:.2f}%")
    with cols[2]:
        st.metric(t('max_drawdown'), f"{metrics.get('max_drawdown', 0)*100:.2f}%")
    with cols[3]:
        st.metric(t('sharpe_ratio'), f"{metrics.get('sharpe_ratio', 0):.2f}")

# ========== 页面函数 ==========

def backtest_page():
    """回测页面"""
    st.markdown(f'<p class="main-header">{t("backtest_title")}</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header(t('backtest_config'))
        
        strategy_list = get_strategy_list()
        strategy_options = {s['name']: s['id'] for s in strategy_list}
        selected_strategy_name = st.selectbox(t('select_strategy'), list(strategy_options.keys()), index=0)
        selected_strategy = strategy_options[selected_strategy_name]
        
        strategy_obj = get_strategy(selected_strategy)
        params_config = strategy_obj.get_params_config() or {}
        
        strategy_params = {}
        if params_config:
            st.subheader(t('backtest_config'))
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
        
        st.subheader(t('stock_pool'))
        
        # 股票池选择
        pool_options = ["标普500前30", "标普500前50", t('custom_stocks'), t('menu_watchlist')]
        stock_pool = st.selectbox(t('stock_pool'), pool_options, index=0)
        
        if stock_pool == t('custom_stocks'):
            custom_tickers = st.text_area(t('custom_stocks'), "AAPL, MSFT, NVDA")
            tickers = [t.strip().upper() for t in custom_tickers.split(',') if t.strip()]
        elif stock_pool == t('menu_watchlist'):
            watchlist_tickers = st.session_state.watchlist.get_tickers()
            if watchlist_tickers:
                tickers = watchlist_tickers
                st.info(f"使用股票池中的 {len(tickers)} 只股票")
            else:
                st.warning("股票池为空，请先在'我的股票池'中添加股票")
                tickers = SP500_TICKERS[:30]
        else:
            num = 30 if "30" in stock_pool else 50
            tickers = SP500_TICKERS[:num]
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(t('start_date'), datetime(2022, 1, 1))
        with col2:
            end_date = st.date_input(t('end_date'), datetime.now())
        
        initial_capital = st.number_input(t('initial_capital'), 10000, 1000000, 100000, 10000)
        commission = st.slider(t('commission'), 0.0, 1.0, 0.1, 0.05) / 100
        
        backtest_name = st.text_input(t('placeholder_stock_name'), f"{strategy_obj.name}_{datetime.now().strftime('%m%d')}")
        
        run_button = st.button(t('btn_run'), type="primary", use_container_width=True)
    
    if run_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text(t('status_running'))
            progress_bar.progress(10)
            
            loader = DataLoader()
            price_data = loader.download_prices(
                tickers=tickers,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
            
            if price_data.empty:
                st.error(t('error_no_data'))
                return
            
            progress_bar.progress(30)
            
            rebalance_dates = get_rebalance_dates(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            all_signals = []
            
            if selected_strategy == 'three_factor':
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
                st.error(t('error_no_signal'))
                return
            
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
            
            st.success(f"{t('status_complete')} (#{backtest_id})")
            
            st.subheader(t('metrics_title'))
            display_metrics(results['metrics'], initial_capital, results['final_value'])
            
            st.subheader(t('chart_equity'))
            fig = go.Figure()
            normalized = results['equity_curve']['Equity'] / initial_capital
            fig.add_trace(go.Scatter(
                x=results['equity_curve']['Date'],
                y=normalized,
                mode='lines',
                name='Strategy',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_hline(y=1, line_dash="dash", line_color="gray")
            fig.update_layout(height=500, xaxis_title='Date', yaxis_title='NAV')
            st.plotly_chart(fig, use_container_width=True)
            
            if not results['trades'].empty:
                st.subheader(t('trades_title'))
                st.dataframe(results['trades'], use_container_width=True)
            
            backtest_data = st.session_state.db.get_backtest_detail(backtest_id)
            if backtest_data:
                html_report = generate_html_report(backtest_data)
                st.download_button(
                    label=t('download_report'),
                    data=html_report,
                    file_name=f"report_{backtest_id}.html",
                    mime="text/html"
                )
                
                st.subheader(t('analysis_title'))
                analysis = generate_backtest_analysis(backtest_data)
                st.markdown(analysis)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.info("👈 " + t('backtest_config'))

def history_page():
    """历史记录页面"""
    st.markdown(f'<p class="main-header">{t("history_title")}</p>', unsafe_allow_html=True)
    
    history_df = st.session_state.db.get_backtest_list(limit=50)
    
    if history_df.empty:
        st.info(t('history_empty'))
        return
    
    st.subheader(t('history_title'))
    display_df = history_df.copy()
    display_df['Return'] = (display_df['total_return'] * 100).round(2).astype(str) + '%'
    display_df['Annual'] = (display_df['annual_return'] * 100).round(2).astype(str) + '%'
    display_df['DD'] = (display_df['max_drawdown'] * 100).round(2).astype(str) + '%'
    display_df['Sharpe'] = display_df['sharpe_ratio'].round(2)
    
    st.dataframe(display_df[['id', 'name', 'strategy', 'Return', 'Annual', 'DD', 'Sharpe']], use_container_width=True)
    
    st.subheader("View Details")
    backtest_id = st.number_input("Enter Backtest ID", min_value=1, step=1)
    
    if st.button("View", type="primary"):
        backtest_data = st.session_state.db.get_backtest_detail(backtest_id)
        if backtest_data:
            info = backtest_data['info']
            
            st.subheader(f"📋 {info['name']}")
            cols = st.columns(4)
            with cols[0]:
                st.metric(t('total_return'), f"{info['total_return']*100:.2f}%")
            with cols[1]:
                st.metric(t('annual_return'), f"{info['annual_return']*100:.2f}%")
            with cols[2]:
                st.metric(t('max_drawdown'), f"{info['max_drawdown']*100:.2f}%")
            with cols[3]:
                st.metric(t('sharpe_ratio'), f"{info['sharpe_ratio']:.2f}")
            
            if not backtest_data['equity_curve'].empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=backtest_data['equity_curve']['date'],
                    y=backtest_data['equity_curve']['equity'],
                    mode='lines',
                    name='Equity'
                ))
                fig.update_layout(height=400, title='Equity Curve')
                st.plotly_chart(fig, use_container_width=True)
            
            if not backtest_data['trades'].empty:
                st.subheader(t('trades_title'))
                st.dataframe(backtest_data['trades'], use_container_width=True)
            
            html_report = generate_html_report(backtest_data)
            st.download_button(
                label=t('download_report'),
                data=html_report,
                file_name=f"report_{info['name']}_{info['id']}.html",
                mime="text/html"
            )
        else:
            st.error("Record not found")

def watchlist_page():
    """股票池页面"""
    st.markdown(f'<p class="main-header">{t("watchlist_title")}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{t("watchlist_desc")}</p>', unsafe_allow_html=True)
    
    watchlist_df = st.session_state.watchlist.get_watchlist()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(t('watchlist_add'))
        new_ticker = st.text_input("Stock Ticker", placeholder="AAPL").upper()
        new_name = st.text_input("Stock Name (optional)", placeholder="Apple Inc.")
        new_notes = st.text_area("Notes (optional)", placeholder="Why interested in this stock?")
        
        if st.button(t('btn_add'), type="primary"):
            if new_ticker:
                if st.session_state.watchlist.add_stock(new_ticker, new_name, new_notes):
                    st.success(f"Added {new_ticker} to watchlist!")
                    st.rerun()
                else:
                    st.error("Failed to add stock")
    
    with col2:
        if not watchlist_df.empty:
            st.subheader(f"Stocks ({len(watchlist_df)})")
            for _, row in watchlist_df.iterrows():
                col_ticker, col_btn = st.columns([3, 1])
                with col_ticker:
                    st.write(f"**{row['ticker']}**")
                    if row['name']:
                        st.caption(row['name'])
                with col_btn:
                    if st.button("🗑️", key=f"del_{row['ticker']}"):
                        st.session_state.watchlist.remove_stock(row['ticker'])
                        st.rerun()
        else:
            st.info(t('watchlist_empty'))

def settings_page():
    """设置页面"""
    st.markdown(f'<p class="main-header">{t("settings_title")}</p>', unsafe_allow_html=True)
    
    st.subheader(t('settings_theme'))
    theme_options = {t('theme_light'): 'light', t('theme_dark'): 'dark', t('theme_auto'): 'auto'}
    selected_theme_name = st.radio("Theme", list(theme_options.keys()), 
                                    index=list(theme_options.values()).index(st.session_state.theme))
    new_theme = theme_options[selected_theme_name]
    
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.session_state.watchlist.set_theme(new_theme)
        st.rerun()
    
    st.subheader(t('settings_language'))
    lang_options = LANGUAGE_NAMES
    selected_lang = st.selectbox("Language", list(lang_options.keys()), 
                                  format_func=lambda x: lang_options[x],
                                  index=list(lang_options.keys()).index(st.session_state.language))
    
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.session_state.watchlist.set_language(selected_lang)
        st.rerun()

def main():
    """主函数"""
    with st.sidebar:
        # Logo和标题
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <span class="brand-badge">🧪 Nono's Quant Lab</span>
            <p style="color: #666; font-size: 0.8rem; margin-top: 0.5rem;">{t('app_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 导航菜单
        page = st.radio("Menu", [
            t('menu_backtest'),
            t('menu_history'),
            t('menu_watchlist'),
            t('menu_settings')
        ], index=0)
        
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size: 0.75rem; color: #999;">
            <p><b>{t('footer_v2_features')}</b></p>
            <p>✅ {t('footer_multi_strategy')}</p>
            <p>✅ {t('footer_history')}</p>
            <p>✅ {t('footer_compare')}</p>
            <p>✅ {t('footer_realtime')}</p>
            <p>✅ {t('footer_analysis')}</p>
            <p>✅ {t('footer_picks')}</p>
            <p>✅ {t('footer_fundamentals')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示当前设置
        st.markdown("---")
        st.caption(f"🌐 {LANGUAGE_NAMES[st.session_state.language]} | 🎨 {st.session_state.theme.title()}")
    
    # 页面路由
    if page == t('menu_backtest'):
        backtest_page()
    elif page == t('menu_history'):
        history_page()
    elif page == t('menu_watchlist'):
        watchlist_page()
    elif page == t('menu_settings'):
        settings_page()

if __name__ == "__main__":
    main()
