@echo off
chcp 65001 >nul
echo ========================================
echo    美股三因子量化策略 - 完整回测
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
echo 正在安装依赖包（首次运行需要，可能需要几分钟）...
pip install -q pandas numpy yfinance matplotlib

echo.
echo 正在运行完整回测（首次会下载数据，需要5-10分钟）...
echo.
python main.py

echo.
echo ========================================
echo 回测完成！
echo 结果文件保存在当前目录：
echo   - equity_curve.csv
echo   - trades.csv
echo   - backtest_result.png
echo ========================================
pause
