@echo off
chcp 65001 >nul
echo ==========================================
echo    美股量化交易系统 - 公开分享模式
echo ==========================================
echo.
echo 注意: 使用此模式会生成公开链接，任何人都能访问
echo.

cd /d "C:\Users\nono\.openclaw\workspace\us_stock_quant"

echo 正在启动并创建公开链接...
echo 首次使用需要注册，按提示操作即可
echo.

streamlit run app.py --server.port=8501 --server.address=localhost --server.enableCORS=false --server.enableXsrfProtection=false

pause
