@echo off
chcp 65001 >nul 2>&1
setlocal

:::: ======== 配置 ========
set "VERSION=v2.0"
set "EXE_NAME=游戏工具中心.exe"
set "DIST_DIR=dist\nuitka"
set "PROJECT_ROOT=%~dp0.."

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   游戏工具中心 %VERSION% - Nuitka 编译打包  ║
echo  ╚══════════════════════════════════════╝
echo.

REM 切换到项目根目录
cd /d "%PROJECT_ROOT%"

:::: ======== Step 1: Nuitka 编译 ========
echo  [1/5] Nuitka 编译...
echo.
echo  注意：编译可能需要 5-10 分钟，请耐心等待...
echo  注意：Python 3.14 对 Nuitka 只是实验性支持，推荐使用 PyInstaller
echo.

python -m nuitka --standalone --onefile ^
    --windows-console-mode=disable ^
    --lto=yes ^
    --python-flag=no_site ^
    --nofollow-import-to=numpy ^
    --nofollow-import-to=scipy ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=pandas ^
    --nofollow-import-to=pytest ^
    --nofollow-import-to=unittest ^
    --nofollow-import-to=test_recoil_core ^
    --nofollow-import-to=test_imported_data ^
    --nofollow-import-to=test_pattern_calculation ^
    --nofollow-import-to=test_dll ^
    --nofollow-import-to=test_right_click ^
    --nofollow-import-to=test_ui ^
    --nofollow-import-to=test_visualization ^
    --nofollow-import-to=test_weapon_multipliers ^
    --nofollow-import-to=recoil_ui ^
    --nofollow-import-to=recoil_control ^
    --nofollow-import-to=network ^
    --output-dir=%DIST_DIR% ^
    --include-data-file=vendor\IbInputSimulator.dll=IbInputSimulator.dll ^
    --include-module=lua_parser ^
    --include-module=pattern_recorder ^
    --enable-plugin=tk-inter ^
    --follow-import-to=customtkinter ^
    --follow-import-to=PIL ^
    --output-filename=%EXE_NAME% ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --show-memory ^
    src\recoil_ui_v2.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ✗ 编译失败！
    pause
    exit /b 1
)

echo.
echo  ✓ 编译成功
echo.

:::: ======== Step 2: 复制配置文件 ========
echo  [2/5] 复制配置文件...

if not exist "%DIST_DIR%\config" mkdir "%DIST_DIR%\config"
xcopy /E /Y /Q "config\*" "%DIST_DIR%\config\" >nul 2>&1
echo      ✓ config\

:::: ======== Step 3: 复制 VC++ 运行时 ========
echo  [3/5] 复制 VC++ 运行时（确保所有电脑都能打开）...

set VC_COPIED=0
for %%F in (vcruntime140.dll vcruntime140_1.dll) do (
    if exist "C:\Windows\System32\%%F" (
        copy /Y "C:\Windows\System32\%%F" "%DIST_DIR%\%%F" >nul 2>&1
        echo      ✓ %%F
        set VC_COPIED=1
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python314\%%F" (
        copy /Y "%LOCALAPPDATA%\Programs\Python\Python314\%%F" "%DIST_DIR%\%%F" >nul 2>&1
        echo      ✓ %%F （从 Python 目录）
        set VC_COPIED=1
    ) else (
        echo      ⚠ %%F 不存在（目标电脑需安装 VC++ Redistributable）
    )
)

:::: ======== Step 4: 复制 IbInputSimulator.dll 兜底 ========
echo  [4/5] 复制 IbInputSimulator.dll...

if exist "vendor\IbInputSimulator.dll" (
    copy /Y "vendor\IbInputSimulator.dll" "%DIST_DIR%\IbInputSimulator.dll" >nul 2>&1
    echo      ✓ IbInputSimulator.dll
) else (
    echo      ⚠ IbInputSimulator.dll 不在 vendor 目录
)

:::: ======== Step 5: 创建启动脚本 ========
echo  [5/5] 创建启动脚本...

(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title 游戏工具中心 %VERSION%
echo cd /d "%%~dp0"
echo.
echo :: 检查 VC++ 运行时
echo if not exist "%%~dp0vcruntime140.dll" ^
    if not exist "C:\Windows\System32\vcruntime140.dll" ^
    echo [警告] 缺少 VC++ 运行时，程序可能无法启动
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
echo  - 已包含 VC++ 运行时 (vcruntime140.dll)
echo  - 已包含 IbInputSimulator.dll
echo  - 已包含 config 配置文件
echo  - 所有电脑均可直接运行，无需安装 Python
echo.
echo  ⚠ 注意：Python 3.14 对 Nuitka 只是实验性支持
echo  如遇 0xC000001D 崩溃，请改用 build_pyinstaller.bat
echo  ══════════════════════════════════════
echo.
pause
