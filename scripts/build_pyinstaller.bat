@echo off
chcp 65001 >nul 2>&1
setlocal

:::: ======== 配置 ========
set "VERSION=v2.0"
set "EXE_NAME=游戏工具中心.exe"
set "DIST_DIR=dist\pyinstaller"
set "PROJECT_ROOT=%~dp0.."

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   游戏工具中心 %VERSION% - PyInstaller 打包  ║
echo  ║   （兼容所有电脑，无需额外依赖）        ║
echo  ╚══════════════════════════════════════╝
echo.

REM 切换到项目根目录
cd /d "%PROJECT_ROOT%"

:::: ======== Step 1: PyInstaller 编译 ========
echo  [1/5] PyInstaller 编译...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "游戏工具中心" ^
    --add-binary "%PROJECT_ROOT%\vendor\IbInputSimulator.dll;." ^
    --add-data "%PROJECT_ROOT%\config;config" ^
    --hidden-import=lua_parser ^
    --hidden-import=pattern_recorder ^
    --hidden-import=PIL ^
    --hidden-import=customtkinter ^
    --distpath %DIST_DIR% ^
    --workpath _pyinstaller_build ^
    --specpath _pyinstaller_build ^
    %PROJECT_ROOT%\src\recoil_ui_v2.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ✗ 编译失败！
    pause
    exit /b 1
)

echo.
echo  ✓ 编译成功
echo.

:::: ======== Step 2: 复制 VC++ 运行时 ========
echo  [2/5] 复制 VC++ 运行时（确保所有电脑都能打开）...

for %%F in (vcruntime140.dll vcruntime140_1.dll) do (
    if exist "C:\Windows\System32\%%F" (
        copy /Y "C:\Windows\System32\%%F" "%DIST_DIR%\%%F" >nul 2>&1
        echo      ✓ %%F
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python314\%%F" (
        copy /Y "%LOCALAPPDATA%\Programs\Python\Python314\%%F" "%DIST_DIR%\%%F" >nul 2>&1
        echo      ✓ %%F （从 Python 目录）
    ) else (
        echo      ⚠ %%F 不存在
    )
)

:::: ======== Step 3: 复制 IbInputSimulator.dll 兜底 ========
echo  [3/5] 复制 IbInputSimulator.dll...

if exist "vendor\IbInputSimulator.dll" (
    copy /Y "vendor\IbInputSimulator.dll" "%DIST_DIR%\IbInputSimulator.dll" >nul 2>&1
    echo      ✓ IbInputSimulator.dll
) else (
    echo      ⚠ IbInputSimulator.dll 不在 vendor 目录
)

:::: ======== Step 4: 复制完整 config 目录 ========
echo  [4/5] 复制完整 config 目录...

if exist "config" (
    if not exist "%DIST_DIR%\config" mkdir "%DIST_DIR%\config"
    xcopy /E /Y /Q "config\*" "%DIST_DIR%\config\" >nul 2>&1
    echo      ✓ config\ （完整复制）
)

:::: ======== Step 5: 创建启动脚本 ========
echo  [5/5] 创建启动脚本...

(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title 游戏工具中心 %VERSION%
echo cd /d "%%~dp0"
echo.
echo echo  启动游戏工具中心 %VERSION% ...
echo "%%~dp0%EXE_NAME%"
echo.
echo set "EXIT_CODE=%%ERRORLEVEL%%"
echo if not "%%EXIT_CODE%%"=="0" (
echo.
echo if exist "%%~dp0crash.log" (
echo.
echo   echo   ---- 闪退诊断日志 ----
echo   type "%%~dp0crash.log"
echo   echo   ----------------------
echo.
echo ^)
echo.
echo echo  程序已退出 ^(代码: %%EXIT_CODE%%^)
echo.
echo pause
echo ^)
) > "%DIST_DIR%\启动游戏工具中心.bat"

echo      ✓ 启动游戏工具中心.bat

:::: ======== 完成汇总 ========
echo.
echo  ══════════════════════════════════════
echo  ✓ 打包完成！
echo.
echo  输出目录: %DIST_DIR%\
echo  主程序:   %EXE_NAME%
echo  启动方式: 双击 启动游戏工具中心.bat
echo.
echo  兼容性说明:
echo  - PyInstaller 打包，使用官方 Python 解释器
echo  - 已包含 VC++ 运行时 (vcruntime140.dll)
echo  - 已包含 IbInputSimulator.dll
echo  - 已包含 config 配置文件
echo  - 所有电脑均可直接运行，无需安装 Python
echo  ══════════════════════════════════════
echo.

:::: 清理构建目录
echo  清理临时文件...
if exist "_pyinstaller_build" rd /s /q "_pyinstaller_build" 2>nul
echo      ✓ 已清理

echo.
pause
