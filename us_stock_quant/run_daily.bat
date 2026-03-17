@echo off
chcp 65001 >nul
cd /d C:\Users\nono\.openclaw\workspace\us_stock_quant
python daily_picker.py
echo.
echo 按任意键退出...
pause >nul
