"""
IbInputSimulator 压枪软件 - 现代化UI版本 v2.0
集成压枪核心模块，支持鼠标左键+右键触发
"""

# ====== 极早初始化：诊断日志 + 崩溃捕获 ======
# 必须在所有其他 import 之前，确保任何阶段崩溃都能记录
import sys
import os
import traceback as _tb

def _get_app_dir():
    """获取项目根目录（用于读写 config、vendor 等持久化文件）
    
    打包模式（Nuitka / PyInstaller onefile）：
    - sys.argv[0] → exe 实际所在路径（用户双击的文件）
    - config 等文件在 exe 同目录下
    
    开发模式（python src/recoil_ui_v2.py）：
    - __file__ 在 src/ 目录下
    - 项目根目录是 src/ 的上一级
    - config/、vendor/ 等在项目根目录下
    """
    is_packaged = not sys.argv[0].endswith('.py')
    if is_packaged:
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # __file__ = .../src/recoil_ui_v2.py → 项目根 = 上一级
        src_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(src_dir)

_APP_DIR = _get_app_dir()
_DIAG_LOG_PATH = os.path.join(_APP_DIR, "crash.log")

def _write_diag(msg):
    """写入诊断日志（极简，不依赖任何外部模块）"""
    try:
        with open(_DIAG_LOG_PATH, "a", encoding="utf-8") as f:
            from datetime import datetime as _dt
            f.write(f"[{_dt.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# 立即写第一条日志——如果这条都没有，说明 Python 运行时本身就加载不了
_write_diag("=" * 50)
_write_diag(f"程序启动 sys.argv[0]={sys.argv[0]}")
_write_diag(f"_APP_DIR={_APP_DIR}")
_write_diag(f"sys.executable={sys.executable}")
_write_diag(f"__file__={__file__}")

# 安装全局未捕获异常处理器
def _global_exception_handler(exc_type, exc_value, exc_tb):
    error = "".join(_tb.format_exception(exc_type, exc_value, exc_tb))
    _write_diag(f"FATAL ERROR:\n{error}")
    try:
        import tkinter as _tk
        _r = _tk.Tk(); _r.withdraw()
        from tkinter import messagebox as _mb
        _mb.showerror("程序崩溃", f"启动失败:\n\n{error[:600]}\n\n日志: {_DIAG_LOG_PATH}")
        _r.destroy()
    except Exception:
        pass

sys.excepthook = _global_exception_handler

# ====== 正常导入 ======
_write_diag("开始导入模块...")

import customtkinter as ctk
_write_diag("✓ customtkinter")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
_write_diag("✓ tkinter")

import json
import threading
import time
from datetime import datetime

# APP_DIR 已在上面定义
APP_DIR = _APP_DIR

# 软件版本
SOFTWARE_VERSION = "1.0.3"

# 添加当前目录到Python路径
sys.path.insert(0, APP_DIR)

# 导入压枪核心模块
_write_diag("导入 recoil_core...")
from recoil_core import RecoilCore
_write_diag("✓ recoil_core")

# 导入数据同步模块
_write_diag("导入 auto_updater...")
from auto_updater import ConfigSyncer, check_for_config_update, get_local_data_version
_write_diag("✓ auto_updater")

# 设置UI主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RecoilControlUIv2:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("压枪控制中心 v2.0")
        self.root.geometry("1200x800")
        
        # 配置文件路径
        # APP_DIR 在打包模式下指向 exe 同目录，普通模式下指向脚本目录
        self.config_dir = os.path.join(APP_DIR, "config")
        
        # 确保 config 目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 创建压枪核心实例
        self.core = RecoilCore(self.config_dir)
        
        # 设置回调函数
        self.core.set_log_callback(self.on_log)
        self.core.set_status_callback(self.on_status_change)
        
        # 创建UI
        self.create_ui()
        
        # 初始化数据
        self.initialize_data()
        
        # 开始监听鼠标按键
        self.core.start_monitoring()
        
        # 记录启动日志
        self.core.log("应用程序启动")
        
    def on_log(self, message):
        """日志回调函数（线程安全：调度到主线程执行）"""
        if hasattr(self, 'log_text') and hasattr(self, 'root'):
            self.root.after(0, lambda: self._append_log(message))
    
    def _append_log(self, message):
        """在主线程中追加日志"""
        if hasattr(self, 'log_text'):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
    
    def on_status_change(self, status):
        """状态变化回调函数"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=f"状态: {status}")
        
        # 更新当前倍镜显示
        self.update_current_scope_display()
    
    def update_current_scope_display(self):
        """更新当前倍镜显示"""
        if hasattr(self, 'current_scope_label'):
            scope_info = self.core.get_weapon_scope_info()
            current_multiplier = scope_info.get("current_multiplier", 1.0)
            self.current_scope_label.configure(text=f"当前倍镜: {current_multiplier}x")
    
    def initialize_data(self):
        """初始化数据"""
        # 加载倍镜列表设置
        scope_multipliers = self.core.settings.get("scope_multipliers", [1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0])
        self.core.set_scope_multipliers(scope_multipliers)
        
        # 创建武器图片目录
        self.weapon_images_dir = os.path.join(self.config_dir, "weapon_images")
        if not os.path.exists(self.weapon_images_dir):
            os.makedirs(self.weapon_images_dir)
        
        # 刷新武器列表
        self.refresh_weapon_list()
        
        # 如果有武器，选择第一个
        weapons = self.core.get_weapon_list()
        if weapons:
            self.select_weapon(weapons[0])
    
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
        
        # 版本标签
        self.version_label = ctk.CTkLabel(
            self.status_frame, 
            text=f"v{SOFTWARE_VERSION}",
            font=("Arial", 10),
            text_color="gray"
        )
        self.version_label.pack(side="left", padx=5)
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="状态: 已禁用",
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
        
        # 触发方式提示
        trigger_label = ctk.CTkLabel(
            self.status_frame,
            text="触发方式: 鼠标左键+右键",
            font=("Arial", 10),
            text_color="gray"
        )
        trigger_label.pack(side="right", padx=10)
    
    def create_weapon_panel(self):
        """创建武器选择面板"""
        self.weapon_frame = ctk.CTkFrame(self.main_frame, width=300)
        self.weapon_frame.pack(side="left", fill="y", padx=(0, 10))
        self.weapon_frame.pack_propagate(False)
        
        # 标题行（武器库 + 全选/取消）
        title_row = ctk.CTkFrame(self.weapon_frame)
        title_row.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(
            title_row,
            text="武器库",
            font=("Arial", 16, "bold")
        ).pack(side="left")
        
        # 全选/取消按钮
        self.select_all_btn = ctk.CTkButton(
            title_row,
            text="全选",
            command=self.toggle_select_all,
            width=55,
            height=26,
            font=("Arial", 11),
            fg_color="gray",
            hover_color="dimgray"
        )
        self.select_all_btn.pack(side="right", padx=2)
        
        # 搜索框
        search_frame = ctk.CTkFrame(self.weapon_frame)
        search_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(search_frame, text="搜索:", font=("Arial", 10)).pack(side="left", padx=2)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="输入武器名称...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=2)
        
        # 搜索框变化时过滤列表（防抖：停止输入300ms后才执行，避免频繁刷新）
        self._search_after_id = None
        def on_search_change(*args):
            if self._search_after_id:
                self.root.after_cancel(self._search_after_id)
            self._search_after_id = self.root.after(300, self._filter_weapon_list)
        
        self.search_entry.bind("<KeyRelease>", on_search_change)
        
        # 武器列表（带复选框）
        self.weapon_list_frame = ctk.CTkScrollableFrame(self.weapon_frame)
        self.weapon_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        # grid 列配置：让武器项占满宽度
        self.weapon_list_frame.columnconfigure(0, weight=1)
        
        # 批量操作按钮框架
        batch_frame = ctk.CTkFrame(self.weapon_frame)
        batch_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        # 批量删除按钮
        batch_delete_btn = ctk.CTkButton(
            batch_frame,
            text="批量删除",
            command=self.batch_delete_weapons,
            width=90,
            fg_color="#c0392b",
            hover_color="#962d22"
        )
        batch_delete_btn.pack(side="left", padx=2)
        
        # 批量启用按钮
        batch_enable_btn = ctk.CTkButton(
            batch_frame,
            text="批量启用",
            command=lambda: self.batch_set_enabled(True),
            width=90,
            fg_color="#27ae60",
            hover_color="#1e8449"
        )
        batch_enable_btn.pack(side="left", padx=2)
        
        # 批量禁用按钮
        batch_disable_btn = ctk.CTkButton(
            batch_frame,
            text="批量禁用",
            command=lambda: self.batch_set_enabled(False),
            width=90,
            fg_color="#e67e22",
            hover_color="#b86318"
        )
        batch_disable_btn.pack(side="left", padx=2)
        
        # 选中计数标签
        self.selected_count_label = ctk.CTkLabel(
            batch_frame,
            text="已选: 0",
            font=("Arial", 11),
            text_color="gray"
        )
        self.selected_count_label.pack(side="right", padx=5)
        
        # 功能按钮框架
        button_frame = ctk.CTkFrame(self.weapon_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # 新增武器按钮
        add_button = ctk.CTkButton(
            button_frame,
            text="新增武器",
            command=self.add_weapon,
            width=90
        )
        add_button.pack(side="left", padx=2)
        
        # 导入LUA按钮
        import_button = ctk.CTkButton(
            button_frame,
            text="导入LUA",
            command=self.import_lua,
            width=90,
            fg_color="green",
            hover_color="darkgreen"
        )
        import_button.pack(side="left", padx=2)
        
        # 轨迹录制按钮
        record_button = ctk.CTkButton(
            button_frame,
            text="轨迹录制",
            command=self.open_pattern_recorder,
            width=90,
            fg_color="orange",
            hover_color="darkorange"
        )
        record_button.pack(side="left", padx=2)
        
        # 删除武器按钮（单个）
        delete_button = ctk.CTkButton(
            button_frame,
            text="删除武器",
            command=self.delete_weapon,
            width=90,
            fg_color="red",
            hover_color="darkred"
        )
        delete_button.pack(side="right", padx=2)
        
        # 初始化选中状态字典
        self.weapon_selected_vars = {}  # {weapon_name: BooleanVar}
        self.weapon_item_frames = {}  # {weapon_name: item_frame} - 用于轻量级高亮更新
        self._weapon_order = {}  # {weapon_name: row_index} - grid 布局行号，保持搜索过滤时顺序稳定
        self.last_selected_weapon = None  # 记录上次选中的武器
        self.all_selected = False
    
    def _filter_weapon_list(self):
        """搜索过滤：只显示/隐藏武器项，不销毁重建（解决搜索卡顿问题）"""
        if not hasattr(self, 'search_entry'):
            return
        
        search_text = self.search_entry.get().strip().lower()
        
        for weapon_name, item_frame in self.weapon_item_frames.items():
            if search_text:
                if search_text in weapon_name.lower():
                    # grid 保持顺序稳定（row 由 _weapon_order 决定）
                    if weapon_name in self._weapon_order:
                        item_frame.grid(row=self._weapon_order[weapon_name], column=0, sticky="ew", pady=2)
                    else:
                        item_frame.grid(sticky="ew", pady=2)
                else:
                    item_frame.grid_remove()  # 隐藏但保留 grid 配置
            else:
                # 搜索框清空时，显示所有武器
                if weapon_name in self._weapon_order:
                    item_frame.grid(row=self._weapon_order[weapon_name], column=0, sticky="ew", pady=2)
                else:
                    item_frame.grid(sticky="ew", pady=2)
    
    def refresh_weapon_list(self):
        """刷新武器列表"""
        # 保存当前选中状态
        old_selected = {}
        for name, var in self.weapon_selected_vars.items():
            old_selected[name] = var.get()
        
        # 清空现有列表
        for widget in self.weapon_list_frame.winfo_children():
            widget.destroy()
        
        # 重置选中状态字典和武器项 frame 字典
        self.weapon_selected_vars = {}
        self.weapon_item_frames = {}
        self._weapon_order = {}
        self.last_selected_weapon = None
        
        # 添加武器项（按字母顺序排序）
        weapons = self.core.get_weapon_list()
        
        # 按字母顺序排序
        weapons_sorted = sorted(weapons)
        
        for row_idx, weapon_name in enumerate(weapons_sorted):
            self._weapon_order[weapon_name] = row_idx
            weapon = self.core.get_weapon(weapon_name)
            if weapon:
                self.create_weapon_item(weapon_name, weapon, old_selected.get(weapon_name, False))
        
        # 搜索过滤：如果有搜索文本，立即应用过滤
        self._filter_weapon_list()
        
        # 更新选中计数
        self.update_selected_count()
    
    def create_weapon_item(self, weapon_name, weapon, previously_selected=False):
        """创建武器列表项（带复选框）"""
        item_frame = ctk.CTkFrame(self.weapon_list_frame)
        # 使用 grid 布局，行号由 _weapon_order 决定，确保搜索过滤时顺序稳定
        row = self._weapon_order.get(weapon_name, len(self.weapon_item_frames))
        item_frame.grid(row=row, column=0, sticky="ew", pady=2)
        
        # 复选框
        selected_var = ctk.BooleanVar(value=previously_selected)
        self.weapon_selected_vars[weapon_name] = selected_var
        
        checkbox = ctk.CTkCheckBox(
            item_frame,
            text="",
            variable=selected_var,
            width=20,
            command=self.update_selected_count
        )
        checkbox.pack(side="left", padx=(5, 2))
        
        # 武器名称（点击可选中武器）
        name_label = ctk.CTkLabel(
            item_frame,
            text=weapon["name"],
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        name_label.pack(side="left", padx=2)
        
        # 启用状态
        enabled_label = ctk.CTkLabel(
            item_frame,
            text="✓" if weapon.get("enabled", True) else "✗",
            font=("Arial", 12),
            text_color="green" if weapon.get("enabled", True) else "red"
        )
        enabled_label.pack(side="right", padx=5)
        
        # 点击武器名称 → 选中该武器（显示参数）
        def on_click(event, name=weapon_name):
            self.select_weapon(name)
        
        # 右键菜单事件
        def on_right_click(event, name=weapon_name):
            self.show_weapon_context_menu(event, name)
        
        # 绑定事件（复选框不参与）
        for widget in [item_frame, name_label, enabled_label]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Button-3>", on_right_click)
        
        # 保存 frame 引用
        self.weapon_item_frames[weapon_name] = item_frame
        
        # 高亮当前选中的武器
        if self.core.current_weapon == weapon_name:
            item_frame.configure(fg_color=("gray70", "gray30"))
    
    def update_selected_count(self):
        """更新选中计数"""
        count = sum(1 for var in self.weapon_selected_vars.values() if var.get())
        total = len(self.weapon_selected_vars)
        self.selected_count_label.configure(text=f"已选: {count}/{total}")
        
        # 更新全选按钮文本
        if count == total and total > 0:
            self.select_all_btn.configure(text="取消")
            self.all_selected = True
        else:
            self.select_all_btn.configure(text="全选")
            self.all_selected = False
    
    def toggle_select_all(self):
        """全选/取消全选"""
        if self.all_selected:
            # 取消全选
            for var in self.weapon_selected_vars.values():
                var.set(False)
        else:
            # 全选
            for var in self.weapon_selected_vars.values():
                var.set(True)
        self.update_selected_count()
    
    def get_selected_weapons(self):
        """获取所有选中的武器名称列表"""
        return [name for name, var in self.weapon_selected_vars.items() if var.get()]
    
    def batch_delete_weapons(self):
        """批量删除选中的武器"""
        selected = self.get_selected_weapons()
        if not selected:
            messagebox.showwarning("提示", "请先勾选要删除的武器")
            return
        
        # 二次确认
        weapon_list_str = "\n".join(f"  • {name}" for name in selected)
        if not messagebox.askyesno(
            "确认批量删除",
            f"确定要删除以下 {len(selected)} 个武器吗？\n\n{weapon_list_str}\n\n此操作不可撤销！"
        ):
            return
        
        # 执行删除
        deleted_count = 0
        for weapon_name in selected:
            if self.core.delete_weapon(weapon_name):
                deleted_count += 1
                # 如果删除的是当前选中的武器，清空当前选择
                if self.core.current_weapon == weapon_name:
                    self.core.current_weapon = None
                    self.current_weapon_label.configure(text="当前武器: 无")
        
        # 刷新武器列表
        self.refresh_weapon_list()
        self.core.log(f"批量删除了 {deleted_count} 个武器")
        
        if deleted_count > 0:
            messagebox.showinfo("完成", f"成功删除 {deleted_count} 个武器")
    
    def batch_set_enabled(self, enabled):
        """批量启用/禁用选中的武器"""
        selected = self.get_selected_weapons()
        if not selected:
            messagebox.showwarning("提示", "请先勾选要操作的武器")
            return
        
        action = "启用" if enabled else "禁用"
        weapon_list_str = "\n".join(f"  • {name}" for name in selected)
        if not messagebox.askyesno(
            f"确认批量{action}",
            f"确定要{action}以下 {len(selected)} 个武器吗？\n\n{weapon_list_str}"
        ):
            return
        
        updated_count = 0
        for weapon_name in selected:
            weapon = self.core.get_weapon(weapon_name)
            if weapon:
                weapon["enabled"] = enabled
                if self.core.update_weapon(weapon_name, weapon):
                    updated_count += 1
        
        # 刷新武器列表
        self.refresh_weapon_list()
        self.core.log(f"批量{action}了 {updated_count} 个武器")
        
        if updated_count > 0:
            messagebox.showinfo("完成", f"成功{action} {updated_count} 个武器")
    
    def show_weapon_context_menu(self, event, weapon_name):
        """显示武器右键菜单"""
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # 选中/取消勾选
        if weapon_name in self.weapon_selected_vars:
            is_selected = self.weapon_selected_vars[weapon_name].get()
            toggle_text = "取消勾选" if is_selected else "勾选此项"
            context_menu.add_command(
                label=toggle_text,
                command=lambda: self._toggle_weapon_selection(weapon_name)
            )
        
        context_menu.add_separator()
        context_menu.add_command(
            label="删除武器",
            command=lambda: self.delete_weapon_by_name(weapon_name)
        )
        
        # 显示菜单
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _toggle_weapon_selection(self, weapon_name):
        """切换单个武器的勾选状态"""
        if weapon_name in self.weapon_selected_vars:
            var = self.weapon_selected_vars[weapon_name]
            var.set(not var.get())
            self.update_selected_count()
    
    def delete_weapon_by_name(self, weapon_name):
        """根据武器名称删除武器"""
        weapon = self.core.get_weapon(weapon_name)
        if not weapon:
            messagebox.showwarning("警告", "武器不存在")
            return
        
        if messagebox.askyesno("确认", f"确定要删除武器 '{weapon['name']}' 吗？"):
            if self.core.delete_weapon(weapon_name):
                # 如果删除的是当前选中的武器，清空当前选择
                if self.core.current_weapon == weapon_name:
                    self.core.current_weapon = None
                    self.current_weapon_label.configure(text="当前武器: 无")
                
                # 刷新武器列表
                self.refresh_weapon_list()
                self.core.log(f"已删除武器: {weapon['name']}")
    
    def select_weapon(self, weapon_name):
        """选择武器"""
        if self.core.set_current_weapon(weapon_name):
            weapon = self.core.get_weapon(weapon_name)
            
            # 更新状态栏
            self.current_weapon_label.configure(text=f"当前武器: {weapon['name']}")
            
            # 更新当前倍镜显示
            self.update_current_scope_display()
            
            # 更新参数显示
            self.update_weapon_params(weapon)
            
            # 轻量级高亮更新（只更新上次和当前选中的武器）
            self._update_highlight(weapon_name)
    
    def _update_highlight(self, new_selected_name):
        """轻量级高亮更新：只更新上次和当前选中的武器，不刷新整个列表"""
        # 清除上次选中的高亮
        if self.last_selected_weapon and self.last_selected_weapon in self.weapon_item_frames:
            self.weapon_item_frames[self.last_selected_weapon].configure(fg_color="transparent")
        
        # 设置新选中的高亮
        if new_selected_name and new_selected_name in self.weapon_item_frames:
            self.weapon_item_frames[new_selected_name].configure(fg_color=("gray70", "gray30"))
        
        # 更新上次选中记录
        self.last_selected_weapon = new_selected_name
    
    def update_weapon_params(self, weapon):
        """更新武器参数显示"""
        # 更新名称
        self.weapon_name_entry.delete(0, "end")
        self.weapon_name_entry.insert(0, weapon["name"])
        
        # 更新描述
        self.weapon_desc_entry.delete(0, "end")
        self.weapon_desc_entry.insert(0, weapon.get("description", ""))
        
        # 更新压枪模式 - 完整显示X、Y、d数据
        # 优先使用lua_pattern，没有则使用pattern
        lua_pattern = weapon.get("lua_pattern", [])
        pattern = weapon.get("pattern", [])
        
        if lua_pattern and len(lua_pattern) > 0 and isinstance(lua_pattern[0], dict):
            # 完整格式：显示x,y,d每个点的数据
            lines = []
            for i, p in enumerate(lua_pattern):
                x = p.get("x", 0)
                y = p.get("y", 0)
                d = p.get("d", 10)
                lines.append(f"{x},{y},{d}")
            pattern_str = "\n".join(lines)
        elif pattern and len(pattern) > 0 and isinstance(pattern[0], dict):
            # 字典格式但没有lua_pattern
            lines = []
            for i, p in enumerate(pattern):
                x = p.get("x", 0)
                y = p.get("y", 0)
                d = p.get("d", 10)
                lines.append(f"{x},{y},{d}")
            pattern_str = "\n".join(lines)
        elif pattern:
            # 普通格式：数字列表（只有Y值）
            pattern_str = ", ".join(str(x) for x in pattern)
        else:
            pattern_str = ""
        self.pattern_text.delete("1.0", "end")
        self.pattern_text.insert("1.0", pattern_str)
        
        # 更新射速
        self.fire_rate_entry.delete(0, "end")
        self.fire_rate_entry.insert(0, str(weapon.get("fire_rate", 10)))
        
        # 更新启用状态
        self.enabled_var.set(weapon.get("enabled", True))
        
        # 更新力度控制（如果有保存的力度值）
        strength = weapon.get("strength", 1.0)
        self.strength_entry.delete(0, "end")
        self.strength_entry.insert(0, f"{strength:.2f}")
        
        # 更新倍率数组
        multipliers = weapon.get("multipliers", [1.0])
        multipliers_str = ", ".join([str(m) for m in multipliers])
        self.multipliers_entry.delete(0, "end")
        self.multipliers_entry.insert(0, multipliers_str)
        
        # 更新倍镜切换选项
        current_index = weapon.get("current_multiplier_index", 0)
        if current_index >= len(multipliers):
            current_index = 0
        
        # 更新倍镜菜单选项
        scope_options = [f"{m}x" for m in multipliers]
        self.scope_menu.configure(values=scope_options)
        
        # 设置当前倍镜
        if scope_options:
            self.scope_var.set(scope_options[current_index])
        
        # 更新轨迹可视化
        self.update_pattern_visualization()
        
        # 更新武器图片显示
        if "image_path" in weapon and weapon["image_path"]:
            image_path = os.path.join(self.weapon_images_dir, weapon["image_path"])
            if os.path.exists(image_path):
                self.display_weapon_image(image_path)
            else:
                self.weapon_image_label.configure(text="图片不存在", image=None)
        else:
            self.weapon_image_label.configure(text="暂无图片", image=None)
    
    def add_weapon(self):
        """新增武器"""
        # 创建新武器对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("新增武器")
        dialog.geometry("500x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 武器名称
        ctk.CTkLabel(dialog, text="武器名称:").pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=400)
        name_entry.pack(pady=5)
        
        # 武器描述
        ctk.CTkLabel(dialog, text="武器描述:").pack(pady=5)
        desc_entry = ctk.CTkEntry(dialog, width=400)
        desc_entry.pack(pady=5)
        
        # 方式1：压枪模式 (逗号分隔Y值)
        ctk.CTkLabel(dialog, text="方式1：压枪模式 (逗号分隔Y值):").pack(pady=(5, 0))
        pattern_entry = ctk.CTkEntry(dialog, width=400)
        pattern_entry.insert(0, "2, 3, 4, 5, 6, 7, 8, 9, 10")
        pattern_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="--- 或 ---", text_color="gray", font=("Arial", 10)).pack(pady=2)
        
        # 方式2：导入LUA格式数据
        ctk.CTkLabel(dialog, text="方式2：导入LUA格式数据 (支持完整x,y,d):").pack(pady=(5, 0))
        lua_data_text = ctk.CTkTextbox(dialog, width=400, height=150)
        lua_data_text.pack(pady=5)
        
        # 填充示例按钮
        def fill_example():
            example_data = """{
    name = "新武器",
    pattern = {{x=-116.02,y=205.85,d=100.0}, {x=-22.46,y=149.71,d=100.0}, {x=-67.37,y=78.6,d=100.0}},
    key = KEY_新武器,
    key_ctrl = 0
}"""
            lua_data_text.delete("1.0", "end")
            lua_data_text.insert("1.0", example_data)
        
        fill_example_btn = ctk.CTkButton(
            dialog, 
            text="填充示例", 
            command=fill_example,
            width=100,
            fg_color="gray"
        )
        fill_example_btn.pack(pady=(0, 10))
        
        def save():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            lua_data_str = lua_data_text.get("1.0", "end-1c").strip()
            
            if not name and not lua_data_str:
                messagebox.showerror("错误", "请输入武器名称或导入LUA格式数据")
                return
            
            # 优先使用LUA格式数据
            weapon_data = None
            if lua_data_str:
                weapon_data = self._parse_lua_weapon_data(lua_data_str)
                if not weapon_data:
                    return
                
                # 如果文本框里也填了名称，用文本框的
                if name:
                    weapon_data["name"] = name
                elif "name" not in weapon_data or not weapon_data["name"]:
                    messagebox.showerror("错误", "LUA数据中缺少武器名称")
                    return
            else:
                # 方式1：使用简单Y值模式
                try:
                    y_values = [float(x.strip()) for x in pattern_entry.get().split(",") if x.strip()]
                except ValueError:
                    messagebox.showerror("错误", "压枪模式格式错误")
                    return
                
                # 转换为完整的X,Y,D格式
                full_pattern = [{"x": 0.0, "y": y, "d": 10.0} for y in y_values]
                
                # 创建新武器 - pattern和lua_pattern都保存完整数据
                weapon_data = {
                    "name": name,
                    "pattern": full_pattern,
                    "lua_pattern": full_pattern,
                    "fire_rate": 10.0,
                    "enabled": True,
                    "description": desc
                }
            
            # 如果描述框里填了，优先用它
            if desc:
                weapon_data["description"] = desc
            
            # 确保一些默认字段
            if "fire_rate" not in weapon_data:
                weapon_data["fire_rate"] = 10.0
            if "enabled" not in weapon_data:
                weapon_data["enabled"] = True
            
            if self.core.add_weapon(weapon_data):
                self.refresh_weapon_list()
                dialog.destroy()
                self.core.log(f"新增武器: {weapon_data['name']}")
            else:
                messagebox.showerror("错误", "添加武器失败")
        
        # 保存按钮
        ctk.CTkButton(dialog, text="保存", command=save, width=150).pack(pady=15)
    
    def _parse_lua_weapon_data(self, lua_str):
        """解析LUA格式的武器数据"""
        try:
            # 先简化一下格式，方便解析
            s = lua_str.strip()
            
            # 如果以{开头，先去掉外层
            if s.startswith("{"):
                s = s[1:]
            if s.endswith("}"):
                s = s[:-1]
            
            result = {}
            lua_pattern = []
            
            # 按行或分号分割处理
            lines = [line.strip() for line in s.replace(";", "\n").split("\n") if line.strip()]
            
            for line in lines:
                line = line.strip()
                if not line or line == "{":
                    continue
                
                # 处理 key = value
                if "=" in line:
                    parts = line.split("=", 1)
                    key = parts[0].strip()
                    value = parts[1].strip().rstrip(",")
                    
                    if key == "name":
                        # 处理字符串：name = "新武器"
                        name_val = value.strip('"\'')
                        result["name"] = name_val
                    
                    elif key == "pattern":
                        # 处理pattern数组：pattern = {{x=-116,y=205,d=100}, {x=-22,y=149,d=100}}
                        # 提取数组内容
                        pat_str = value
                        if pat_str.startswith("{"):
                            pat_str = pat_str[1:]
                        if pat_str.endswith("}"):
                            pat_str = pat_str[:-1]
                        
                        # 遍历每个点
                        in_point = False
                        point_str = ""
                        bracket_level = 0
                        
                        for char in pat_str:
                            if char == "{":
                                bracket_level += 1
                                in_point = True
                                point_str = ""
                            elif char == "}":
                                bracket_level -= 1
                                if bracket_level == 0 and in_point and point_str:
                                    # 解析点
                                    point = self._parse_lua_point(point_str.strip())
                                    if point:
                                        lua_pattern.append(point)
                                    in_point = False
                                    point_str = ""
                            elif in_point:
                                point_str += char
                        
                        if lua_pattern:
                            result["lua_pattern"] = lua_pattern
                            # pattern字段也完整保存X,Y,D（不再只存Y值）
                            result["pattern"] = lua_pattern
                            # 取第一个点的d作为默认fire_rate
                            if lua_pattern and "d" in lua_pattern[0]:
                                result["fire_rate"] = lua_pattern[0]["d"]
            
            # 如果解析成功
            if result:
                return result
            else:
                messagebox.showerror("解析错误", "无法解析LUA格式数据，请检查格式")
                return None
                
        except Exception as e:
            messagebox.showerror("解析错误", f"解析LUA数据失败: {str(e)}")
            return None
    
    def _parse_lua_point(self, point_str):
        """解析LUA中的点：x=-116.02,y=205.85,d=100.0 - 保留小数位"""
        try:
            x = 0.0
            y = 0.0
            d = 10.0
            
            parts = [p.strip() for p in point_str.split(",") if p.strip()]
            
            for part in parts:
                if "=" in part:
                    kv = part.split("=", 1)
                    k = kv[0].strip()
                    v = kv[1].strip()
                    try:
                        num = float(v)
                        if k == "x":
                            x = num
                        elif k == "y":
                            y = num
                        elif k == "d":
                            d = num
                    except ValueError:
                        pass
            
            return {"x": x, "y": y, "d": d}
            
        except Exception:
            return None
    
    def import_lua(self):
        """导入LUA压枪脚本"""
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择LUA压枪脚本",
            filetypes=[("LUA文件", "*.lua"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 导入解析器
            from lua_parser import LuaRecoilParser
            
            # 解析LUA文件
            parser = LuaRecoilParser()
            result = parser.parse_file(file_path)
            
            if not result:
                messagebox.showerror("错误", "解析LUA文件失败")
                return
            
            weapons = result.get('weapons', [])
            if not weapons:
                messagebox.showwarning("警告", "LUA文件中没有找到武器数据")
                return
            
            # 转换为正确的格式（pattern为Y值列表）
            weapons_json = parser.convert_to_json_format()
            
            # 显示导入结果
            imported_count = 0
            for weapon_name, weapon_data in weapons_json.items():
                if self.core.add_weapon(weapon_data):
                    imported_count += 1
            
            # 刷新武器列表
            self.refresh_weapon_list()
            
            # 显示成功消息
            messagebox.showinfo(
                "导入成功",
                f"成功导入 {imported_count} 个武器\n"
                f"倍率: {result.get('multipliers', [])}\n"
                f"基础灵敏度: X={result.get('base_sensitivity_x', 1)}, Y={result.get('base_sensitivity_y', 1)}"
            )
            
            # 记录日志
            self.core.log(f"从LUA文件导入 {imported_count} 个武器: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入LUA文件失败: {str(e)}")
    
    def open_pattern_recorder(self):
        """打开轨迹录制器"""
        try:
            from pattern_recorder import PatternRecorder
            
            def on_weapon_generated(weapon_data):
                """武器数据生成回调"""
                if self.core.add_weapon(weapon_data):
                    self.refresh_weapon_list()
                    self.core.log(f"通过轨迹录制添加武器: {weapon_data['name']}")
                    messagebox.showinfo("成功", f"已添加武器: {weapon_data['name']}")
                else:
                    messagebox.showerror("错误", "添加武器失败")
            
            # 创建并显示录制器
            recorder = PatternRecorder(self.root, callback=on_weapon_generated)
            recorder.show()
            
        except Exception as e:
            messagebox.showerror("错误", f"打开轨迹录制器失败: {str(e)}")
    
    def delete_weapon(self):
        """删除武器"""
        if not self.core.current_weapon:
            messagebox.showwarning("警告", "请先选择要删除的武器")
            return
        
        weapon = self.core.get_weapon(self.core.current_weapon)
        weapon_name = weapon["name"]
        
        if messagebox.askyesno("确认", f"确定要删除武器 '{weapon_name}' 吗？"):
            if self.core.delete_weapon(self.core.current_weapon):
                self.core.current_weapon = None
                self.current_weapon_label.configure(text="当前武器: 无")
                self.refresh_weapon_list()
    
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
        
        # 数据同步选项卡
        self.network_tab = self.tabview.add("数据同步")
        self.create_data_sync_tab()
    
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
        
        # 力度控制
        strength_frame = ctk.CTkFrame(self.weapon_tab)
        strength_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(strength_frame, text="力度控制:", width=100).pack(side="left", padx=5)
        self.strength_entry = ctk.CTkEntry(strength_frame, width=120)
        self.strength_entry.insert(0, "1.00")
        self.strength_entry.pack(side="left", padx=5)
        ctk.CTkLabel(strength_frame, text="x（范围 0.01~3.00）").pack(side="left", padx=5)
        
        # 倍率数组设置
        multipliers_frame = ctk.CTkFrame(self.weapon_tab)
        multipliers_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(multipliers_frame, text="倍率数组:", width=100).pack(side="left", padx=5)
        self.multipliers_entry = ctk.CTkEntry(multipliers_frame, width=200)
        self.multipliers_entry.pack(side="left", padx=5)
        
        # 实时更新倍镜菜单选项
        def update_scope_options(*args):
            try:
                multipliers_str = self.multipliers_entry.get().strip()
                if not multipliers_str:
                    multipliers = [1.0]
                else:
                    multipliers = [float(m.strip()) for m in multipliers_str.split(",") if m.strip()]
                    if not multipliers:
                        multipliers = [1.0]
                
                # 更新倍镜菜单选项
                scope_options = [f"{m}x" for m in multipliers]
                self.scope_menu.configure(values=scope_options)
                
                # 如果当前选项不在新选项中，设置为第一个
                current_scope = self.scope_var.get()
                if current_scope not in scope_options and scope_options:
                    self.scope_var.set(scope_options[0])
            except ValueError:
                # 如果解析失败，不做任何事情
                pass
        
        self.multipliers_entry.bind("<KeyRelease>", update_scope_options)
        
        # 倍镜切换
        scope_frame = ctk.CTkFrame(self.weapon_tab)
        scope_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(scope_frame, text="倍镜切换:", width=100).pack(side="left", padx=5)
        self.scope_var = ctk.StringVar(value="1.0x")
        self.scope_menu = ctk.CTkOptionMenu(
            scope_frame,
            variable=self.scope_var,
            values=[],
            width=200
        )
        self.scope_menu.pack(side="left", padx=5)
        
        # 压枪轨迹可视化
        pattern_viz_frame = ctk.CTkFrame(self.weapon_tab)
        pattern_viz_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(pattern_viz_frame, text="压枪轨迹预览:").pack(anchor="w", padx=5, pady=2)
        
        # 创建Canvas用于绘制轨迹
        self.pattern_canvas = tk.Canvas(
            pattern_viz_frame,
            bg="#2b2b2b",
            highlightthickness=0,
            height=200
        )
        self.pattern_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 绑定Canvas大小变化事件
        self.pattern_canvas.bind("<Configure>", self.on_canvas_resize)
        
        # 保存按钮
        save_button = ctk.CTkButton(
            self.weapon_tab,
            text="保存武器参数",
            command=self.save_weapon_params,
            width=200
        )
        save_button.pack(pady=20)
        
        # 武器数据版本号（选项卡最底部）
        data_ver = get_local_data_version()
        self.weapon_data_version_label = ctk.CTkLabel(
            self.weapon_tab,
            text=f"武器数据版本: v{data_ver}",
            font=("Arial", 10),
            text_color="gray"
        )
        self.weapon_data_version_label.pack(pady=(0, 5))
    
    def save_weapon_params(self):
        """保存武器参数 - 完整保留压枪数组数据"""
        if not self.core.current_weapon:
            messagebox.showwarning("警告", "请先选择武器")
            return
        
        try:
            # 获取当前武器配置（保留原有数据）
            current_weapon = self.core.get_weapon(self.core.current_weapon)
            
            # 获取参数
            name = self.weapon_name_entry.get().strip()
            desc = self.weapon_desc_entry.get().strip()
            pattern_str = self.pattern_text.get("1.0", "end-1c").strip()
            fire_rate = float(self.fire_rate_entry.get().strip())
            enabled = self.enabled_var.get()
            
            # 获取力度和倍镜值
            strength = round(float(self.strength_entry.get().strip()), 2)
            strength = max(0.01, min(3.0, strength))  # 限制范围
            scope = self.scope_var.get()
            
            # 解析倍率数组
            try:
                multipliers_str = self.multipliers_entry.get().strip()
                multipliers = [float(m.strip()) for m in multipliers_str.split(",") if m.strip()]
                if not multipliers:
                    multipliers = [1.0]
            except ValueError:
                messagebox.showerror("错误", "倍率数组格式错误，请输入数字，用逗号分隔")
                return
            
            # 计算当前倍率索引
            scope_multiplier = float(scope.replace("x", ""))
            current_multiplier_index = 0
            for i, m in enumerate(multipliers):
                if abs(m - scope_multiplier) < 0.01:
                    current_multiplier_index = i
                    break
            
            # 构建基础武器数据（不包含pattern/lua_pattern，需要单独处理）
            weapon_data = {
                "name": name,
                "fire_rate": fire_rate,
                "enabled": enabled,
                "description": desc,
                "strength": strength,
                "scope": scope,
                "multipliers": multipliers,
                "current_multiplier_index": current_multiplier_index
            }
            
            # ---------------- 压枪数组处理逻辑 ----------------
            # 优先保留lua_pattern，其次保留pattern，最后才从文本框解析
            lua_pattern_changed = False
            new_lua_pattern = None
            
            # 1. 检查文本框内容是否为空或与原有数据一致
            if pattern_str:
                # 尝试解析文本框内容
                parsed_pattern = self._parse_pattern_text(pattern_str, current_weapon)
                if parsed_pattern:
                    new_lua_pattern = parsed_pattern
                    lua_pattern_changed = True
            elif not pattern_str and current_weapon:
                # 文本框清空了，但可能是意外，保留原有数据
                pass
            
            # 2. 优先保留原有压枪数据，只有用户主动修改了才更新
            if current_weapon:
                # 保留lua_pattern（优先级最高）
                if "lua_pattern" in current_weapon and current_weapon["lua_pattern"] and not lua_pattern_changed:
                    weapon_data["lua_pattern"] = current_weapon["lua_pattern"]
                elif new_lua_pattern:
                    weapon_data["lua_pattern"] = new_lua_pattern
                elif "lua_pattern" in current_weapon:
                    weapon_data["lua_pattern"] = current_weapon["lua_pattern"]
                
                # pattern字段也完整保存X,Y,D数据（不再只存Y值）
                if "pattern" in current_weapon and current_weapon["pattern"] and not lua_pattern_changed:
                    weapon_data["pattern"] = current_weapon["pattern"]
                elif new_lua_pattern:
                    # 如果用户主动修改了，pattern字段也保存完整的X,Y,D数据
                    weapon_data["pattern"] = new_lua_pattern
                elif "pattern" in current_weapon:
                    weapon_data["pattern"] = current_weapon["pattern"]
            
            # 保留其他原有字段
            if current_weapon:
                for key in ["lua_key", "lua_key_ctrl", "base_yqxs_x", "base_yqxs_y", "mode", "image_path"]:
                    if key in current_weapon and key not in weapon_data:
                        weapon_data[key] = current_weapon[key]
            
            if self.core.update_weapon(self.core.current_weapon, weapon_data):
                self.refresh_weapon_list()
                messagebox.showinfo("成功", "武器参数已保存")
            else:
                messagebox.showerror("错误", "保存失败")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _parse_pattern_text(self, pattern_str, current_weapon=None):
        """解析压枪模式文本，支持多种格式：
        1. 每行一个点：x,y,d
        2. 逗号分隔的Y值列表
        保留小数位
        """
        lines = [line.strip() for line in pattern_str.split("\n") if line.strip()]
        
        if not lines:
            return None
        
        # 检查是否是完整格式（每行x,y,d）
        if "," in lines[0] and lines[0].count(",") >= 1:
            try:
                parsed = []
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        x = float(parts[0]) if parts[0] else 0.0
                        y = float(parts[1]) if parts[1] else 0.0
                        d = float(parts[2]) if len(parts) > 2 and parts[2] else (current_weapon.get("fire_rate", 10.0) if current_weapon else 10.0)
                        parsed.append({"x": x, "y": y, "d": d})
                if parsed:
                    return parsed
            except ValueError:
                pass
        
        # 尝试简单逗号分隔格式（仅Y值）
        try:
            all_values = []
            for line in lines:
                all_values.extend([x.strip() for x in line.split(",") if x.strip()])
            y_values = [float(x) for x in all_values]
            if y_values:
                fire_rate = current_weapon.get("fire_rate", 10.0) if current_weapon else 10.0
                return [{"x": 0.0, "y": y, "d": fire_rate} for y in y_values]
        except ValueError:
            pass
        
        return None
    
    def on_canvas_resize(self, event):
        """Canvas大小变化时更新轨迹可视化"""
        self.update_pattern_visualization()
    
    def update_pattern_visualization(self):
        """更新压枪轨迹可视化 - X-Y坐标图（参考recoil_v4.0绘制方式）"""
        if not hasattr(self, 'pattern_canvas'):
            return
        
        # 清空Canvas
        self.pattern_canvas.delete("all")
        
        # 获取当前武器的压枪模式
        if not self.core.current_weapon:
            return
        
        weapon = self.core.get_weapon(self.core.current_weapon)
        if not weapon:
            return
        
        # 获取lua_pattern（完整的x, y, d数据）
        lua_pattern = weapon.get("lua_pattern", [])
        
        # 如果没有lua_pattern，尝试从pattern构建
        if not lua_pattern:
            pattern = weapon.get("pattern", [])
            if pattern and len(pattern) > 0:
                if isinstance(pattern[0], (int, float)):
                    # 普通格式：数字列表
                    lua_pattern = [{"x": 0, "y": y, "d": 10} for y in pattern]
                elif isinstance(pattern[0], dict):
                    # LUA格式：字典列表，直接使用
                    lua_pattern = pattern
            else:
                return
        
        if not lua_pattern:
            return
        
        # 获取Canvas尺寸
        canvas_width = self.pattern_canvas.winfo_width()
        canvas_height = self.pattern_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # 将相对位移转换为绝对坐标（参考recoil_v4.0的方式）
        # 起始点在画布中心
        absolute_points = []
        x, y = 0, 0
        for point in lua_pattern:
            dx = point.get("x", 0)
            dy = point.get("y", 0)
            x += dx
            y += dy
            absolute_points.append((x, y))
        
        # 计算绝对坐标的边界
        x_values = [p[0] for p in absolute_points]
        y_values = [p[1] for p in absolute_points]
        
        max_x = max(x_values) if x_values else 10
        min_x = min(x_values) if x_values else -10
        max_y = max(y_values) if y_values else 10
        min_y = min(y_values) if y_values else 0
        
        # 确保范围不为0，且包含原点
        max_x = max(max_x, 5)
        min_x = min(min_x, -5)
        max_y = max(max_y, 5)
        min_y = min(min_y, -5)
        
        # 添加边距
        margin = 40
        plot_width = canvas_width - 2 * margin
        plot_height = canvas_height - 2 * margin
        
        # 计算缩放比例（保持纵横比）
        x_range = max_x - min_x
        y_range = max_y - min_y
        
        scale_x = plot_width / x_range if x_range > 0 else 1
        scale_y = plot_height / y_range if y_range > 0 else 1
        scale = min(scale_x, scale_y) * 0.85  # 留出15%边距
        
        # 计算原点在Canvas上的位置（画布中心）
        origin_canvas_x = canvas_width / 2
        origin_canvas_y = canvas_height / 2
        
        # 绘制网格线
        grid_color = "#333333"
        grid_spacing = 50  # 像素
        
        # 垂直网格线
        x = origin_canvas_x % grid_spacing
        while x < canvas_width:
            self.pattern_canvas.create_line(x, margin, x, canvas_height - margin, fill=grid_color, dash=(2, 2))
            x += grid_spacing
            
        # 水平网格线
        y = origin_canvas_y % grid_spacing
        while y < canvas_height:
            self.pattern_canvas.create_line(margin, y, canvas_width - margin, y, fill=grid_color, dash=(2, 2))
            y += grid_spacing
        
        # 绘制坐标轴
        axis_color = "#666666"
        # X轴
        self.pattern_canvas.create_line(margin, origin_canvas_y, canvas_width - margin, origin_canvas_y, 
                                       fill=axis_color, width=2)
        # Y轴
        self.pattern_canvas.create_line(origin_canvas_x, margin, origin_canvas_x, canvas_height - margin, 
                                       fill=axis_color, width=2)
        
        # 绘制坐标轴标签
        label_color = "#999999"
        self.pattern_canvas.create_text(canvas_width - margin + 5, origin_canvas_y, text="X", fill=label_color, anchor="w")
        self.pattern_canvas.create_text(origin_canvas_x, margin - 5, text="Y", fill=label_color, anchor="s")
        
        # 绘制原点标记
        self.pattern_canvas.create_oval(origin_canvas_x-5, origin_canvas_y-5, 
                                       origin_canvas_x+5, origin_canvas_y+5, 
                                       fill="white", outline="gray")
        
        # 转换绝对坐标为Canvas坐标
        canvas_points = []
        for abs_x, abs_y in absolute_points:
            canvas_x = origin_canvas_x + abs_x * scale
            canvas_y = origin_canvas_y + abs_y * scale  # Y轴向下为正（与屏幕坐标一致）
            canvas_points.append((canvas_x, canvas_y))
        
        # 绘制后坐力骨架连线（黄色虚线）- 参考recoil_v4.0
        if len(canvas_points) > 1:
            for i in range(len(canvas_points) - 1):
                x1, y1 = canvas_points[i]
                x2, y2 = canvas_points[i + 1]
                self.pattern_canvas.create_line(x1, y1, x2, y2, 
                                               fill="#ffff00", width=2, dash=(4, 2),
                                               tags="skeleton")
        
        # 绘制压枪方向箭头（青色）- 参考recoil_v4.0
        if len(canvas_points) > 1:
            for i in range(len(canvas_points) - 1):
                x1, y1 = canvas_points[i]
                x2, y2 = canvas_points[i + 1]
                
                # 压枪方向 = 后坐力的反方向
                dx = x1 - x2
                dy = y1 - y2
                
                # 只在位移足够大时显示箭头
                if abs(dx) > 3 or abs(dy) > 3:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    arrow_len = 0.4  # 箭头长度比例
                    self.pattern_canvas.create_line(mid_x, mid_y, 
                                                   mid_x + dx * arrow_len, mid_y + dy * arrow_len,
                                                   fill="#00ffff", width=2, arrow=tk.LAST,
                                                   tags="recoil")
        
        # 绘制轨迹点（参考recoil_v4.0的点形标记）
        for i, (canvas_x, canvas_y) in enumerate(canvas_points):
            # 颜色渐变（从蓝到红）
            ratio = i / max(len(canvas_points) - 1, 1)
            r = int(255 * ratio)
            g = int(100 * (1 - abs(ratio - 0.5) * 2))
            b = int(255 * (1 - ratio))
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # 第一个点特殊标记
            if i == 0:
                color = "#00ff00"  # 起点绿色
                size = 6
            elif i == len(canvas_points) - 1:
                color = "#ff0000"  # 终点红色
                size = 6
            else:
                size = 4
            
            # 绘制实心圆点
            self.pattern_canvas.create_oval(canvas_x - size, canvas_y - size,
                                           canvas_x + size, canvas_y + size,
                                           fill=color, outline="#ffffff", width=1)
            
            # 数字标签（右偏移显示，参考recoil_v4.0）
            if i < 20 or i == len(canvas_points) - 1:  # 只显示前20个和最后一个
                self.pattern_canvas.create_text(canvas_x + 10, canvas_y,
                                               text=str(i + 1), fill=color,
                                               font=("Arial", 8), anchor="w")
        
        # 添加信息标签
        info_text = f"点数: {len(lua_pattern)} | 终点: ({absolute_points[-1][0]:.1f}, {absolute_points[-1][1]:.1f})"
        self.pattern_canvas.create_text(
            margin, 10,
            text=info_text,
            fill="white",
            anchor="nw"
        )
    
    def create_global_settings_tab(self):
        """创建全局设置选项卡"""
        # 全局压枪力度设置
        global_strength_frame = ctk.CTkFrame(self.global_tab)
        global_strength_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(global_strength_frame, text="全局力度:", width=100).pack(side="left", padx=5)
        self.global_strength_entry = ctk.CTkEntry(global_strength_frame, width=120)
        global_strength_val = self.core.settings.get("global_strength", 1.0)
        self.global_strength_entry.insert(0, f"{global_strength_val:.2f}")
        self.global_strength_entry.pack(side="left", padx=5)
        ctk.CTkLabel(global_strength_frame, text="（范围 0.01~3.00，默认1.00）").pack(side="left", padx=5)
        
        # 热键设置
        hotkey_frame = ctk.CTkFrame(self.global_tab)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(hotkey_frame, text="开关热键:", width=100).pack(side="left", padx=5)
        self.hotkey_entry = ctk.CTkEntry(hotkey_frame, width=200)
        self.hotkey_entry.insert(0, self.core.settings.get("hotkey", "F1"))
        self.hotkey_entry.pack(side="left", padx=5)
        
        # 开火键设置
        fire_button_frame = ctk.CTkFrame(self.global_tab)
        fire_button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(fire_button_frame, text="开火键:", width=100).pack(side="left", padx=5)
        self.fire_button_entry = ctk.CTkEntry(fire_button_frame, width=200)
        self.fire_button_entry.insert(0, self.core.settings.get("fire_button", "LButton"))
        self.fire_button_entry.pack(side="left", padx=5)
        
        # 移动间隔
        interval_frame = ctk.CTkFrame(self.global_tab)
        interval_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(interval_frame, text="移动间隔(ms):", width=100).pack(side="left", padx=5)
        self.interval_entry = ctk.CTkEntry(interval_frame, width=200)
        self.interval_entry.insert(0, str(self.core.settings.get("move_interval", 10)))
        self.interval_entry.pack(side="left", padx=5)
        
        # 触发方式设置
        trigger_frame = ctk.CTkFrame(self.global_tab)
        trigger_frame.pack(fill="x", padx=10, pady=5)
        
        self.trigger_var = ctk.BooleanVar(value=self.core.settings.get("left_right_trigger", True))
        self.trigger_checkbox = ctk.CTkCheckBox(
            trigger_frame,
            text="鼠标左键+右键触发",
            variable=self.trigger_var
        )
        self.trigger_checkbox.pack(side="left", padx=5)
        
        # 倍镜列表设置
        scope_frame = ctk.CTkFrame(self.global_tab)
        scope_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(scope_frame, text="倍镜列表:", width=100).pack(side="left", padx=5)
        
        # 获取当前倍镜列表
        scope_multipliers = self.core.scope_multipliers
        scope_str = ", ".join([str(m) for m in scope_multipliers])
        
        self.scope_list_entry = ctk.CTkEntry(scope_frame, width=200)
        self.scope_list_entry.insert(0, scope_str)
        self.scope_list_entry.pack(side="left", padx=5)
        
        # 倍镜切换快捷键设置
        scope_hotkey_frame = ctk.CTkFrame(self.global_tab)
        scope_hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(scope_hotkey_frame, text="侧键1 (上一个):", width=120).pack(side="left", padx=5)
        self.scope_prev_key_var = ctk.StringVar(value=self.core.settings.get("scope_prev_key", "侧键1"))
        scope_prev_options = ["侧键1", "侧键2", "无"]
        self.scope_prev_menu = ctk.CTkOptionMenu(
            scope_hotkey_frame,
            variable=self.scope_prev_key_var,
            values=scope_prev_options,
            width=120
        )
        self.scope_prev_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(scope_hotkey_frame, text="侧键2 (下一个):", width=120).pack(side="left", padx=5)
        self.scope_next_key_var = ctk.StringVar(value=self.core.settings.get("scope_next_key", "侧键2"))
        scope_next_options = ["侧键1", "侧键2", "无"]
        self.scope_next_menu = ctk.CTkOptionMenu(
            scope_hotkey_frame,
            variable=self.scope_next_key_var,
            values=scope_next_options,
            width=120
        )
        self.scope_next_menu.pack(side="left", padx=5)
        
        # 倍镜切换说明
        scope_info_frame = ctk.CTkFrame(self.global_tab)
        scope_info_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            scope_info_frame, 
            text="倍镜切换提示: 侧键1切换到上一个倍率, 侧键2切换到下一个倍率",
            font=("Arial", 10)
        ).pack(padx=5, pady=5)
        
        # 当前倍镜显示
        self.current_scope_label = ctk.CTkLabel(
            scope_info_frame,
            text="当前倍镜: --",
            font=("Arial", 12, "bold")
        )
        self.current_scope_label.pack(padx=5, pady=5)
        
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
            self.core.settings["hotkey"] = self.hotkey_entry.get().strip()
            self.core.settings["fire_button"] = self.fire_button_entry.get().strip()
            self.core.settings["move_interval"] = int(self.interval_entry.get().strip())
            self.core.settings["left_right_trigger"] = self.trigger_var.get()
            
            # 保存全局压枪力度
            global_strength = round(float(self.global_strength_entry.get().strip()), 2)
            global_strength = max(0.01, min(3.0, global_strength))  # 限制范围
            self.core.settings["global_strength"] = global_strength
            
            # 保存倍镜列表
            scope_str = self.scope_list_entry.get().strip()
            scope_multipliers = [float(m.strip()) for m in scope_str.split(",") if m.strip()]
            self.core.set_scope_multipliers(scope_multipliers)
            self.core.settings["scope_multipliers"] = scope_multipliers
            
            # 保存倍镜切换快捷键
            scope_prev_key = self.scope_prev_key_var.get()
            scope_next_key = self.scope_next_key_var.get()
            self.core.settings["scope_prev_key"] = scope_prev_key
            self.core.settings["scope_next_key"] = scope_next_key
            self.core.set_scope_hotkeys(scope_prev_key, scope_next_key)
            
            self.core.save_settings()
            
            # 更新当前倍镜显示
            self.current_scope_label.configure(text=f"当前倍镜: {self.core.current_scope_multiplier}x")
            
            messagebox.showinfo("成功", "全局设置已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def create_data_sync_tab(self):
        """创建数据同步选项卡"""
        # 当前数据版本显示
        version_frame = ctk.CTkFrame(self.network_tab)
        version_frame.pack(fill="x", padx=10, pady=10)
        
        current_ver = get_local_data_version()
        ctk.CTkLabel(version_frame, text="当前武器数据版本:", width=140).pack(side="left", padx=5)
        self.data_version_label = ctk.CTkLabel(
            version_frame, 
            text=f"v{current_ver}",
            font=("Arial", 14, "bold"),
            text_color="#00b894"
        )
        self.data_version_label.pack(side="left", padx=5)
        
        # 同步武器配置按钮
        sync_button = ctk.CTkButton(
            self.network_tab,
            text="同步武器配置",
            command=self.sync_weapon_config,
            width=200,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#0984e3",
            hover_color="#0770c2"
        )
        sync_button.pack(pady=20)
        
        # 同步状态显示
        self.network_status = ctk.CTkLabel(
            self.network_tab,
            text="",
            font=("Arial", 11),
            text_color="gray"
        )
        self.network_status.pack(pady=5)
        
        # 同步说明
        info_frame = ctk.CTkFrame(self.network_tab)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, 
            text="点击「同步武器配置」从云端获取最新的武器压枪数据。\n"
                 "同步会覆盖本地同名配置文件，请确保重要修改已备份。",
            font=("Arial", 10),
            text_color="gray",
            justify="left"
        ).pack(padx=10, pady=10, anchor="w")
    
    def sync_weapon_config(self):
        """同步武器配置数据"""
        self.network_status.configure(text="正在检查更新...", text_color="gray")
        self.core.log("正在检查武器数据更新...")

        def _sync():
            try:
                # 先检查是否有更新
                result = check_for_config_update()
                
                if result.get("error"):
                    self.root.after(0, lambda: self.network_status.configure(
                        text=f"检查失败: {result['error']}", text_color="#e74c3c"))
                    self.root.after(0, lambda: self.core.log(f"数据同步检查失败: {result['error']}"))
                    return

                if not result["has_update"]:
                    local_ver = result.get("local_version", "?")
                    self.root.after(0, lambda: self.network_status.configure(
                        text=f"已是最新版本 v{local_ver}", text_color="#00b894"))
                    self.root.after(0, lambda: self.core.log("武器数据已是最新版本"))
                    return

                # 有更新，执行同步
                release = result["release"]
                latest_ver = result.get("latest_version", "?")
                self.root.after(0, lambda: self.network_status.configure(
                    text=f"发现新版本 v{latest_ver}，正在同步...", text_color="#0984e3"))
                
                syncer = ConfigSyncer()
                
                def on_progress(msg):
                    self.root.after(0, lambda m=msg: self.network_status.configure(text=m))
                
                success, msg = syncer.sync_config(release, on_progress=on_progress)
                
                if success:
                    # 更新版本显示
                    new_ver = get_local_data_version()
                    self.root.after(0, lambda: self.data_version_label.configure(text=f"v{new_ver}"))
                    self.root.after(0, lambda: self.weapon_data_version_label.configure(text=f"武器数据版本: v{new_ver}"))
                    self.root.after(0, lambda: self.network_status.configure(text=msg, text_color="#00b894"))
                    self.root.after(0, lambda: self.core.log(msg))
                    # 刷新武器列表
                    self.root.after(0, self.refresh_weapon_list)
                    self.root.after(0, lambda: messagebox.showinfo("同步完成", msg))
                else:
                    self.root.after(0, lambda: self.network_status.configure(text=msg, text_color="#e74c3c"))
                    self.root.after(0, lambda: self.core.log(f"数据同步失败: {msg}"))
                    self.root.after(0, lambda: messagebox.showerror("同步失败", msg))

            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: self.network_status.configure(
                    text=f"同步失败: {err_msg}", text_color="#e74c3c"))
                self.root.after(0, lambda: self.core.log(f"数据同步异常: {err_msg}"))

        threading.Thread(target=_sync, daemon=True).start()
    
    def create_log_panel(self):
        """创建日志面板"""
        self.log_frame = ctk.CTkFrame(self.main_frame, height=120)
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
        
        # 武器图片面板
        self.weapon_image_panel = ctk.CTkFrame(self.main_frame, height=300)
        self.weapon_image_panel.pack(fill="x", padx=10, pady=(10, 0))
        self.weapon_image_panel.pack_propagate(False)
        
        # 武器图片标题行
        weapon_image_header = ctk.CTkFrame(self.weapon_image_panel)
        weapon_image_header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            weapon_image_header,
            text="武器图片",
            font=("Arial", 12, "bold")
        ).pack(side="left")
        
        # 选择图片按钮
        select_image_btn = ctk.CTkButton(
            weapon_image_header,
            text="选择图片",
            command=self.select_weapon_image,
            width=90
        )
        select_image_btn.pack(side="right", padx=2)
        
        # 清除图片按钮
        clear_image_btn = ctk.CTkButton(
            weapon_image_header,
            text="清除图片",
            command=self.clear_weapon_image,
            width=90,
            fg_color="gray",
            hover_color="dimgray"
        )
        clear_image_btn.pack(side="right", padx=2)
        
        # 图片显示区域（支持2K分辨率显示，缩小显示但不改变像素）
        self.weapon_image_label = ctk.CTkLabel(
            self.weapon_image_panel,
            text="暂无图片",
            fg_color=("gray70", "gray30"),
            corner_radius=8
        )
        self.weapon_image_label.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def clear_log(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空日志吗？"):
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")
            self.core.log("日志已清空")
    
    def export_log(self):
        """导出日志"""
        try:
            export_file = os.path.join(self.config_dir, f"log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get("1.0", "end"))
            messagebox.showinfo("成功", f"日志已导出到: {export_file}")
            self.core.log(f"日志已导出到: {export_file}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def select_weapon_image(self):
        """选择武器图片"""
        if not self.core.current_weapon:
            messagebox.showwarning("警告", "请先选择武器")
            return
        
        file_path = filedialog.askopenfilename(
            title="选择武器图片",
            filetypes=[
                ("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 生成唯一文件名（基于武器名称和时间戳）
                weapon_name = self.core.current_weapon
                timestamp = int(time.time())
                ext = os.path.splitext(file_path)[1]
                new_filename = f"{weapon_name}_{timestamp}{ext}"
                new_path = os.path.join(self.weapon_images_dir, new_filename)
                
                # 复制图片到武器图片目录
                import shutil
                shutil.copy2(file_path, new_path)
                
                # 更新武器数据中的图片路径
                weapon = self.core.get_weapon(weapon_name)
                if weapon:
                    weapon["image_path"] = new_filename
                    self.core.update_weapon(weapon_name, weapon)
                
                # 显示图片
                self.display_weapon_image(new_path)
                self.core.log(f"已为武器 {weapon_name} 设置图片")
                
            except Exception as e:
                messagebox.showerror("错误", f"选择图片失败: {str(e)}")
    
    def clear_weapon_image(self):
        """清除武器图片"""
        if not self.core.current_weapon:
            messagebox.showwarning("警告", "请先选择武器")
            return
        
        weapon_name = self.core.current_weapon
        weapon = self.core.get_weapon(weapon_name)
        
        if weapon and "image_path" in weapon:
            try:
                # 删除图片文件
                image_path = os.path.join(self.weapon_images_dir, weapon["image_path"])
                if os.path.exists(image_path):
                    os.remove(image_path)
                
                # 清除武器数据中的图片路径
                del weapon["image_path"]
                self.core.update_weapon(weapon_name, weapon)
                
                # 清除显示
                self.weapon_image_label.configure(text="暂无图片", image=None)
                self.core.log(f"已清除武器 {weapon_name} 的图片")
                
            except Exception as e:
                messagebox.showerror("错误", f"清除图片失败: {str(e)}")
        else:
            messagebox.showinfo("提示", "该武器没有设置图片")
    
    def display_weapon_image(self, image_path):
        """显示武器图片 - 使用CTkImage支持HighDPI，支持2K分辨率缩小显示"""
        try:
            from PIL import Image
            from customtkinter import CTkImage
            
            # 打开原始图片（保持原始像素不变）
            img = Image.open(image_path)
            
            # 获取面板实际尺寸，用于计算显示大小
            panel_width = self.weapon_image_panel.winfo_width()
            panel_height = self.weapon_image_panel.winfo_height()
            
            # 如果面板尺寸还没初始化，使用默认值
            if panel_width <= 1:
                panel_width = 800
            if panel_height <= 1:
                panel_height = 260
            
            # 计算缩放尺寸（留边距），支持2K分辨率
            max_width = panel_width - 30
            max_height = panel_height - 30
            
            # 按比例缩放（保持纵横比）
            img_width, img_height = img.size
            scale_w = max_width / img_width
            scale_h = max_height / img_height
            scale = min(scale_w, scale_h, 1.0)  # 不放大，只缩小
            
            display_width = int(img_width * scale)
            display_height = int(img_height * scale)
            
            # 确保最小尺寸
            display_width = max(display_width, 50)
            display_height = max(display_height, 50)
            
            # 创建CTkImage（支持HighDPI缩放）
            ctk_image = CTkImage(
                light_image=img,
                dark_image=img,
                size=(display_width, display_height)
            )
            
            # 更新标签
            self.weapon_image_label.configure(image=ctk_image, text="")
            self.weapon_image_label.ctk_image = ctk_image  # 保持引用防止被垃圾回收
            
        except ImportError:
            self.weapon_image_label.configure(text="需安装Pillow\npip install Pillow", image=None)
        except Exception as e:
            self.weapon_image_label.configure(text=f"图片加载失败: {str(e)[:30]}", image=None)
    
    def toggle_recoil(self):
        """切换压枪状态"""
        if self.enable_switch.get():
            self.core.enable()
        else:
            self.core.disable()
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        finally:
            # 清理资源
            self.core.cleanup()
    

def _extract_bundled_config():
    """PyInstaller 打包模式：如果 exe 同目录没有 config，从打包目录复制出来
    
    PyInstaller --add-data 把 config 打包进 exe，运行时解压到 sys._MEIPASS 临时目录。
    但 config 需要持久化（用户修改后要保存），所以首次运行时复制到 exe 同目录。
    """
    meipass_dir = getattr(sys, '_MEIPASS', None)
    if not meipass_dir:
        return  # 非 PyInstaller 模式，跳过
    
    app_config_dir = os.path.join(_APP_DIR, "config")
    bundled_config_dir = os.path.join(meipass_dir, "config")
    
    if not os.path.exists(bundled_config_dir):
        return  # 打包时没有包含 config
    
    # 如果 exe 同目录已有 config，不覆盖（保留用户修改）
    if os.path.exists(app_config_dir):
        # 只补充缺失的文件（不覆盖已有文件）
        import shutil
        for item in os.listdir(bundled_config_dir):
            src = os.path.join(bundled_config_dir, item)
            dst = os.path.join(app_config_dir, item)
            if not os.path.exists(dst):
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
    else:
        # 首次运行：完整复制 config 目录
        import shutil
        shutil.copytree(bundled_config_dir, app_config_dir)

def main():
    """主函数"""
    # PyInstaller 首次运行：解压打包的配置文件
    _extract_bundled_config()
    
    # 清除旧 crash.log，开始新记录
    try:
        if os.path.exists(_DIAG_LOG_PATH):
            os.remove(_DIAG_LOG_PATH)
    except Exception:
        pass
    
    _write_diag("=" * 50)
    _write_diag("main() 开始执行")
    
    try:
        _write_diag(f"APP_DIR = {APP_DIR}")
        _write_diag(f"__file__ = {__file__}")
        config_dir = os.path.join(APP_DIR, 'config')
        _write_diag(f"config_dir = {config_dir}")
        _write_diag(f"config exists = {os.path.exists(config_dir)}")
        
        _write_diag("创建应用实例...")
        app = RecoilControlUIv2()
        _write_diag("应用实例创建成功")
        
        _write_diag("进入主循环...")
        app.run()
    except Exception as e:
        error_msg = f"启动失败: {e}\n{_tb.format_exc()}"
        _write_diag(f"FATAL: {error_msg}")
        
        # 弹出错误对话框
        try:
            import tkinter as _tk
            _root = _tk.Tk()
            _root.withdraw()
            from tkinter import messagebox as _mb
            _mb.showerror("启动失败", f"程序启动失败:\n\n{error_msg[:500]}\n\n日志: {_DIAG_LOG_PATH}")
            _root.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    main()