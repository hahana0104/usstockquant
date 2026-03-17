# 🚀 V2.0 更新部署指南

## 本次更新内容

### ✨ 新增功能

1. **多策略支持**
   - 三因子策略 (QVM)
   - 均线交叉策略 (MA Crossover)
   - RSI策略 (超买超卖)
   - MACD策略 (金叉死叉)
   - 布林带策略

2. **回测历史保存**
   - 所有回测自动保存到SQLite数据库
   - 查看历史回测列表
   - 查看回测详情和图表
   - 删除历史记录

3. **策略对比功能**
   - 同时对比2-5个策略
   - 权益曲线叠加对比
   - 绩效指标并排对比

4. **实时行情监控**
   - 大盘指数实时显示
   - 热门股票列表
   - 单股票查询

5. **报告导出**
   - 生成HTML格式报告
   - 包含图表、指标、交易记录
   - 可下载保存

---

## 部署步骤

### Step 1: 更新 GitHub 仓库

**在 PowerShell 中执行：**

```bash
cd C:\Users\nono\.openclaw\workspace\us_stock_quant

git add .
git commit -m "V2.0 update: multi-strategy, history, comparison, realtime"
git push origin master
```

**如果没有 git：**

1. 打开 https://github.com/hahana0104/usstockquant
2. 删除旧的 `app.py`
3. 重新上传所有文件（包括新增的文件）

### Step 2: 重新部署

1. 访问 https://streamlit.io/cloud
2. 找到你的应用 `nono-usstockquant`
3. 点击右上角 **「⋮」** → **「Reboot」** 或等待自动更新

或者：

1. 点击应用进入管理页面
2. 点击 **「Reboot」** 重新部署

---

## 文件清单

确保上传了这些新文件：

```
us_stock_quant/
├── app.py                      ✅ 更新 - 主应用V2.0
├── strategies/
│   └── all_strategies.py      ✅ 新增 - 多策略支持
├── utils/
│   ├── __init__.py            ✅ 新增
│   ├── database.py            ✅ 新增 - 数据库模块
│   ├── report_generator.py    ✅ 新增 - 报告生成
│   └── realtime_data.py       ✅ 新增 - 实时数据
└── requirements.txt           ✅ 更新 - 添加kaleido
```

---

## 使用说明

### 多策略回测

1. 进入「策略回测」页面
2. 在侧边栏选择策略类型
3. 调整策略参数
4. 点击「开始回测」

### 查看历史

1. 进入「回测历史」页面
2. 查看所有保存的回测记录
3. 输入ID查看详情
4. 可以下载报告或删除记录

### 策略对比

1. 进入「策略对比」页面
2. 选择2-5个历史回测
3. 点击「开始对比」
4. 查看对比表格和叠加图表

### 实时行情

1. 进入「实时行情」页面
2. 查看大盘指数
3. 查看热门股票
4. 输入股票代码查询

---

## ⚠️ 注意事项

1. **数据库**: 回测历史保存在 SQLite 数据库中，Streamlit Cloud 免费版重启后数据会丢失（容器化部署）。如需持久化保存，需要：
   - 付费版 Streamlit Cloud
   - 或者使用外部数据库（如 PostgreSQL）

2. **实时数据**: Yahoo Finance 数据有15分钟延迟，非真正的实时数据

3. **首次加载**: 部署后首次访问可能需要 30-60 秒启动时间

---

有问题随时问我！
