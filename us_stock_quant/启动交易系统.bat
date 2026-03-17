@echo off
chcp 65001 >nul
echo ==========================================
echo    美股三因子量化交易系统
echo    Web可视化界面启动器
echo ==========================================
echo.

cd /d "C:\Users\nono\.openclaw\workspace\us_stock_quant"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请确保已安装Python 3.8+
    pause
    exit /b 1
)
echo OK
echo.

echo [2/3] 检查依赖包...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 安装依赖失败
        pause
        exit /b 1
    )
)
echo OK
echo.

echo [3/3] 启动Web服务...
echo.
echo ==========================================
echo 系统将在浏览器中打开
echo 如果未自动打开，请访问: http://localhost:8501
echo 按 Ctrl+C 停止服务
echo ==========================================
echo.

streamlit run app.py --server.port=8501 --server.address=localhost

pause
