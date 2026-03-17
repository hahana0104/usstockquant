#!/usr/bin/env python3
"""
每日选股更新 - 实盘/模拟盘用
每天运行一次，输出当前应该持有的股票
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============ 配置 ============
CONFIG = {
    'num_positions': 20,          # 持仓数量
    'quality_weight': 0.4,        # 质量因子权重
    'value_weight': 0.3,          # 价值因子权重  
    'momentum_weight': 0.3,       # 动量因子权重
    'lookback_days': 126,         # 动量回看天数（6个月）
}

TICKERS = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'UNH', 'JPM',
    'V', 'JNJ', 'XOM', 'WMT', 'MA', 'PG', 'HD', 'CVX', 'MRK', 'LLY',
    'ABBV', 'PEP', 'KO', 'COST', 'TMO', 'ABT', 'MCD', 'ACN', 'WFC', 'DHR',
    'QCOM'  # 新增：高通
]

class DailyStockPicker:
    def __init__(self, config):
        self.config = config
        
    def fetch_data(self):
        """获取最新数据"""
        print(f"📊 获取 {len(TICKERS)} 只股票最新数据...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=200)  # 留够动量计算
        
        prices_data = []
        fundamentals_data = []
        
        for i, ticker in enumerate(TICKERS):
            try:
                stock = yf.Ticker(ticker)
                
                # 价格数据
                hist = stock.history(start=start_date, end=end_date)
                if len(hist) > 0:
                    hist['Ticker'] = ticker
                    hist.reset_index(inplace=True)
                    if hasattr(hist['Date'].dtype, 'tz'):
                        hist['Date'] = hist['Date'].dt.tz_localize(None)
                    prices_data.append(hist)
                
                # 基本面
                info = stock.info
                fundamentals_data.append({
                    'Ticker': ticker,
                    'ROE': info.get('returnOnEquity'),
                    'PE': info.get('trailingPE') or info.get('forwardPE'),
                    'Sector': info.get('sector'),
                    'Price': hist['Close'].iloc[-1] if len(hist) > 0 else None,
                    'Company': info.get('shortName', ticker)
                })
                
                if (i + 1) % 10 == 0:
                    print(f"  ✅ {i+1}/{len(TICKERS)}")
                    
            except Exception as e:
                print(f"  ❌ {ticker}: {e}")
        
        prices_df = pd.concat(prices_data, ignore_index=True) if prices_data else pd.DataFrame()
        fundamentals_df = pd.DataFrame(fundamentals_data).set_index('Ticker') if fundamentals_data else pd.DataFrame()
        
        return prices_df, fundamentals_df
    
    def calc_quality(self, fundamentals):
        """质量因子"""
        roe = fundamentals.get('ROE', pd.Series())
        score = pd.Series(0.5, index=roe.index)
        valid_roe = roe[roe > 0].dropna()
        if len(valid_roe) > 0:
            score.update(valid_roe.rank(pct=True))
        score[roe <= 0] = 0
        return score
    
    def calc_value(self, fundamentals):
        """价值因子"""
        pe = fundamentals.get('PE', pd.Series())
        score = pd.Series(0.5, index=pe.index)
        valid_pe = pe[(pe > 0) & (pe < 100)].dropna()
        if len(valid_pe) > 0:
            score.update(valid_pe.rank(pct=True, ascending=False))
        score[pe <= 0] = 0
        return score
    
    def calc_momentum(self, prices_df):
        """动量因子"""
        pivot = prices_df.pivot(index='Date', columns='Ticker', values='Close')
        
        momentum_scores = {}
        for ticker in pivot.columns:
            series = pivot[ticker].dropna()
            if len(series) >= self.config['lookback_days']:
                ret = (series.iloc[-1] - series.iloc[-self.config['lookback_days']]) / series.iloc[-self.config['lookback_days']]
                momentum_scores[ticker] = ret
        
        momentum = pd.Series(momentum_scores)
        score = momentum.rank(pct=True).fillna(0.5)
        score[momentum < 0] = score[momentum < 0] * 0.5
        return score
    
    def select_stocks(self):
        """选股主函数"""
        prices_df, fundamentals_df = self.fetch_data()
        
        if prices_df.empty or fundamentals_df.empty:
            print("❌ 数据获取失败")
            return None
        
        print("\n🔍 计算三因子...")
        
        # 计算各因子
        quality = self.calc_quality(fundamentals_df)
        value = self.calc_value(fundamentals_df)
        momentum = self.calc_momentum(prices_df)
        
        # 合成
        common = quality.index.intersection(value.index).intersection(momentum.index)
        combined = (
            self.config['quality_weight'] * quality.reindex(common, fill_value=0.5) +
            self.config['value_weight'] * value.reindex(common, fill_value=0.5) +
            self.config['momentum_weight'] * momentum.reindex(common, fill_value=0.5)
        )
        
        # 获取TOP股票
        top_stocks = combined.sort_values(ascending=False).head(self.config['num_positions'])
        
        # 显示全部排名（不只是TOP20）
        all_ranked = combined.sort_values(ascending=False)
        
        print(f"\n📊 全部 {len(all_ranked)} 只股票排名：\n")
        
        # 构建全部结果表
        all_results = []
        for rank, (ticker, score) in enumerate(all_ranked.items(), 1):
            info = fundamentals_df.loc[ticker] if ticker in fundamentals_df.index else {}
            q_score = quality.get(ticker, 0)
            v_score = value.get(ticker, 0)
            m_score = momentum.get(ticker, 0)
            
            # 标记是否入选TOP20
            mark = "✅" if rank <= 20 else "  "
            
            all_results.append({
                '排名': rank,
                '入选': mark,
                '代码': ticker,
                '公司': str(info.get('Company', ''))[:12],
                '现价': f"${info.get('Price', 0):.2f}" if info.get('Price') else '-',
                'PE': f"{info.get('PE', 0):.1f}"[:4] if info.get('PE') else '-',
                'ROE': f"{info.get('ROE', 0)*100:.1f}%"[:5] if info.get('ROE') else '-',
                '质量': f"{q_score:.2f}",
                '价值': f"{v_score:.2f}",
                '动量': f"{m_score:.2f}",
                '综合': f"{score:.3f}"
            })
        
        # 打印全部
        import pandas as pd
        df_all = pd.DataFrame(all_results)
        print(df_all.to_string(index=False))
        
        # 只返回TOP20给后续使用
        top_stocks = all_ranked.head(self.config['num_positions'])
        results = all_results[:20]  # 前20条
        
        return pd.DataFrame(results)
    
    def run(self):
        """运行每日选股"""
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n{'='*60}")
        print(f"📅 每日选股报告 - {today}")
        print(f"{'='*60}\n")
        
        picks = self.select_stocks()
        
        if picks is not None:
            print("📈 今日推荐持仓（按排名）：\n")
            print(picks.to_string(index=False))
            print(f"\n{'='*60}")
            print(f"✅ 共选出 {len(picks)} 只股票")
            print(f"💡 建议：等权配置，每只占 5% 仓位")
            print(f"{'='*60}\n")
            
            # 保存结果
            picks.to_csv(f'daily_picks_{today}.csv', index=False, encoding='utf-8-sig')
            print(f"💾 已保存: daily_picks_{today}.csv")
            
            return picks
        else:
            print("❌ 选股失败")
            return None

def send_feishu_report(picks_df, today):
    """发送报告到Feishu"""
    import subprocess
    try:
        header = f"**每日选股报告 - {today}**\n\n"
        header += "| 排名 | 代码 | 公司 | 现价 | PE | ROE | 得分 |\n"
        header += "|------|------|------|------|-----|------|------|\n"
        
        rows = []
        for _, row in picks_df.iterrows():
            rows.append(f"| {row['排名']} | {row['代码']} | {row['公司']} | {row['现价']} | {row['PE']} | {row['ROE']} | {row['综合得分']} |")
        
        footer = f"\n共选出 {len(picks_df)} 只股票 | 建议：等权配置，每只占 5% 仓位"
        message = header + '\n'.join(rows) + '\n' + footer
        
        cmd = ["openclaw", "message", "send", "--target", "feishu", "--message", message]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return result.returncode == 0
    except Exception as e:
        print(f"Feishu推送错误: {e}")
        return False

if __name__ == '__main__':
    picker = DailyStockPicker(CONFIG)
    picks = picker.run()
    if picks is not None:
        today = datetime.now().strftime('%Y-%m-%d')
        print("\n正在推送到Feishu...")
        if send_feishu_report(picks, today):
            print("[OK] Feishu推送成功")
        else:
            print("[WARN] Feishu推送失败")
