"""
压枪核心模块
实现鼠标按键检测和压枪轨迹执行
"""

import ctypes
import ctypes.wintypes
import time
import threading
import json
import os
import sys
import math
import random
from datetime import datetime

# Windows API 常量
VK_LBUTTON = 0x01  # 鼠标左键
VK_RBUTTON = 0x02  # 鼠标右键
VK_XBUTTON1 = 0x05  # 鼠标侧键1（后退）
VK_XBUTTON2 = 0x06  # 鼠标侧键2（前进）
MOUSEEVENTF_MOVE = 0x0001

class RecoilCore:
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.weapons_file = os.path.join(config_dir, "weapons.json")
        self.settings_file = os.path.join(config_dir, "settings.json")
        self.log_file = os.path.join(config_dir, "app.log")
        
        # 加载配置
        self.weapons = self.load_weapons()
        self.settings = self.load_settings()
        
        # 当前武器
        self.current_weapon = None
        
        # 压枪状态
        self.enabled = False
        self.running = False
        self.paused = False
        
        # 按键状态
        self.left_button_pressed = False
        self.right_button_pressed = False
        self.side_button1_pressed = False
        self.side_button2_pressed = False
        
        # 倍镜切换
        self.scope_multipliers = [1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0]  # 默认倍镜列表
        self.current_scope_index = 0  # 当前倍镜索引
        self.current_scope_multiplier = 1.0  # 当前倍镜倍率
        
        # 倍镜切换快捷键设置
        self.scope_prev_key = self.settings.get("scope_prev_key", "侧键1")  # 切换到上一个倍率的按键
        self.scope_next_key = self.settings.get("scope_next_key", "侧键2")  # 切换到下一个倍率的按键
        
        # 线程控制
        self.monitor_thread = None
        self.recoil_thread = None
        self.stop_event = threading.Event()
        
        # 回调函数
        self.log_callback = None
        self.status_callback = None
        
        # 加载IbInputSimulator
        self.ib_input = None
        self.load_ib_input_simulator()
        
    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback
        
    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception:
            pass
        
        # 调用回调函数
        if self.log_callback:
            self.log_callback(log_entry)
            
    def update_status(self, status):
        """更新状态"""
        if self.status_callback:
            self.status_callback(status)
    
    def load_ib_input_simulator(self):
        """加载IbInputSimulator DLL"""
        try:
            # DLL 搜索路径（按优先级）：
            # 1. exe 同目录（用户手动放置的 DLL）
            # 2. PyInstaller 临时解压目录（sys._MEIPASS，打包进 exe 的 DLL）
            # 3. vendor/ 目录（开发模式下 DLL 在项目根目录的 vendor/ 下）
            # 4. __file__ 同目录（Nuitka onefile 临时解压目录）
            is_packaged = not sys.argv[0].endswith('.py')
            
            if is_packaged:
                exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            else:
                # 开发模式：__file__ 在 src/ 下，项目根目录是上一级
                src_dir = os.path.dirname(os.path.abspath(__file__))
                exe_dir = os.path.dirname(src_dir)
            
            # PyInstaller 解压临时目录
            meipass_dir = getattr(sys, '_MEIPASS', None)
            
            dll_paths = [
                os.path.join(exe_dir, "IbInputSimulator.dll"),          # exe 同目录 / 项目根目录
            ]
            
            # vendor/ 目录（开发模式下 DLL 在此）
            dll_paths.append(os.path.join(exe_dir, "vendor", "IbInputSimulator.dll"))
            
            # PyInstaller 临时目录（打包进 exe 的 DLL）
            if meipass_dir:
                dll_paths.append(os.path.join(meipass_dir, "IbInputSimulator.dll"))
            
            # Nuitka __file__ 目录（打包进 exe 的 DLL）
            dll_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "IbInputSimulator.dll"))
            
            dll_path = None
            for path in dll_paths:
                if os.path.exists(path):
                    dll_path = path
                    break
            if dll_path and os.path.exists(dll_path):
                self.ib_input = ctypes.CDLL(dll_path)
                self.ib_input.IbSendInit.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
                self.ib_input.IbSendInit.restype = ctypes.c_uint32
                self.ib_input.IbSendMouseMove.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
                self.ib_input.IbSendMouseMove.restype = ctypes.c_bool
                
                # 初始化
                result = self.ib_input.IbSendInit(1, 0, None)  # SendInput驱动
                if result == 0:
                    self.log("IbInputSimulator 加载成功")
                    return True
                else:
                    self.log(f"IbInputSimulator 初始化失败: {result}", "ERROR")
            else:
                self.log("未找到 IbInputSimulator.dll", "ERROR")
        except Exception as e:
            self.log(f"加载 IbInputSimulator 失败: {e}", "ERROR")
        return False
    
    def load_weapons(self):
        """加载武器配置"""
        if os.path.exists(self.weapons_file):
            try:
                with open(self.weapons_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def save_weapons(self):
        """保存武器配置"""
        try:
            with open(self.weapons_file, 'w', encoding='utf-8') as f:
                json.dump(self.weapons, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log(f"保存武器配置失败: {e}", "ERROR")
            return False
    
    def load_settings(self):
        """加载设置"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "hotkey": "F1",
            "fire_button": "LButton",
            "move_interval": 10,
            "left_right_trigger": True,  # 左键+右键触发
            "scope_prev_key": "侧键1",  # 切换到上一个倍率的按键
            "scope_next_key": "侧键2"  # 切换到下一个倍率的按键
        }
    
    def save_settings(self):
        """保存设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log(f"保存设置失败: {e}", "ERROR")
            return False
    
    def set_current_weapon(self, weapon_name):
        """设置当前武器"""
        if weapon_name in self.weapons:
            self.current_weapon = weapon_name
            weapon = self.weapons[weapon_name]
            self.log(f"选择武器: {weapon['name']}")
            return True
        return False
    
    def get_weapon_list(self):
        """获取武器列表"""
        return list(self.weapons.keys())
    
    def get_weapon(self, weapon_name):
        """获取武器配置"""
        return self.weapons.get(weapon_name)
    
    def add_weapon(self, weapon_data):
        """添加武器"""
        try:
            name = weapon_data.get("name")
            if not name:
                return False
            
            self.weapons[name] = weapon_data
            self.save_weapons()
            self.log(f"添加武器: {name}")
            return True
        except Exception as e:
            self.log(f"添加武器失败: {e}", "ERROR")
            return False
    
    def delete_weapon(self, weapon_name):
        """删除武器"""
        try:
            if weapon_name in self.weapons:
                del self.weapons[weapon_name]
                self.save_weapons()
                self.log(f"删除武器: {weapon_name}")
                return True
            return False
        except Exception as e:
            self.log(f"删除武器失败: {e}", "ERROR")
            return False
    
    def update_weapon(self, weapon_name, weapon_data):
        """更新武器配置"""
        try:
            if weapon_name in self.weapons:
                self.weapons[weapon_name] = weapon_data
                self.save_weapons()
                self.log(f"更新武器: {weapon_name}")
                return True
            return False
        except Exception as e:
            self.log(f"更新武器失败: {e}", "ERROR")
            return False
    
    def start_monitoring(self):
        """开始监听鼠标按键"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_mouse_buttons, daemon=True)
        self.monitor_thread.start()
        self.log("开始监听鼠标按键")
    
    def stop_monitoring(self):
        """停止监听鼠标按键"""
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        self.log("停止监听鼠标按键")
    
    def _monitor_mouse_buttons(self):
        """监听鼠标按键状态"""
        while not self.stop_event.is_set():
            # 检查鼠标左键状态
            left_state = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON)
            left_pressed = (left_state & 0x8000) != 0
            
            # 检查鼠标右键状态
            right_state = ctypes.windll.user32.GetAsyncKeyState(VK_RBUTTON)
            right_pressed = (right_state & 0x8000) != 0
            
            # 检查鼠标侧键状态
            side1_state = ctypes.windll.user32.GetAsyncKeyState(VK_XBUTTON1)
            side1_pressed = (side1_state & 0x8000) != 0
            
            side2_state = ctypes.windll.user32.GetAsyncKeyState(VK_XBUTTON2)
            side2_pressed = (side2_state & 0x8000) != 0
            
            # 检查是否同时按下左键和右键
            if left_pressed and right_pressed:
                if not self.running and self.enabled and not self.paused:
                    self._start_recoil()
            else:
                if self.running:
                    self._stop_recoil()
            
            # 检查侧键1按下
            if side1_pressed and not self.side_button1_pressed:
                # 根据设置决定是切换上一个还是下一个倍率
                if self.scope_prev_key == "侧键1":
                    self.switch_scope(-1)
                elif self.scope_next_key == "侧键1":
                    self.switch_scope(1)
            
            # 检查侧键2按下
            if side2_pressed and not self.side_button2_pressed:
                # 根据设置决定是切换上一个还是下一个倍率
                if self.scope_prev_key == "侧键2":
                    self.switch_scope(-1)
                elif self.scope_next_key == "侧键2":
                    self.switch_scope(1)
            
            # 更新按键状态
            self.left_button_pressed = left_pressed
            self.right_button_pressed = right_pressed
            self.side_button1_pressed = side1_pressed
            self.side_button2_pressed = side2_pressed
            
            time.sleep(0.001)  # 1ms轮询间隔
    
    def _start_recoil(self):
        """开始压枪"""
        if not self.current_weapon:
            self.log("未选择武器", "WARNING")
            return
        
        weapon = self.weapons.get(self.current_weapon)
        if not weapon:
            self.log(f"武器配置不存在: {self.current_weapon}", "ERROR")
            return
        
        if not weapon.get("enabled", True):
            self.log(f"武器已禁用: {self.current_weapon}", "WARNING")
            return
        
        self.running = True
        self.update_status("压枪中...")
        self.log(f"开始压枪: {weapon['name']}")
        
        # 启动压枪线程
        self.recoil_thread = threading.Thread(
            target=self._execute_recoil_pattern,
            args=(weapon,),
            daemon=True
        )
        self.recoil_thread.start()
    
    def _stop_recoil(self):
        """停止压枪"""
        self.running = False
        self.update_status("已启用")
        self.log("停止压枪")
    
    def _execute_recoil_pattern(self, weapon):
        """执行压枪轨迹 - 与LUA脚本execute_recoil_precise完全一致
        
        LUA核心逻辑：
        1. 每个pattern点执行5次内循环 (for _ = 1, 5 do)
        2. 使用math.ceil取整移动量
        3. 使用高精度忙等待计时（累积延迟保持精度）
        4. 应用BASE_YQXS基础灵敏度 × 倍率
        """
        # 优先使用lua_pattern（包含x, y, d的完整数据）
        lua_pattern = weapon.get("lua_pattern", [])
        pattern = weapon.get("pattern", [])
        fire_rate = weapon.get("fire_rate", 10)
        
        # 如果没有lua_pattern，从pattern构建
        if not lua_pattern and pattern and len(pattern) > 0:
            if isinstance(pattern[0], (int, float)):
                # 普通格式：数字列表
                lua_pattern = [{"x": 0, "y": y, "d": fire_rate} for y in pattern]
            elif isinstance(pattern[0], dict):
                # LUA格式：字典列表，直接使用
                lua_pattern = pattern
        
        if not lua_pattern:
            self.log("压枪模式为空", "WARNING")
            return
        
        # 获取基础灵敏度（与LUA的BASE_YQXS对应）
        base_yqxs_y = weapon.get("base_yqxs_y", 1.0)
        base_yqxs_x = weapon.get("base_yqxs_x", 1.0)
        
        # 获取力度控制（类型保护，防止JSON中存储为字符串）
        strength = float(weapon.get("strength", 1.0))
        
        # 获取全局力度（所有武器共享）
        global_strength = float(self.settings.get("global_strength", 1.0))
        
        # 使用武器自己的倍率数组
        multipliers = weapon.get("multipliers", [1.0])
        current_index = weapon.get("current_multiplier_index", 0)
        
        # 确保索引有效
        if current_index >= len(multipliers):
            current_index = 0
        
        # 获取当前倍率（与LUA的current_multiplier对应）
        scope_multiplier = multipliers[current_index]
        
        # 计算实际灵敏度（基础 × 力度 × 全局力度 × 倍率，与LUA一致）
        actual_yqxs_y = base_yqxs_y * strength * global_strength * scope_multiplier
        actual_yqxs_x = base_yqxs_x * strength * global_strength * scope_multiplier
        
        # 高精度计时：使用performance_counter获取起始时间戳
        anchor = time.perf_counter()
        total_delay = 0.0  # 累积延迟（保持小数精度，与LUA一致）
        
        # 获取触发模式（与LUA的MODE对应）
        # MODE=1: 仅左键触发, MODE=2: 左键+右键触发（默认）
        mode = weapon.get("mode", self.settings.get("mode", 2))
        
        # 与LUA一致：遍历每个pattern点
        for i in range(len(lua_pattern)):
            point = lua_pattern[i]
            move_x = point.get("x", 0)
            move_y = point.get("y", 0)
            delay = point.get("d", fire_rate)
            
            # 与LUA一致：每个pattern点执行5次内循环
            for _ in range(5):
                # 检查是否仍然按下鼠标键（根据MODE模式）
                left_state = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON)
                left_pressed = (left_state & 0x8000) != 0
                
                if mode == 1:
                    # MODE=1: 仅检查左键
                    if not left_pressed:
                        return
                else:
                    # MODE=2: 检查左键+右键
                    right_state = ctypes.windll.user32.GetAsyncKeyState(VK_RBUTTON)
                    right_pressed = (right_state & 0x8000) != 0
                    if not (left_pressed and right_pressed):
                        return
                
                # 累积延迟时间（保持小数精度，与LUA的total_delay = total_delay + pattern[i].d一致）
                total_delay += delay
                
                # 计算目标时间点（与LUA的target_time = anchor + math.floor(total_delay + 0.5)一致）
                target_time = anchor + (math.floor(total_delay + 0.5) / 1000.0)
                
                # 高精度忙等待（与LUA的while GetRunningTime() < target_time do end一致）
                while time.perf_counter() < target_time:
                    pass
                
                # 执行鼠标移动（与LUA的MoveMouseRelative(math.ceil(...), math.ceil(...))一致）
                # 添加+-0.001的随机偏移，防止反作弊检测
                offset_x = (random.random() * 2 - 1) * 0.001  # -0.001 ~ +0.001
                offset_y = (random.random() * 2 - 1) * 0.001  # -0.001 ~ +0.001
                
                if self.ib_input:
                    int_x = math.ceil(actual_yqxs_x * (move_x + offset_x))
                    int_y = math.ceil(actual_yqxs_y * (move_y + offset_y))
                    
                    if int_x != 0 or int_y != 0:
                        try:
                            self.ib_input.IbSendMouseMove(int_x, int_y, 1)
                        except Exception as e:
                            self.log(f"鼠标移动失败: {e}", "ERROR")
                
                # 检查运行状态
                if not self.running or self.stop_event.is_set():
                    return
    
    def enable(self):
        """启用压枪功能"""
        self.enabled = True
        self.update_status("已启用")
        self.log("压枪功能已启用")
    
    def disable(self):
        """禁用压枪功能"""
        self.enabled = False
        self.running = False
        self.update_status("已禁用")
        self.log("压枪功能已禁用")
    
    def pause(self):
        """暂停压枪功能"""
        self.paused = True
        self.update_status("已暂停")
        self.log("压枪功能已暂停")
    
    def resume(self):
        """恢复压枪功能"""
        self.paused = False
        self.update_status("已启用")
        self.log("压枪功能已恢复")
    
    def set_scope_multipliers(self, multipliers):
        """设置倍镜列表"""
        if multipliers and isinstance(multipliers, list):
            self.scope_multipliers = [float(m) for m in multipliers]
            self.current_scope_index = 0
            self.current_scope_multiplier = self.scope_multipliers[0] if self.scope_multipliers else 1.0
            self.log(f"倍镜列表已更新: {self.scope_multipliers}")
    
    def set_scope_hotkeys(self, prev_key, next_key):
        """设置倍镜切换快捷键"""
        self.scope_prev_key = prev_key
        self.scope_next_key = next_key
        self.log(f"倍镜切换快捷键已更新: 上一个={prev_key}, 下一个={next_key}")
    
    def switch_scope(self, direction=1):
        """切换倍镜
        direction: 1=下一个, -1=上一个
        """
        if not self.current_weapon:
            self.log("没有选择武器，无法切换倍镜", "WARNING")
            return
        
        weapon = self.get_weapon(self.current_weapon)
        if not weapon:
            self.log("武器不存在", "WARNING")
            return
        
        # 获取武器的倍率数组
        multipliers = weapon.get("multipliers", [1.0])
        if not multipliers:
            self.log("武器没有倍率数组", "WARNING")
            return
        
        # 获取当前倍率索引
        current_index = weapon.get("current_multiplier_index", 0)
        
        # 切换倍率索引
        new_index = (current_index + direction) % len(multipliers)
        
        # 更新武器配置
        weapon["current_multiplier_index"] = new_index
        
        # 保存武器配置
        self.update_weapon(self.current_weapon, weapon)
        
        # 获取新的倍率
        new_multiplier = multipliers[new_index]
        
        self.log(f"切换倍镜: {new_multiplier}x (第{new_index + 1}档，共{len(multipliers)}档)")
        self.update_status(f"倍镜: {new_multiplier}x")
    
    def get_current_scope(self):
        """获取当前倍镜倍率"""
        if not self.current_weapon:
            return 1.0
        
        weapon = self.get_weapon(self.current_weapon)
        if not weapon:
            return 1.0
        
        multipliers = weapon.get("multipliers", [1.0])
        current_index = weapon.get("current_multiplier_index", 0)
        
        if current_index >= len(multipliers):
            return 1.0
        
        return multipliers[current_index]
    
    def get_weapon_scope_info(self):
        """获取当前武器的倍率信息"""
        if not self.current_weapon:
            return {"multipliers": [1.0], "current_index": 0, "current_multiplier": 1.0}
        
        weapon = self.get_weapon(self.current_weapon)
        if not weapon:
            return {"multipliers": [1.0], "current_index": 0, "current_multiplier": 1.0}
        
        multipliers = weapon.get("multipliers", [1.0])
        current_index = weapon.get("current_multiplier_index", 0)
        
        if current_index >= len(multipliers):
            current_index = 0
        
        return {
            "multipliers": multipliers,
            "current_index": current_index,
            "current_multiplier": multipliers[current_index]
        }
    
    def is_enabled(self):
        """是否已启用"""
        return self.enabled
    
    def is_running(self):
        """是否正在压枪"""
        return self.running
    
    def is_paused(self):
        """是否已暂停"""
        return self.paused
    
    def get_status(self):
        """获取当前状态"""
        if not self.enabled:
            return "已禁用"
        elif self.paused:
            return "已暂停"
        elif self.running:
            return "压枪中..."
        else:
            return "已启用"
    
    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        self.running = False
        self.log("资源已清理")

# 测试代码
if __name__ == "__main__":
    # 创建压枪核心实例
    is_packaged = not sys.argv[0].endswith('.py')
    if is_packaged:
        config_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config")
    else:
        # 开发模式：__file__ 在 src/ 下，项目根目录是上一级
        src_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(src_dir), "config")
    core = RecoilCore(config_dir)
    
    # 设置回调函数
    def log_callback(message):
        print(message)
    
    def status_callback(status):
        print(f"状态: {status}")
    
    core.set_log_callback(log_callback)
    core.set_status_callback(status_callback)
    
    # 测试功能
    print("测试压枪核心模块...")
    
    # 获取武器列表
    weapons = core.get_weapon_list()
    print(f"武器列表: {weapons}")
    
    # 选择武器
    if weapons:
        core.set_current_weapon(weapons[0])
    
    # 启用压枪
    core.enable()
    
    # 开始监听
    core.start_monitoring()
    
    print("按 Ctrl+C 停止测试...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止测试...")
        core.cleanup()