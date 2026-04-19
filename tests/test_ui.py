"""
测试压枪控制中心UI
"""

import sys
import os

# 添加 src 目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "src", "deprecated"))

try:
    # 尝试导入customtkinter
    import customtkinter as ctk
    print("[OK] customtkinter 导入成功")
except ImportError as e:
    print(f"[ERROR] 无法导入 customtkinter: {e}")
    print("请运行: pip install customtkinter")
    sys.exit(1)

try:
    # 尝试导入主程序
    from recoil_ui import RecoilControlUI
    print("[OK] 主程序导入成功")
except ImportError as e:
    print(f"[ERROR] 无法导入主程序: {e}")
    sys.exit(1)

# 检查配置文件目录
config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
if os.path.exists(config_dir):
    print(f"[OK] 配置目录存在: {config_dir}")
else:
    print(f"[WARN] 配置目录不存在，将创建: {config_dir}")

# 检查武器配置文件
weapons_file = os.path.join(config_dir, "weapons.json")
if os.path.exists(weapons_file):
    print(f"[OK] 武器配置文件存在: {weapons_file}")
else:
    print(f"[WARN] 武器配置文件不存在，将使用默认配置")

# 检查设置配置文件
settings_file = os.path.join(config_dir, "settings.json")
if os.path.exists(settings_file):
    print(f"[OK] 设置配置文件存在: {settings_file}")
else:
    print(f"[WARN] 设置配置文件不存在，将使用默认设置")

# 检查IbInputSimulator.dll
dll_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "IbInputSimulator.dll")
if os.path.exists(dll_file):
    print(f"[OK] IbInputSimulator.dll 存在: {dll_file}")
else:
    print(f"[WARN] IbInputSimulator.dll 不存在，压枪功能可能无法正常工作")

print("\n测试完成！")
print("如果所有检查都通过，可以运行 '启动压枪控制中心.bat' 启动程序。")

# 尝试启动UI（可选）
try:
    response = input("\n是否立即启动UI? (y/n): ")
    if response.lower() == 'y':
        print("正在启动UI...")
        app = RecoilControlUI()
        app.run()
except KeyboardInterrupt:
    print("\n用户取消启动")
except Exception as e:
    print(f"\n启动UI失败: {e}")