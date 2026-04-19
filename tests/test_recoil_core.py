"""
压枪核心模块测试脚本
测试鼠标按键检测和压枪功能
"""

import sys
import os
import time

# 添加 src 目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "src"))

from recoil_core import RecoilCore

def main():
    print("=== 压枪核心模块测试 ===")
    
    # 创建压枪核心实例
    config_dir = os.path.join(_project_root, "config")
    core = RecoilCore(config_dir)
    
    # 设置回调函数
    def log_callback(message):
        print(f"[LOG] {message}")
    
    def status_callback(status):
        print(f"[状态] {status}")
    
    core.set_log_callback(log_callback)
    core.set_status_callback(status_callback)
    
    # 测试功能
    print("\n1. 检查武器配置...")
    weapons = core.get_weapon_list()
    print(f"   武器列表: {weapons}")
    
    if weapons:
        print(f"\n2. 选择武器: {weapons[0]}")
        core.set_current_weapon(weapons[0])
        
        weapon = core.get_weapon(weapons[0])
        print(f"   武器名称: {weapon['name']}")
        print(f"   压枪模式: {weapon['pattern']}")
        print(f"   射速: {weapon['fire_rate']}ms")
        print(f"   启用状态: {weapon.get('enabled', True)}")
    
    print("\n3. 启用压枪功能...")
    core.enable()
    
    print("\n4. 开始监听鼠标按键...")
    core.start_monitoring()
    
    print("\n5. 测试说明:")
    print("   - 同时按下鼠标左键和右键触发压枪")
    print("   - 松开任意键停止压枪")
    print("   - 按 Ctrl+C 停止测试")
    
    try:
        # 运行10秒测试
        for i in range(10):
            print(f"\r测试运行中... {i+1}/10秒", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n用户中断测试...")
    finally:
        print("\n6. 清理资源...")
        core.cleanup()
        print("测试完成!")

if __name__ == "__main__":
    main()