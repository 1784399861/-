@echo off
chcp 65001 >nul 2>&1
setlocal

REM ============================================
REM  打包分发脚本 - 将程序打包成可分发的 ZIP
REM  自动收集所有必需文件，确保所有电脑可运行
REM ============================================

set VERSION=v2.0
set "EXE_NAME=游戏工具中心.exe"
set "DIST_DIR=dist\pyinstaller"
set "OUTPUT_ZIP=游戏工具中心%VERSION%_发布包.zip"
set "PROJECT_ROOT=%~dp0.."

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   打包分发 - 游戏工具中心 %VERSION%       ║
echo  ╚══════════════════════════════════════╝
echo.

REM 切换到项目根目录
cd /d "%PROJECT_ROOT%"

REM 检查主程序
if not exist "%DIST_DIR%\%EXE_NAME%" (
    echo  ✗ 未找到编译后的 exe，请先运行 scripts\build_pyinstaller.bat
    pause
    exit /b 1
)

echo [1/4] 检查依赖文件...

REM 确保 VC++ 运行时存在
set VC_MISSING=0
for %%F in (vcruntime140.dll vcruntime140_1.dll) do (
    if not exist "%DIST_DIR%\%%F" (
        if exist "C:\Windows\System32\%%F" (
            copy /Y "C:\Windows\System32\%%F" "%DIST_DIR%\%%F" >nul 2>&1
            echo      ✓ %%F 已补充复制
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python314\%%F" (
            copy /Y "%LOCALAPPDATA%\Programs\Python\Python314\%%F" "%DIST_DIR%\%%F" >nul 2>&1
            echo      ✓ %%F 已从 Python 目录补充
        ) else (
            echo      ⚠ %%F 缺失！新电脑可能无法启动
            set VC_MISSING=1
        )
    ) else (
        echo      ✓ %%F
    )
)

REM 确保 IbInputSimulator.dll 存在
if not exist "%DIST_DIR%\IbInputSimulator.dll" (
    if exist "vendor\IbInputSimulator.dll" (
        copy /Y "vendor\IbInputSimulator.dll" "%DIST_DIR%\IbInputSimulator.dll" >nul 2>&1
        echo      ✓ IbInputSimulator.dll 已补充
    ) else (
        echo      ⚠ IbInputSimulator.dll 缺失！
    )
) else (
    echo      ✓ IbInputSimulator.dll
)

echo.
echo [2/4] 复制配置文件...

if exist "config" (
    if not exist "%DIST_DIR%\config" mkdir "%DIST_DIR%\config"
    copy "config\weapons.json" "%DIST_DIR%\config\" >nul 2>&1
    copy "config\settings.json" "%DIST_DIR%\config\" >nul 2>&1
    echo      ✓ 配置文件已复制
    
    REM 复制武器图片目录
    if exist "config\weapon_images" (
        if not exist "%DIST_DIR%\config\weapon_images" mkdir "%DIST_DIR%\config\weapon_images"
        xcopy "config\weapon_images\*" "%DIST_DIR%\config\weapon_images\" /Y /Q >nul 2>&1
        echo      ✓ 武器图片已复制
    )
) else (
    echo      ⚠ config 目录不存在
)

echo.
echo [3/4] 打包 ZIP...

REM 使用 PowerShell 创建 ZIP
powershell -NoProfile -Command ^
    "if (Test-Path '%OUTPUT_ZIP%') { Remove-Item '%OUTPUT_ZIP%' -Force }; ^
     $src = '%DIST_DIR%'; ^
     $items = @(); ^
     $exe = Join-Path $src '%EXE_NAME%'; if (Test-Path $exe) { $items += $exe }; ^
     $bat = Get-ChildItem (Join-Path $src '*.bat') -ErrorAction SilentlyContinue; if ($bat) { $items += $bat }; ^
     $dll1 = Join-Path $src 'vcruntime140.dll'; if (Test-Path $dll1) { $items += $dll1 }; ^
     $dll2 = Join-Path $src 'vcruntime140_1.dll'; if (Test-Path $dll2) { $items += $dll2 }; ^
     $dll3 = Join-Path $src 'IbInputSimulator.dll'; if (Test-Path $dll3) { $items += $dll3 }; ^
     $cfg = Join-Path $src 'config'; if (Test-Path $cfg) { $items += $cfg }; ^
     Compress-Archive -Path $items -DestinationPath '%OUTPUT_ZIP%' -Force"

if errorlevel 1 (
    echo      ✗ 打包失败
    pause
    exit /b 1
)

echo      ✓ 已生成: %OUTPUT_ZIP%

echo.
echo [4/4] 分发内容清单:
echo      ├─ %EXE_NAME%              （主程序）
echo      ├─ 启动游戏工具中心.bat        （启动脚本，含环境检测）
echo      ├─ vcruntime140.dll              （VC++ 运行时）
echo      ├─ vcruntime140_1.dll            （VC++ 运行时）
echo      ├─ IbInputSimulator.dll          （驱动级输入库）
echo      └─ config\                       （配置目录）
echo          ├─ weapons.json
echo          ├─ settings.json
echo          └─ weapon_images\
echo.
echo  ══════════════════════════════════════
echo  新电脑使用方法:
echo  1. 解压 ZIP 到任意目录
echo  2. 双击 "启动游戏工具中心.bat"
echo  3. 也可以直接双击 exe 启动
echo.
echo  兼容性说明:
echo  - 已包含 VC++ 运行时，无需额外安装
echo  - 已包含所有依赖 DLL，无需安装 Python
echo  - 支持 Windows 10/11 (64位)
echo  ══════════════════════════════════════
echo.
echo  ✓ 打包完成！
pause
