"""
测试右键删除武器功能
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

print("\n测试右键删除武器功能...")
print("说明：")
print("1. 在武器列表中右键点击某个武器")
print("2. 应该会弹出右键菜单")
print("3. 点击'删除武器'选项")
print("4. 确认删除对话框应该出现")

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