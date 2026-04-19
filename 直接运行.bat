@echo off
chcp 65001 >nul
echo 正在启动压枪脚本（旧版）...
cd /d "%~dp0"
python src\deprecated\recoil_control.py
pause
