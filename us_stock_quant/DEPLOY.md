# 🚀 Streamlit Cloud 部署指南

## 部署前准备

### 1. 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称: `us-stock-quant` (或其他你喜欢的名字)
3. 选择 **Public** (公开) 或 **Private** (私有)
4. 勾选 "Add a README file"
5. 点击 **Create repository**

### 2. 上传代码到 GitHub

在本地 `us_stock_quant` 文件夹中打开终端/PowerShell，执行：

```bash
# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 关联远程仓库 (替换 YOUR_USERNAME 为你的GitHub用户名)
git remote add origin https://github.com/YOUR_USERNAME/us-stock-quant.git

# 推送到 GitHub
git push -u origin main
```

如果没有安装 git，可以直接在 GitHub 网页上上传文件：
1. 进入你的仓库
2. 点击 "Add file" → "Upload files"
3. 拖放 `us_stock_quant` 文件夹中的所有文件
4. 点击 "Commit changes"

### 3. 部署到 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 点击 "Sign in with GitHub" 登录
3. 点击 "New app"
4. 选择你的仓库 `us-stock-quant`
5. 主文件路径填写: `app.py`
6. 点击 "Deploy"

等待几分钟，部署完成后会显示一个链接，如:
```
https://your-app-name.streamlit.app
```

### 4. 设置访问密码（可选）

1. 在 Streamlit Cloud 点击你的应用
2. 点击右上角 "⋮" → "Settings"
3. 选择 "Sharing" 标签
4. 开启 "Enable access code"
5. 设置密码

## 文件结构说明

```
us_stock_quant/
├── app.py                 # 主应用文件 (Streamlit入口)
├── config.py              # 策略配置
├── requirements.txt       # Python依赖包
├── .gitignore            # Git忽略文件
├── README.md             # 项目说明
├── backtest/
│   ├── __init__.py
│   └── engine.py         # 回测引擎
├── strategies/
│   ├── __init__.py
│   └── factors.py        # 三因子模型
└── data/
    ├── __init__.py
    └── data_loader.py    # 数据获取
```

## 常见问题

### Q: 部署失败，提示模块找不到？
A: 检查 `requirements.txt` 是否包含所有依赖

### Q: 数据下载很慢？
A: Streamlit Cloud 服务器在国外，首次下载数据会比较慢，请耐心等待

### Q: 如何更新应用？
A: 修改代码后推送到 GitHub，Streamlit Cloud 会自动重新部署

### Q: 免费版有什么限制？
A: - 1GB 内存
   - 1GB 存储
   - 应用会在不使用时休眠（首次访问需要几秒唤醒）
   - 私有仓库需要付费 ($7/月)

## 私有化部署（可选）

如果你不想公开代码，可以：
1. 购买 Streamlit Cloud 付费版 ($7/月)
2. 或者部署到自己的服务器/VPS

## 联系方式

有问题可以查看：
- Streamlit 文档: https://docs.streamlit.io
- GitHub Issues: 在你的仓库提交问题
