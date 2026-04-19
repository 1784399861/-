"""
测试轨迹可视化功能
"""

import sys
import os

# 添加 src 目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "src"))

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
    from recoil_ui_v2 import RecoilControlUIv2
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
    
    # 读取武器数据检查LUA导入
    import json
    try:
        with open(weapons_file, 'r', encoding='utf-8') as f:
            weapons_data = json.load(f)
        
        # 查找有lua_pattern的武器
        lua_weapons = []
        for weapon_name, weapon_data in weapons_data.items():
            if isinstance(weapon_data, dict) and "lua_pattern" in weapon_data:
                lua_weapons.append(weapon_name)
        
        if lua_weapons:
            print(f"[OK] 找到 {len(lua_weapons)} 个LUA导入的武器: {', '.join(lua_weapons[:5])}{'...' if len(lua_weapons) > 5 else ''}")
        else:
            print("[WARN] 没有找到LUA导入的武器数据")
            
    except Exception as e:
        print(f"[ERROR] 读取武器配置失败: {e}")
else:
    print(f"[WARN] 武器配置文件不存在，将使用默认配置")

print("\n测试完成！")
print("正在启动UI测试轨迹可视化...")

# 启动UI
try:
    app = RecoilControlUIv2()
    app.run()
except KeyboardInterrupt:
    print("\n用户取消启动")
except Exception as e:
    print(f"\n启动UI失败: {e}")
    import traceback
    traceback.print_exc()