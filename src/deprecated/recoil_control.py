"""
IbInputSimulator 压枪脚本 (Python 版本)
使用前请确保已安装 IbInputSimulator 并正确配置驱动
"""

import ctypes
import ctypes.wintypes
import time
import threading
import sys
import os

# 配置参数
RECOIL_PATTERN = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]  # 每发子弹的下移像素
FIRE_BUTTON = 0x01  # 鼠标左键 VK_LBUTTON
TOGGLE_KEY = 0x70   # F1 键
MOVE_INTERVAL_MS = 10  # 移动间隔（毫秒）

# 全局变量
enabled = True
firing = False
bullet_index = 0

# 尝试加载 IbInputSimulator.dll
script_dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(script_dir, "IbInputSimulator.dll")
if not os.path.exists(dll_path):
    print(f"错误：找不到 {dll_path}")
    print("请确保 DLL 文件在脚本同一目录下。")
    sys.exit(1)

try:
    ib_input = ctypes.CDLL(dll_path)
except OSError as e:
    print(f"错误：无法加载 {dll_path}")
    print(f"详细信息：{e}")
    sys.exit(1)

# 定义 SendType 枚举
class SendType:
    AnyDriver = 0
    SendInput = 1
    Logitech = 2
    LogitechGHubNew = 6
    Razer = 3
    DD = 4
    MouClassInputInjection = 5

# 定义 MoveMode 枚举
class MoveMode:
    Absolute = 0
    Relative = 1

# 定义函数签名
ib_input.IbSendInit.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
ib_input.IbSendInit.restype = ctypes.c_uint32

ib_input.IbSendDestroy.argtypes = []
ib_input.IbSendDestroy.restype = None

ib_input.IbSendMouseMove.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
ib_input.IbSendMouseMove.restype = ctypes.c_bool

# 初始化 IbInputSimulator
def init_ib_input_simulator():
    """初始化 IbInputSimulator"""
    # 使用 SendInput 驱动（最通用）
    result = ib_input.IbSendInit(SendType.SendInput, 0, None)
    if result != 0:
        print(f"错误：IbSendInit 初始化失败，错误码：{result}")
        return False
    print("IbInputSimulator 初始化成功")
    return True

# 模拟鼠标相对移动
def move_mouse_relative(x, y):
    """模拟鼠标相对移动"""
    return ib_input.IbSendMouseMove(x, y, MoveMode.Relative)

# 压枪逻辑
def recoil_control():
    """压枪逻辑"""
    global bullet_index
    
    if not enabled or not firing:
        return
    
    # 获取当前子弹对应的下移量
    if bullet_index >= len(RECOIL_PATTERN):
        bullet_index = len(RECOIL_PATTERN) - 1
    
    move_y = RECOIL_PATTERN[bullet_index]
    
    # 执行向下移动
    move_mouse_relative(0, move_y)
    
    bullet_index += 1

# 重置子弹计数
def reset_bullet_index():
    """重置子弹计数"""
    global bullet_index
    bullet_index = 0

# 压枪线程
def recoil_thread():
    """压枪线程"""
    while True:
        recoil_control()
        time.sleep(MOVE_INTERVAL_MS / 1000.0)

# 监听鼠标和键盘事件
def listen_events():
    """监听鼠标和键盘事件"""
    global enabled, firing
    
    print("开始监听事件...")
    print("热键说明：")
    print("  F1 - 开关压枪功能")
    print("  鼠标左键 - 开火时自动压枪")
    print("  Ctrl+C - 退出程序")
    print("")
    
    try:
        while True:
            # 检测鼠标左键状态
            left_button_state = ctypes.windll.user32.GetAsyncKeyState(FIRE_BUTTON)
            if left_button_state & 0x8000:  # 按下
                if not firing:
                    firing = True
                    reset_bullet_index()
            else:  # 松开
                if firing:
                    firing = False
                    reset_bullet_index()
            
            # 检测 F1 键状态
            f1_state = ctypes.windll.user32.GetAsyncKeyState(TOGGLE_KEY)
            if f1_state & 0x0001:  # 按下并释放
                enabled = not enabled
                if enabled:
                    print("压枪已开启")
                else:
                    print("压枪已关闭")
            
            time.sleep(0.001)  # 1ms 轮询间隔
            
    except KeyboardInterrupt:
        print("\n程序已退出")

# 清理资源
def cleanup():
    """清理资源"""
    ib_input.IbSendDestroy()
    print("资源已清理")

def main():
    """主函数"""
    print("=== IbInputSimulator 压枪脚本 (Python 版本) ===")
    
    # 初始化 IbInputSimulator
    if not init_ib_input_simulator():
        input("按任意键退出...")
        return
    
    # 启动压枪线程
    recoil_thread_handle = threading.Thread(target=recoil_thread, daemon=True)
    recoil_thread_handle.start()
    
    try:
        # 开始监听事件
        listen_events()
    finally:
        # 清理资源
        cleanup()

if __name__ == "__main__":
    main()