@echo off
chcp 65001 >nul
echo ========================================
echo   压枪控制中心 v2.0 - 集成压枪核心
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.x
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 customtkinter 是否安装
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 customtkinter...
    pip install customtkinter
)

REM 检查主程序是否存在
if not exist "%~dp0src\recoil_ui_v2.py" (
    echo 错误：未找到 src\recoil_ui_v2.py
    pause
    exit /b 1
)

echo 正在启动压枪控制中心 v2.0...
echo.
echo 功能说明：
echo   - 左侧：武器选择和新增
echo   - 右侧：参数设置和显示
echo   - 底部：运行日志查询
echo   - 支持联网同步配置
echo   - 集成压枪核心功能
echo   - 触发方式：鼠标左键+右键同时按下
echo.
echo ========================================
echo.

REM 以管理员权限运行（某些游戏需要）
net session >nul 2>&1
if errorlevel 1 (
    echo 提示：建议以管理员权限运行此程序
    echo 正在尝试以管理员权限重新启动...
    powershell -Command "Start-Process python -ArgumentList '%~dp0src\recoil_ui_v2.py' -Verb RunAs"
    exit /b
)

REM 运行 Python 脚本
python "%~dp0src\recoil_ui_v2.py"

pause
