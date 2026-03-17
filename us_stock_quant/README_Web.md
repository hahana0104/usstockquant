# 美股三因子量化交易系统 - Web版

基于Streamlit的可视化量化交易平台

## 🚀 快速启动

### 方式1: 双击启动 (推荐)
直接双击 `启动交易系统.bat` 文件

### 方式2: 命令行启动
```bash
cd us_stock_quant
python run_web.py
```

或

```bash
cd us_stock_quant
streamlit run app.py
```

### 方式3: 快速分析
```bash
streamlit run quick_analysis.py
```

## 📁 文件说明

```
us_stock_quant/
├── app.py                 # 主应用 (完整功能)
├── quick_analysis.py      # 快速分析 (单股票)
├── run_web.py             # Python启动器
├── 启动交易系统.bat       # Windows批处理启动器
├── requirements.txt       # 依赖包列表
├── README_Web.md          # 本文件
│
├── backtest/              # 回测引擎
│   └── engine.py
├── strategies/            # 策略模块
│   └── factors.py
├── data/                  # 数据加载
│   └── data_loader.py
└── config.py              # 配置文件
```

## ✨ 功能特性

### 1. 策略回测
- **股票池选择**: 标普500前30/50/全部，或自定义
- **时间范围**: 灵活选择回测起止日期
- **策略参数**: 
  - 持仓数量 (5-50只)
  - 调仓频率 (月/周/季)
  - 三因子权重自定义
- **资金配置**: 初始资金、手续费率

### 2. 单股票分析
- 实时价格和技术指标
- 基本面数据展示
- 价格走势图

### 3. 可视化图表
- **权益曲线**: 策略 vs 基准对比
- **回撤分析**: 最大回撤可视化
- **月度收益**: 热力图展示
- **交互式图表**: 支持缩放、悬停查看详情

### 4. 绩效指标
- 总收益率 / 年化收益
- 最大回撤 / 年化波动率
- 夏普比率 / 卡尔玛比率
- 胜率 / 盈亏比

## 🎯 使用流程

1. **启动系统**
   - 双击 `启动交易系统.bat`
   - 等待浏览器自动打开 (http://localhost:8501)

2. **运行回测**
   - 左侧选择「策略回测」
   - 配置参数 (股票池、时间、因子权重等)
   - 点击「开始回测」
   - 查看图表和绩效指标

3. **分析单股票**
   - 选择「单股票分析」
   - 输入股票代码
   - 查看技术指标和基本面

## 📊 三因子策略说明

### 质量因子 (Quality)
- ROE (净资产收益率) > 15%
- 盈利稳定性
- 财务健康度

### 价值因子 (Value)
- PE/PB 低于行业中位数
- 低估值优先

### 动量因子 (Momentum)
- 6个月价格趋势
- 强势股优先

## ⚙️ 系统要求

- Python 3.8+
- Windows/macOS/Linux
- 网络连接 (下载Yahoo Finance数据)

## 🛠️ 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖:
- streamlit >= 1.32.0
- plotly >= 5.18.0
- pandas >= 2.0.0
- yfinance >= 0.2.28

## 🔧 故障排除

### 页面无法打开
1. 检查终端是否有错误信息
2. 尝试手动访问 http://localhost:8501
3. 检查端口8501是否被占用

### 数据下载失败
1. 检查网络连接
2. 某些股票代码可能不存在，尝试其他代码
3. Yahoo Finance偶尔维护，稍后再试

### 缺少依赖
```bash
pip install --upgrade streamlit plotly pandas yfinance
```

## 📝 注意事项

1. **历史回测不代表未来收益**
2. 建议先用模拟盘测试1-3个月
3. 不要全仓跟随，建议只用部分资金
4. 定期检查策略绩效，必要时调整

## 🔄 更新日志

### v1.0 (2026-03-17)
- ✅ 初始版本发布
- ✅ 策略回测功能
- ✅ 可视化图表
- ✅ 单股票分析
- ✅ 交互式Web界面

---

**版本**: v1.0  
**策略**: Quality + Value + Momentum  
**数据源**: Yahoo Finance  
**技术栈**: Python + Streamlit + Plotly
