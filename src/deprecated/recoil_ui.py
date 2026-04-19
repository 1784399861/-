"""
IbInputSimulator 压枪软件 - 现代化UI版本
支持武器管理、参数设置、日志查询、联网配置
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
from datetime import datetime
import ctypes
import sys

# 设置UI主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RecoilControlUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("压枪控制中心 v1.0")
        self.root.geometry("1200x800")
        
        # 配置文件路径
        self.config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        self.weapons_file = os.path.join(self.config_dir, "weapons.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self.log_file = os.path.join(self.config_dir, "app.log")
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 加载配置
        self.weapons = self.load_weapons()
        self.settings = self.load_settings()
        
        # 当前选中的武器
        self.current_weapon = None
        
        # 压枪状态
        self.recoil_enabled = False
        self.recoil_running = False
        
        # 加载IbInputSimulator
        self.ib_input = None
        self.load_ib_input_simulator()
        
        # 创建UI
        self.create_ui()
        
        # 记录启动日志
        self.log("应用程序启动")
        
    def load_ib_input_simulator(self):
        """加载IbInputSimulator DLL"""
        try:
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "IbInputSimulator.dll")
            if os.path.exists(dll_path):
                self.ib_input = ctypes.CDLL(dll_path)
                self.ib_input.IbSendInit.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
                self.ib_input.IbSendInit.restype = ctypes.c_uint32
                self.ib_input.IbSendMouseMove.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
                self.ib_input.IbSendMouseMove.restype = ctypes.c_bool
                
                # 初始化
                result = self.ib_input.IbSendInit(1, 0, None)  # SendInput驱动
                if result == 0:
                    self.log("IbInputSimulator 加载成功")
                else:
                    self.log(f"IbInputSimulator 初始化失败: {result}", "ERROR")
            else:
                self.log("未找到 IbInputSimulator.dll", "ERROR")
        except Exception as e:
            self.log(f"加载 IbInputSimulator 失败: {e}", "ERROR")
    
    def load_weapons(self):
        """加载武器配置"""
        if os.path.exists(self.weapons_file):
            try:
                with open(self.weapons_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        # 默认武器配置
        return {
            "M416": {
                "name": "M416",
                "pattern": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                "fire_rate": 10,
                "enabled": True,
                "description": "突击步枪 - 稳定型"
            },
            "AKM": {
                "name": "AKM",
                "pattern": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
                "fire_rate": 10,
                "enabled": True,
                "description": "突击步枪 - 高伤害"
            },
            "SCAR-L": {
                "name": "SCAR-L",
                "pattern": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                "fire_rate": 10,
                "enabled": True,
                "description": "突击步枪 - 全面型"
            }
        }
    
    def save_weapons(self):
        """保存武器配置"""
        try:
            with open(self.weapons_file, 'w', encoding='utf-8') as f:
                json.dump(self.weapons, f, ensure_ascii=False, indent=2)
            self.log("武器配置已保存")
        except Exception as e:
            self.log(f"保存武器配置失败: {e}", "ERROR")
    
    def load_settings(self):
        """加载设置"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "hotkey": "F1",
            "fire_button": "LButton",
            "move_interval": 10,
            "auto_start": False,
            "minimize_to_tray": True,
            "log_level": "INFO"
        }
    
    def save_settings(self):
        """保存设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            self.log("设置已保存")
        except Exception as e:
            self.log(f"保存设置失败: {e}", "ERROR")
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except:
            pass
        
        # 更新UI日志显示
        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", log_entry + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
    
    def create_ui(self):
        """创建UI界面"""
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建左侧武器选择面板
        self.create_weapon_panel()
        
        # 创建右侧参数设置面板
        self.create_settings_panel()
        
        # 创建底部日志面板
        self.create_log_panel()
        
        # 创建顶部状态栏
        self.create_status_bar()
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ctk.CTkFrame(self.main_frame, height=40)
        self.status_frame.pack(fill="x", pady=(0, 10))
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="状态: 就绪",
            font=("Arial", 12)
        )
        self.status_label.pack(side="left", padx=10)
        
        # 启用/禁用开关
        self.enable_switch = ctk.CTkSwitch(
            self.status_frame,
            text="启用压枪",
            command=self.toggle_recoil,
            font=("Arial", 12)
        )
        self.enable_switch.pack(side="right", padx=10)
        
        # 当前武器显示
        self.current_weapon_label = ctk.CTkLabel(
            self.status_frame,
            text="当前武器: 无",
            font=("Arial", 12)
        )
        self.current_weapon_label.pack(side="right", padx=10)
    
    def create_weapon_panel(self):
        """创建武器选择面板"""
        self.weapon_frame = ctk.CTkFrame(self.main_frame, width=300)
        self.weapon_frame.pack(side="left", fill="y", padx=(0, 10))
        self.weapon_frame.pack_propagate(False)
        
        # 标题
        title_label = ctk.CTkLabel(
            self.weapon_frame,
            text="武器库",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 武器列表
        self.weapon_list_frame = ctk.CTkScrollableFrame(self.weapon_frame)
        self.weapon_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 刷新武器列表
        self.refresh_weapon_list()
        
        # 按钮框架
        button_frame = ctk.CTkFrame(self.weapon_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 新增武器按钮
        add_button = ctk.CTkButton(
            button_frame,
            text="新增武器",
            command=self.add_weapon,
            width=120
        )
        add_button.pack(side="left", padx=5)
        
        # 删除武器按钮
        delete_button = ctk.CTkButton(
            button_frame,
            text="删除武器",
            command=self.delete_weapon,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(side="right", padx=5)
    
    def refresh_weapon_list(self):
        """刷新武器列表"""
        # 清空现有列表
        for widget in self.weapon_list_frame.winfo_children():
            widget.destroy()
        
        # 添加武器项
        for weapon_id, weapon in self.weapons.items():
            self.create_weapon_item(weapon_id, weapon)
    
    def create_weapon_item(self, weapon_id, weapon):
        """创建武器列表项"""
        item_frame = ctk.CTkFrame(self.weapon_list_frame)
        item_frame.pack(fill="x", pady=2)
        
        # 武器名称
        name_label = ctk.CTkLabel(
            item_frame,
            text=weapon["name"],
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        name_label.pack(side="left", padx=5)
        
        # 启用状态
        enabled_label = ctk.CTkLabel(
            item_frame,
            text="✓" if weapon.get("enabled", True) else "✗",
            font=("Arial", 12),
            text_color="green" if weapon.get("enabled", True) else "red"
        )
        enabled_label.pack(side="right", padx=5)
        
        # 点击事件
        def on_click(event, wid=weapon_id):
            self.select_weapon(wid)
        
        item_frame.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        enabled_label.bind("<Button-1>", on_click)
        
        # 高亮当前选中的武器
        if self.current_weapon == weapon_id:
            item_frame.configure(fg_color=("gray70", "gray30"))
    
    def select_weapon(self, weapon_id):
        """选择武器"""
        self.current_weapon = weapon_id
        weapon = self.weapons[weapon_id]
        
        # 更新状态栏
        self.current_weapon_label.configure(text=f"当前武器: {weapon['name']}")
        
        # 更新参数显示
        self.update_weapon_params(weapon)
        
        # 刷新武器列表以更新高亮
        self.refresh_weapon_list()
        
        self.log(f"选择武器: {weapon['name']}")
    
    def update_weapon_params(self, weapon):
        """更新武器参数显示"""
        # 更新名称
        self.weapon_name_entry.delete(0, "end")
        self.weapon_name_entry.insert(0, weapon["name"])
        
        # 更新描述
        self.weapon_desc_entry.delete(0, "end")
        self.weapon_desc_entry.insert(0, weapon.get("description", ""))
        
        # 更新压枪模式
        pattern_str = ", ".join(str(x) for x in weapon["pattern"])
        self.pattern_text.delete("1.0", "end")
        self.pattern_text.insert("1.0", pattern_str)
        
        # 更新射速
        self.fire_rate_entry.delete(0, "end")
        self.fire_rate_entry.insert(0, str(weapon.get("fire_rate", 10)))
        
        # 更新启用状态
        self.enabled_var.set(weapon.get("enabled", True))
    
    def add_weapon(self):
        """新增武器"""
        # 创建新武器对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("新增武器")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 武器名称
        ctk.CTkLabel(dialog, text="武器名称:").pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(pady=5)
        
        # 武器描述
        ctk.CTkLabel(dialog, text="武器描述:").pack(pady=5)
        desc_entry = ctk.CTkEntry(dialog, width=300)
        desc_entry.pack(pady=5)
        
        # 压枪模式
        ctk.CTkLabel(dialog, text="压枪模式 (逗号分隔):").pack(pady=5)
        pattern_entry = ctk.CTkEntry(dialog, width=300)
        pattern_entry.insert(0, "2, 3, 4, 5, 6, 7, 8, 9, 10")
        pattern_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("错误", "请输入武器名称")
                return
            
            try:
                pattern = [int(x.strip()) for x in pattern_entry.get().split(",")]
            except:
                messagebox.showerror("错误", "压枪模式格式错误")
                return
            
            # 创建新武器
            self.weapons[name] = {
                "name": name,
                "pattern": pattern,
                "fire_rate": 10,
                "enabled": True,
                "description": desc_entry.get().strip()
            }
            
            self.save_weapons()
            self.refresh_weapon_list()
            self.log(f"新增武器: {name}")
            dialog.destroy()
        
        # 保存按钮
        ctk.CTkButton(dialog, text="保存", command=save).pack(pady=20)
    
    def delete_weapon(self):
        """删除武器"""
        if not self.current_weapon:
            messagebox.showwarning("警告", "请先选择要删除的武器")
            return
        
        weapon_name = self.weapons[self.current_weapon]["name"]
        if messagebox.askyesno("确认", f"确定要删除武器 '{weapon_name}' 吗？"):
            del self.weapons[self.current_weapon]
            self.save_weapons()
            self.current_weapon = None
            self.current_weapon_label.configure(text="当前武器: 无")
            self.refresh_weapon_list()
            self.log(f"删除武器: {weapon_name}")
    
    def create_settings_panel(self):
        """创建参数设置面板"""
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_frame.pack(side="right", fill="both", expand=True)
        
        # 创建选项卡
        self.tabview = ctk.CTkTabview(self.settings_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 武器参数选项卡
        self.weapon_tab = self.tabview.add("武器参数")
        self.create_weapon_params_tab()
        
        # 全局设置选项卡
        self.global_tab = self.tabview.add("全局设置")
        self.create_global_settings_tab()
        
        # 网络配置选项卡
        self.network_tab = self.tabview.add("网络配置")
        self.create_network_tab()
    
    def create_weapon_params_tab(self):
        """创建武器参数选项卡"""
        # 武器名称
        name_frame = ctk.CTkFrame(self.weapon_tab)
        name_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(name_frame, text="武器名称:", width=100).pack(side="left", padx=5)
        self.weapon_name_entry = ctk.CTkEntry(name_frame, width=200)
        self.weapon_name_entry.pack(side="left", padx=5)
        
        # 武器描述
        desc_frame = ctk.CTkFrame(self.weapon_tab)
        desc_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(desc_frame, text="武器描述:", width=100).pack(side="left", padx=5)
        self.weapon_desc_entry = ctk.CTkEntry(desc_frame, width=200)
        self.weapon_desc_entry.pack(side="left", padx=5)
        
        # 压枪模式
        pattern_frame = ctk.CTkFrame(self.weapon_tab)
        pattern_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(pattern_frame, text="压枪模式:", width=100).pack(side="left", padx=5)
        self.pattern_text = ctk.CTkTextbox(pattern_frame, width=200, height=100)
        self.pattern_text.pack(side="left", padx=5)
        
        # 射速
        fire_rate_frame = ctk.CTkFrame(self.weapon_tab)
        fire_rate_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(fire_rate_frame, text="射速(ms):", width=100).pack(side="left", padx=5)
        self.fire_rate_entry = ctk.CTkEntry(fire_rate_frame, width=200)
        self.fire_rate_entry.pack(side="left", padx=5)
        
        # 启用状态
        enabled_frame = ctk.CTkFrame(self.weapon_tab)
        enabled_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(enabled_frame, text="启用状态:", width=100).pack(side="left", padx=5)
        self.enabled_var = ctk.BooleanVar(value=True)
        self.enabled_checkbox = ctk.CTkCheckBox(
            enabled_frame, 
            text="启用此武器", 
            variable=self.enabled_var
        )
        self.enabled_checkbox.pack(side="left", padx=5)
        
        # 保存按钮
        save_button = ctk.CTkButton(
            self.weapon_tab,
            text="保存武器参数",
            command=self.save_weapon_params,
            width=200
        )
        save_button.pack(pady=20)
    
    def save_weapon_params(self):
        """保存武器参数"""
        if not self.current_weapon:
            messagebox.showwarning("警告", "请先选择武器")
            return
        
        try:
            # 获取参数
            name = self.weapon_name_entry.get().strip()
            desc = self.weapon_desc_entry.get().strip()
            pattern_str = self.pattern_text.get("1.0", "end-1c").strip()
            fire_rate = int(self.fire_rate_entry.get().strip())
            enabled = self.enabled_var.get()
            
            # 解析压枪模式
            pattern = [int(x.strip()) for x in pattern_str.split(",")]
            
            # 更新武器配置
            self.weapons[self.current_weapon] = {
                "name": name,
                "pattern": pattern,
                "fire_rate": fire_rate,
                "enabled": enabled,
                "description": desc
            }
            
            self.save_weapons()
            self.refresh_weapon_list()
            self.log(f"保存武器参数: {name}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def create_global_settings_tab(self):
        """创建全局设置选项卡"""
        # 热键设置
        hotkey_frame = ctk.CTkFrame(self.global_tab)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(hotkey_frame, text="开关热键:", width=100).pack(side="left", padx=5)
        self.hotkey_entry = ctk.CTkEntry(hotkey_frame, width=200)
        self.hotkey_entry.insert(0, self.settings.get("hotkey", "F1"))
        self.hotkey_entry.pack(side="left", padx=5)
        
        # 开火键设置
        fire_button_frame = ctk.CTkFrame(self.global_tab)
        fire_button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(fire_button_frame, text="开火键:", width=100).pack(side="left", padx=5)
        self.fire_button_entry = ctk.CTkEntry(fire_button_frame, width=200)
        self.fire_button_entry.insert(0, self.settings.get("fire_button", "LButton"))
        self.fire_button_entry.pack(side="left", padx=5)
        
        # 移动间隔
        interval_frame = ctk.CTkFrame(self.global_tab)
        interval_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(interval_frame, text="移动间隔(ms):", width=100).pack(side="left", padx=5)
        self.interval_entry = ctk.CTkEntry(interval_frame, width=200)
        self.interval_entry.insert(0, str(self.settings.get("move_interval", 10)))
        self.interval_entry.pack(side="left", padx=5)
        
        # 自动启动
        auto_start_frame = ctk.CTkFrame(self.global_tab)
        auto_start_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_start_var = ctk.BooleanVar(value=self.settings.get("auto_start", False))
        self.auto_start_checkbox = ctk.CTkCheckBox(
            auto_start_frame,
            text="开机自动启动",
            variable=self.auto_start_var
        )
        self.auto_start_checkbox.pack(side="left", padx=5)
        
        # 保存设置按钮
        save_settings_button = ctk.CTkButton(
            self.global_tab,
            text="保存全局设置",
            command=self.save_global_settings,
            width=200
        )
        save_settings_button.pack(pady=20)
    
    def save_global_settings(self):
        """保存全局设置"""
        try:
            self.settings["hotkey"] = self.hotkey_entry.get().strip()
            self.settings["fire_button"] = self.fire_button_entry.get().strip()
            self.settings["move_interval"] = int(self.interval_entry.get().strip())
            self.settings["auto_start"] = self.auto_start_var.get()
            
            self.save_settings()
            self.log("全局设置已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def create_network_tab(self):
        """创建网络配置选项卡"""
        # 服务器地址
        server_frame = ctk.CTkFrame(self.network_tab)
        server_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(server_frame, text="配置服务器:", width=100).pack(side="left", padx=5)
        self.server_entry = ctk.CTkEntry(server_frame, width=300)
        self.server_entry.insert(0, "https://api.example.com/weapons")
        self.server_entry.pack(side="left", padx=5)
        
        # 同步按钮
        sync_button = ctk.CTkButton(
            self.network_tab,
            text="同步武器配置",
            command=self.sync_weapons,
            width=200
        )
        sync_button.pack(pady=10)
        
        # 检查更新按钮
        update_button = ctk.CTkButton(
            self.network_tab,
            text="检查更新",
            command=self.check_updates,
            width=200
        )
        update_button.pack(pady=10)
        
        # 状态显示
        self.network_status = ctk.CTkLabel(
            self.network_tab,
            text="状态: 未连接",
            font=("Arial", 12)
        )
        self.network_status.pack(pady=10)
    
    def sync_weapons(self):
        """同步武器配置"""
        self.network_status.configure(text="状态: 正在同步...")
        self.log("开始同步武器配置")
        
        # 模拟网络请求
        def sync_thread():
            time.sleep(2)  # 模拟网络延迟
            self.root.after(0, lambda: self.network_status.configure(text="状态: 同步完成"))
            self.log("武器配置同步完成")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def check_updates(self):
        """检查更新"""
        self.network_status.configure(text="状态: 检查更新中...")
        self.log("检查更新")
        
        # 模拟检查更新
        def check_thread():
            time.sleep(1)
            self.root.after(0, lambda: self.network_status.configure(text="状态: 已是最新版本"))
            self.log("检查更新完成: 已是最新版本")
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def create_log_panel(self):
        """创建日志面板"""
        self.log_frame = ctk.CTkFrame(self.main_frame, height=150)
        self.log_frame.pack(fill="x", pady=(10, 0))
        self.log_frame.pack_propagate(False)
        
        # 标题和控制按钮
        header_frame = ctk.CTkFrame(self.log_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="运行日志", font=("Arial", 12, "bold")).pack(side="left")
        
        # 清空日志按钮
        clear_button = ctk.CTkButton(
            header_frame,
            text="清空日志",
            command=self.clear_log,
            width=80,
            height=25
        )
        clear_button.pack(side="right", padx=5)
        
        # 导出日志按钮
        export_button = ctk.CTkButton(
            header_frame,
            text="导出日志",
            command=self.export_log,
            width=80,
            height=25
        )
        export_button.pack(side="right", padx=5)
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(self.log_frame, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
    
    def clear_log(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空日志吗？"):
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")
            self.log("日志已清空")
    
    def export_log(self):
        """导出日志"""
        try:
            export_file = os.path.join(self.config_dir, f"log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get("1.0", "end"))
            messagebox.showinfo("成功", f"日志已导出到: {export_file}")
            self.log(f"日志已导出到: {export_file}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def toggle_recoil(self):
        """切换压枪状态"""
        self.recoil_enabled = not self.recoil_enabled
        if self.recoil_enabled:
            self.status_label.configure(text="状态: 已启用")
            self.log("压枪功能已启用")
        else:
            self.status_label.configure(text="状态: 已禁用")
            self.log("压枪功能已禁用")
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

def main():
    """主函数"""
    app = RecoilControlUI()
    app.run()

if __name__ == "__main__":
    main()