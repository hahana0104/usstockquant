"""
回测分析报告生成器
自动解读回测结果，给出专业分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


def generate_backtest_analysis(backtest_data: dict) -> str:
    """生成回测分析报告"""
    info = backtest_data['info']
    equity_curve = backtest_data['equity_curve']
    trades = backtest_data['trades']
    
    analysis = []
    
    # 1. 收益分析
    total_return = info.get('total_return', 0) * 100
    annual_return = info.get('annual_return', 0) * 100
    
    if total_return > 50:
        performance = "表现优异"
    elif total_return > 20:
        performance = "表现良好"
    elif total_return > 0:
        performance = "小幅盈利"
    elif total_return > -20:
        performance = "小幅亏损"
    else:
        performance = "表现较差"
    
    analysis.append(f"## 📊 策略总体表现：{performance}")
    analysis.append(f"")
    analysis.append(f"回测期间总收益率为 **{total_return:.2f}%**，年化收益 **{annual_return:.2f}%**。")
    
    # 2. 风险分析
    max_dd = info.get('max_drawdown', 0) * 100
    sharpe = info.get('sharpe_ratio', 0)
    volatility = info.get('annual_volatility', 0) * 100
    
    analysis.append(f"")
    analysis.append(f"## ⚠️ 风险评估")
    
    if max_dd > -30:
        risk_level = "较低"
    elif max_dd > -50:
        risk_level = "中等"
    else:
        risk_level = "较高"
    
    analysis.append(f"- **最大回撤**：{max_dd:.2f}%（风险水平：{risk_level}）")
    analysis.append(f"- **夏普比率**：{sharpe:.2f}")
    analysis.append(f"- **年化波动率**：{volatility:.2f}%")
    
    if sharpe > 1.5:
        analysis.append(f"- 💡 夏普比率优秀，风险调整后收益很好")
    elif sharpe > 1:
        analysis.append(f"- 💡 夏普比率良好，风险调整后收益合理")
    else:
        analysis.append(f"- ⚠️ 夏普比率偏低，承担的风险可能没有得到足够补偿")
    
    # 3. 图表解读
    analysis.append(f"")
    analysis.append(f"## 📈 权益曲线解读")
    
    if not equity_curve.empty:
        # 计算阶段表现
        equity_values = equity_curve['equity'].values
        dates = pd.to_datetime(equity_curve['date'])
        
        # 找出最大回撤区间
        peak_idx = np.argmax(np.maximum.accumulate(equity_values) - equity_values)
        peak_value = np.maximum.accumulate(equity_values)[peak_idx]
        
        # 近期趋势
        if len(equity_values) >= 20:
            recent_20 = equity_values[-20:]
            early_20 = equity_values[:20]
            recent_return = (recent_20[-1] / recent_20[0] - 1) * 100
            overall_trend = "上升" if equity_values[-1] > equity_values[0] else "下降"
            
            analysis.append(f"- 整体趋势：**{overall_trend}**")
            analysis.append(f"- 近20个交易日收益：**{recent_return:.2f}%**")
            
            # 波动性分析
            returns = np.diff(equity_values) / equity_values[:-1]
            volatility = np.std(returns) * np.sqrt(252) * 100
            
            if volatility < 15:
                vol_desc = "低波动"
            elif volatility < 25:
                vol_desc = "中等波动"
            else:
                vol_desc = "高波动"
            
            analysis.append(f"- 波动特征：**{vol_desc}**（年化波动率 {volatility:.1f}%）")
    
    # 4. 交易分析
    analysis.append(f"")
    analysis.append(f"## 💼 交易分析")
    
    if not trades.empty:
        num_trades = len(trades)
        buy_trades = len(trades[trades['action'] == 'BUY'])
        sell_trades = len(trades[trades['action'] == 'SELL'])
        
        analysis.append(f"- 总交易次数：**{num_trades}** 次")
        analysis.append(f"- 买入次数：{buy_trades} 次")
        analysis.append(f"- 卖出次数：{sell_trades} 次")
        
        if num_trades > 0:
            avg_trade_size = trades['amount'].abs().mean()
            analysis.append(f"- 平均交易金额：${avg_trade_size:,.2f}")
    else:
        analysis.append(f"- 本回测期间没有产生交易")
    
    # 5. 策略建议
    analysis.append(f"")
    analysis.append(f"## 💡 策略建议")
    
    suggestions = []
    
    if max_dd < -40:
        suggestions.append("- ⚠️ **风险控制**：最大回撤超过40%，建议加强止损机制或降低仓位")
    
    if sharpe < 0.5:
        suggestions.append("- ⚠️ **收益优化**：夏普比率偏低，建议优化选股逻辑或调整策略参数")
    
    if volatility > 30:
        suggestions.append("- 📊 **波动管理**：波动率较高，适合风险偏好型投资者")
    elif volatility < 10:
        suggestions.append("- 📊 **稳定策略**：波动率较低，适合稳健型投资者")
    
    if total_return < 0:
        suggestions.append("- 🔍 **策略审视**：策略在回测期间亏损，建议检查策略逻辑或更换股票池")
    
    if total_return > 50 and sharpe > 1:
        suggestions.append("- ✅ **策略优秀**：收益和风险调整后收益都很好，值得实盘测试")
    
    if not suggestions:
        suggestions.append("- ✅ 策略表现中规中矩，可以继续观察")
    
    analysis.extend(suggestions)
    
    # 6. 与基准对比建议
    analysis.append(f"")
    analysis.append(f"## 🎯 下一步行动建议")
    
    if sharpe > 1 and max_dd > -30:
        analysis.append("1. ✅ 策略表现良好，建议先用小资金实盘测试")
        analysis.append("2. 📊 持续监控策略表现，设置止损线")
        analysis.append("3. 🔄 定期回顾和调整策略参数")
    elif total_return > 0:
        analysis.append("1. 📝 策略有盈利但风险较高，建议优化后再实盘")
        analysis.append("2. 🔧 可以尝试调整参数，降低最大回撤")
        analysis.append("3. 📚 学习更多风险管理方法")
    else:
        analysis.append("1. 🔍 重新审视策略逻辑，检查是否有漏洞")
        analysis.append("2. 📖 建议先用模拟盘观察更长时间")
        analysis.append("3. 💡 考虑更换股票池或调整策略类型")
    
    return "\n".join(analysis)


def get_strategy_recommendation(strategy_type: str, performance: dict) -> str:
    """根据策略类型和表现给出建议"""
    recommendations = {
        'three_factor': {
            'name': '三因子策略',
            'suitable': '适合中长期投资，偏好价值+成长风格',
            'risk': '中等风险，需要承受一定的回撤',
            'adjustment': '可以调整三个因子的权重来适应不同市场环境'
        },
        'ma_cross': {
            'name': '均线策略',
            'suitable': '适合趋势明显的市场',
            'risk': '在震荡市可能频繁交易导致亏损',
            'adjustment': '可以调整均线周期，长期均线适合牛市，短期均线适合震荡市'
        },
        'rsi': {
            'name': 'RSI策略',
            'suitable': '适合震荡市场，高抛低吸',
            'risk': '在强趋势市场可能过早离场',
            'adjustment': '可以调整超买超卖阈值'
        },
        'macd': {
            'name': 'MACD策略',
            'suitable': '适合捕捉中期趋势',
            'risk': '信号可能滞后，需要配合止损',
            'adjustment': '可以调整快慢线周期'
        },
        'bollinger': {
            'name': '布林带策略',
            'suitable': '适合波动性较大的股票',
            'risk': '突破上下轨后可能继续沿趋势运行',
            'adjustment': '可以调整布林带宽度和周期'
        }
    }
    
    return recommendations.get(strategy_type, {})
