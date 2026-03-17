# Streamlit Cloud 部署检查清单

## ✅ 部署前确认

- [ ] 已创建 GitHub 账号: https://github.com/signup
- [ ] 已创建 GitHub 仓库 (Public 或 Private)
- [ ] 代码已上传到 GitHub

## 📁 代码文件清单

确认以下文件都在 `us_stock_quant` 文件夹中：

```
us_stock_quant/
├── app.py                 ✅ 主应用
├── config.py              ✅ 配置文件
├── requirements.txt       ✅ 依赖列表
├── .gitignore            ✅ Git忽略
├── DEPLOY.md             ✅ 部署指南
├── backtest/
│   ├── __init__.py       ✅
│   └── engine.py         ✅ 回测引擎
├── strategies/
│   ├── __init__.py       ✅
│   └── factors.py        ✅ 三因子策略
└── data/
    ├── __init__.py       ✅
    └── data_loader.py    ✅ 数据加载
```

## 🚀 部署步骤

### Step 1: 上传到 GitHub

**方法一：命令行（推荐）**

```bash
cd us_stock_quant
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/us-stock-quant.git
git push -u origin main
```

**方法二：网页上传**

1. 打开 https://github.com/YOUR_USERNAME/us-stock-quant
2. 点击 "Add file" → "Upload files"
3. 选择所有文件上传

### Step 2: 部署到 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择仓库: `YOUR_USERNAME/us-stock-quant`
5. 主文件路径: `app.py`
6. 点击 "Deploy"

### Step 3: 等待部署完成

- 部署通常需要 2-5 分钟
- 完成后会显示链接: `https://xxx.streamlit.app`

### Step 4: 分享链接

- 复制链接发给朋友
- 可选：设置访问密码

## 🔒 设置密码保护

1. 在 Streamlit Cloud 点击你的应用
2. 点击 "⋮" → "Settings"
3. 选择 "Sharing" 标签
4. 开启 "Enable access code"
5. 输入密码，点击 Save

## ❌ 常见问题

**Q: 提示 "Module not found"？**
- 检查 requirements.txt 是否包含该模块
- 重新部署

**Q: 应用打开很慢？**
- Streamlit Cloud 免费版会休眠，首次访问需要唤醒（约 5-10 秒）
- 数据下载依赖 Yahoo Finance，国外服务器访问较快

**Q: 如何更新应用？**
- 修改代码 → push 到 GitHub → 自动重新部署

## 📞 需要帮助？

如果部署遇到问题，可以：
1. 查看 `DEPLOY.md` 详细说明
2. 检查 GitHub 仓库文件是否完整
3. 查看 Streamlit Cloud 的部署日志
