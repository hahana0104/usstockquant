# 📈 美股三因子量化交易系统

基于 Quality + Value + Momentum 三因子模型的量化回测系统。

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## ✨ 功能特性

- **策略回测**: 支持自定义股票池、时间范围、因子权重
- **可视化分析**: 权益曲线、回撤分析、月度收益热力图
- **绩效指标**: 收益率、夏普比率、最大回撤、胜率等
- **单股票分析**: 实时技术指标和基本面数据

## 🚀 在线体验

部署到 Streamlit Cloud 后，访问链接:
```
https://your-app-name.streamlit.app
```

## 📊 三因子策略

| 因子 | 权重 | 说明 |
|------|------|------|
| **Quality** | 40% | ROE > 15%，盈利稳定性 |
| **Value** | 30% | PE/PB 低于行业中位数 |
| **Momentum** | 30% | 6个月价格趋势 |

## 🛠️ 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

访问 http://localhost:8501

## 📁 项目结构

```
├── app.py              # Streamlit 主应用
├── config.py           # 策略配置
├── backtest/           # 回测引擎
├── strategies/         # 三因子模型
└── data/               # 数据获取模块
```

## 📌 免责声明

本系统仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。

## 📄 License

MIT License
