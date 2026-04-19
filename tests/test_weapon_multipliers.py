"""
测试每把武器倍率数组功能
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

print("\n测试每把武器倍率数组功能...")
print("说明：")
print("1. 选择一个武器")
print("2. 在武器参数选项卡中查看'倍率数组'输入框")
print("3. 修改倍率数组（例如：1.0, 1.25, 2.0, 3.0）")
print("4. 点击'保存武器参数'")
print("5. 查看'倍镜切换'下拉菜单，应该显示武器自己的倍率选项")
print("6. 使用鼠标侧键切换倍率，应该在武器的倍率数组内循环切换")

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