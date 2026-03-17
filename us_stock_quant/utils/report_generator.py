"""
报告生成模块 - 导出PDF报告
"""

import base64
from io import BytesIO
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def generate_html_report(backtest_data: dict) -> str:
    """生成HTML格式的回测报告"""
    info = backtest_data['info']
    equity_curve = backtest_data['equity_curve']
    trades = backtest_data['trades']
    
    # 生成权益曲线图
    fig = go.Figure()
    if not equity_curve.empty:
        fig.add_trace(go.Scatter(
            x=equity_curve['date'],
            y=equity_curve['equity'],
            mode='lines',
            name='权益',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title='权益曲线',
            xaxis_title='日期',
            yaxis_title='权益 ($)',
            height=400
        )
    
    # 转换为base64图片
    img_bytes = fig.to_image(format="png", scale=2)
    img_base64 = base64.b64encode(img_bytes).decode()
    
    # 交易统计
    num_trades = len(trades)
    buy_trades = len(trades[trades['action'] == 'BUY']) if not trades.empty else 0
    sell_trades = len(trades[trades['action'] == 'SELL']) if not trades.empty else 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>回测报告 - {info.get('name', '未命名')}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #1f77b4;
            }}
            .metric-label {{
                color: #666;
                margin-top: 5px;
            }}
            .section {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #333;
                border-bottom: 2px solid #1f77b4;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            .positive {{ color: #28a745; }}
            .negative {{ color: #dc3545; }}
            .chart {{
                text-align: center;
                margin: 20px 0;
            }}
            .chart img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 回测报告</h1>
            <p>{info.get('name', '未命名策略')} | {info.get('start_date', '')} 至 {info.get('end_date', '')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value {'positive' if info.get('total_return', 0) > 0 else 'negative'}">{info.get('total_return', 0)*100:.2f}%</div>
                <div class="metric-label">总收益率</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{info.get('annual_return', 0)*100:.2f}%</div>
                <div class="metric-label">年化收益</div>
            </div>
            <div class="metric-card">
                <div class="metric-value negative">{info.get('max_drawdown', 0)*100:.2f}%</div>
                <div class="metric-label">最大回撤</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{info.get('sharpe_ratio', 0):.2f}</div>
                <div class="metric-label">夏普比率</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 权益曲线</h2>
            <div class="chart">
                <img src="data:image/png;base64,{img_base64}" alt="权益曲线">
            </div>
        </div>
        
        <div class="section">
            <h2>📋 策略配置</h2>
            <table>
                <tr><th>配置项</th><th>值</th></tr>
                <tr><td>策略类型</td><td>{info.get('strategy', '未知')}</td></tr>
                <tr><td>初始资金</td><td>${info.get('initial_capital', 0):,.2f}</td></tr>
                <tr><td>手续费率</td><td>{info.get('commission', 0)*100:.2f}%</td></tr>
                <tr><td>股票数量</td><td>{len(info.get('tickers', []))}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>💼 交易统计</h2>
            <table>
                <tr><th>统计项</th><th>值</th></tr>
                <tr><td>总交易次数</td><td>{num_trades}</td></tr>
                <tr><td>买入次数</td><td>{buy_trades}</td></tr>
                <tr><td>卖出次数</td><td>{sell_trades}</td></tr>
            </table>
        </div>
        
        {'<div class="section"><h2>📝 交易记录</h2><table><tr><th>日期</th><th>股票</th><th>操作</th><th>数量</th><th>价格</th></tr>' + ''.join([f"<tr><td>{row['date']}</td><td>{row['ticker']}</td><td>{row['action']}</td><td>{row['shares']}</td><td>${row['price']:.2f}</td></tr>" for _, row in trades.head(20).iterrows()]) + '</table></div>' if not trades.empty else ''}
        
        <div class="footer">
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>美股三因子量化交易系统</p>
        </div>
    </body>
    </html>
    """
    
    return html


def get_download_link(html_content: str, filename: str = "report.html") -> str:
    """生成下载链接"""
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'data:text/html;base64,{b64}'
    return href
