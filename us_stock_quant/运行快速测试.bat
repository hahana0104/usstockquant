@echo off
chcp 65001 >nul
echo ========================================
echo    美股三因子量化策略 - 快速测试
echo ========================================
echo.

cd /d "C:\Users\nono\.openclaw\workspace\us_stock_quant"

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python环境正常
echo.
echo 正在安装依赖包（首次运行需要）...
pip install -q pandas numpy yfinance matplotlib

echo.
echo 正在运行快速测试...
echo.
python quick_test.py

echo.
echo ========================================
echo 测试完成！按任意键退出...
echo ========================================
pause >nul
