"""
测试 IbInputSimulator.dll 是否能被正确加载
"""

import ctypes
import os
import sys

# 获取项目根目录和 DLL 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dll_path = os.path.join(_project_root, "vendor", "IbInputSimulator.dll")

print(f"项目根目录: {_project_root}")
print(f"DLL 路径: {dll_path}")
print(f"DLL 是否存在: {os.path.exists(dll_path)}")

if not os.path.exists(dll_path):
    print("错误：找不到 IbInputSimulator.dll")
    sys.exit(1)

try:
    # 尝试加载 DLL
    ib_input = ctypes.CDLL(dll_path)
    print("[OK] DLL 加载成功！")
    
    # 尝试获取 IbSendInit 函数
    try:
        ib_input.IbSendInit.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        ib_input.IbSendInit.restype = ctypes.c_uint32
        print("[OK] IbSendInit 函数找到！")
        
        # 尝试初始化
        result = ib_input.IbSendInit(1, 0, None)  # SendInput 驱动
        if result == 0:
            print("[OK] IbSendInit 初始化成功！")
        else:
            print(f"[WARN] IbSendInit 返回错误码: {result}")
            
    except AttributeError as e:
        print(f"[ERROR] 找不到 IbSendInit 函数: {e}")
        
except OSError as e:
    print(f"[ERROR] 无法加载 DLL: {e}")
    sys.exit(1)

print("\n测试完成！")