"""
压枪轨迹录制模块
支持手动标记弹孔位置，生成压枪轨迹数据
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math


class PatternRecorder:
    """压枪轨迹录制器"""
    
    def __init__(self, parent, callback=None):
        """
        初始化录制器
        
        Args:
            parent: 父窗口
            callback: 数据生成后的回调函数
        """
        self.parent = parent
        self.callback = callback
        
        # 标记点数据: [(x, y, index), ...]
        self.marks = []
        
        # 当前选中的标记
        self.selected_mark = None
        
        # 画布尺寸
        self.canvas_width = 600
        self.canvas_height = 400
        
        # 原点位置（画布中心）
        self.origin_x = self.canvas_width // 2
        self.origin_y = self.canvas_height // 2
        
        # 缩放比例
        self.scale = 1.0
        
        # 武器配置
        self.weapon_name = "新武器"
        self.fire_rate = 10  # 毫秒
        
    def show(self):
        """显示录制窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("压枪轨迹录制器")
        self.window.geometry("800x600")
        self.window.configure(bg="#2b2b2b")
        
        # 创建UI
        self._create_ui()
        
        # 绑定快捷键
        self._bind_shortcuts()
        
    def _create_ui(self):
        """创建UI界面"""
        # 顶部工具栏
        toolbar = tk.Frame(self.window, bg="#3b3b3b", height=50)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 武器名称
        tk.Label(toolbar, text="武器名称:", bg="#3b3b3b", fg="white").pack(side=tk.LEFT, padx=5)
        self.name_entry = tk.Entry(toolbar, width=15)
        self.name_entry.insert(0, self.weapon_name)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        
        # 射速
        tk.Label(toolbar, text="射速(ms):", bg="#3b3b3b", fg="white").pack(side=tk.LEFT, padx=5)
        self.rate_entry = tk.Entry(toolbar, width=8)
        self.rate_entry.insert(0, str(self.fire_rate))
        self.rate_entry.pack(side=tk.LEFT, padx=5)
        
        # 按钮
        ttk.Button(toolbar, text="清空标记", command=self.clear_marks).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="撤销", command=self.undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="生成数据", command=self.generate_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导入数据", command=self.import_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出JSON", command=self.export_json).pack(side=tk.LEFT, padx=5)
        
        # 主区域
        main_frame = tk.Frame(self.window, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧画布
        canvas_frame = tk.Frame(main_frame, bg="#1a1a1a")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定画布事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # 右侧面板
        right_panel = tk.Frame(main_frame, bg="#2b2b2b", width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # 标记列表
        list_frame = tk.LabelFrame(right_panel, text="标记点列表", bg="#2b2b2b", fg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.mark_listbox = tk.Listbox(list_frame, bg="#1a1a1a", fg="white", selectbackground="#444")
        self.mark_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.mark_listbox.bind("<<ListboxSelect>>", self.on_list_select)
        
        # 数据预览
        preview_frame = tk.LabelFrame(right_panel, text="数据预览", bg="#2b2b2b", fg="white")
        preview_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.preview_text = tk.Text(preview_frame, height=8, bg="#1a1a1a", fg="#00ff00", font=("Consolas", 9))
        self.preview_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态栏
        status_frame = tk.Frame(self.window, bg="#3b3b3b", height=30)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.status_label = tk.Label(status_frame, text="就绪 - 点击画布添加标记点", bg="#3b3b3b", fg="white")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.mark_count_label = tk.Label(status_frame, text="标记数: 0", bg="#3b3b3b", fg="white")
        self.mark_count_label.pack(side=tk.RIGHT, padx=10)
        
        # 绘制初始画布
        self.draw_canvas()
        
    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.window.bind("<Control-z>", lambda e: self.undo())
        self.window.bind("<Delete>", lambda e: self.delete_selected())
        self.window.bind("<Escape>", lambda e: self.deselect())
        
    def on_resize(self, event):
        """画布大小改变"""
        self.canvas_width = event.width
        self.canvas_height = event.height
        self.origin_x = self.canvas_width // 2
        self.origin_y = self.canvas_height // 2
        self.draw_canvas()
        
    def on_click(self, event):
        """左键点击"""
        # 检查是否点击了现有标记
        clicked_mark = self.find_mark_at(event.x, event.y)
        
        if clicked_mark is not None:
            # 选中标记
            self.selected_mark = clicked_mark
            self.draw_canvas()
        else:
            # 添加新标记
            x = (event.x - self.origin_x) / self.scale
            y = (event.y - self.origin_y) / self.scale
            
            index = len(self.marks) + 1
            self.marks.append((x, y, index))
            self.selected_mark = len(self.marks) - 1
            
            self.update_list()
            self.draw_canvas()
            self.update_preview()
            
            self.status_label.config(text=f"添加标记 #{index}: ({x:.1f}, {y:.1f})")
            
    def on_drag(self, event):
        """拖拽标记"""
        if self.selected_mark is not None:
            x = (event.x - self.origin_x) / self.scale
            y = (event.y - self.origin_y) / self.scale
            
            # 更新标记位置
            old_x, old_y, index = self.marks[self.selected_mark]
            self.marks[self.selected_mark] = (x, y, index)
            
            self.draw_canvas()
            self.update_preview()
            
    def on_release(self, event):
        """释放鼠标"""
        if self.selected_mark is not None:
            self.update_list()
            
    def on_right_click(self, event):
        """右键菜单"""
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="删除标记", command=self.delete_selected)
        menu.add_command(label="编辑坐标", command=self.edit_mark)
        menu.add_separator()
        menu.add_command(label="清空所有", command=self.clear_marks)
        
        menu.tk_popup(event.x_root, event.y_root)
        
    def on_list_select(self, event):
        """列表选择"""
        selection = self.mark_listbox.curselection()
        if selection:
            self.selected_mark = selection[0]
            self.draw_canvas()
            
    def find_mark_at(self, x, y, radius=10):
        """查找点击位置的标记"""
        for i, (mx, my, _) in enumerate(self.marks):
            screen_x = self.origin_x + mx * self.scale
            screen_y = self.origin_y + my * self.scale
            
            distance = math.sqrt((x - screen_x)**2 + (y - screen_y)**2)
            if distance <= radius:
                return i
        return None
        
    def draw_canvas(self):
        """绘制画布"""
        self.canvas.delete("all")
        
        # 绘制网格
        self.draw_grid()
        
        # 绘制坐标轴
        self.draw_axes()
        
        # 绘制标记点
        self.draw_marks()
        
    def draw_grid(self):
        """绘制网格"""
        grid_size = 50
        grid_color = "#333333"
        
        # 垂直线
        x = self.origin_x % grid_size
        while x < self.canvas_width:
            self.canvas.create_line(x, 0, x, self.canvas_height, fill=grid_color, dash=(2, 2))
            x += grid_size
            
        # 水平线
        y = self.origin_y % grid_size
        while y < self.canvas_height:
            self.canvas.create_line(0, y, self.canvas_width, y, fill=grid_color, dash=(2, 2))
            y += grid_size
            
    def draw_axes(self):
        """绘制坐标轴"""
        axis_color = "#666666"
        
        # X轴
        self.canvas.create_line(0, self.origin_y, self.canvas_width, self.origin_y, 
                               fill=axis_color, width=2)
        
        # Y轴
        self.canvas.create_line(self.origin_x, 0, self.origin_x, self.canvas_height, 
                               fill=axis_color, width=2)
        
        # 原点标记
        self.canvas.create_oval(self.origin_x-5, self.origin_y-5, 
                               self.origin_x+5, self.origin_y+5, 
                               fill="white", outline="gray")
        
        # 标签
        self.canvas.create_text(self.canvas_width - 20, self.origin_y + 15, 
                               text="X", fill="white", anchor="w")
        self.canvas.create_text(self.origin_x + 15, 20, 
                               text="Y", fill="white", anchor="w")
        
    def draw_marks(self):
        """绘制标记点"""
        for i, (x, y, index) in enumerate(self.marks):
            screen_x = self.origin_x + x * self.scale
            screen_y = self.origin_y + y * self.scale
            
            # 选中状态
            is_selected = (i == self.selected_mark)
            
            # 颜色渐变
            ratio = i / max(len(self.marks) - 1, 1)
            r = int(255 * (1 - ratio))
            g = int(255 * ratio)
            b = 255
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # 绘制点
            size = 8 if is_selected else 5
            self.canvas.create_oval(screen_x - size, screen_y - size,
                                   screen_x + size, screen_y + size,
                                   fill=color, outline="white" if is_selected else "gray",
                                   width=2 if is_selected else 1)
            
            # 绘制序号
            self.canvas.create_text(screen_x + 12, screen_y, 
                                   text=str(index), fill="white", anchor="w")
            
            # 绘制连线
            if i > 0:
                prev_x, prev_y, _ = self.marks[i-1]
                prev_screen_x = self.origin_x + prev_x * self.scale
                prev_screen_y = self.origin_y + prev_y * self.scale
                
                self.canvas.create_line(prev_screen_x, prev_screen_y, 
                                       screen_x, screen_y,
                                       fill=color, width=2, dash=(4, 2))
                
    def update_list(self):
        """更新标记列表"""
        self.mark_listbox.delete(0, tk.END)
        for i, (x, y, index) in enumerate(self.marks):
            self.mark_listbox.insert(tk.END, f"#{index}: ({x:.1f}, {y:.1f})")
            
        self.mark_count_label.config(text=f"标记数: {len(self.marks)}")
        
    def update_preview(self):
        """更新数据预览"""
        self.preview_text.delete("1.0", tk.END)
        
        if not self.marks:
            self.preview_text.insert(tk.END, "暂无数据")
            return
            
        # 生成相对位移数据
        data = []
        for i, (x, y, index) in enumerate(self.marks):
            if i == 0:
                dx, dy = 0, 0
            else:
                prev_x, prev_y, _ = self.marks[i-1]
                dx = x - prev_x
                dy = y - prev_y
                
            data.append(f"第{index}发: x={dx:.2f}, y={dy:.2f}")
            
        self.preview_text.insert(tk.END, "\n".join(data[:10]))
        if len(data) > 10:
            self.preview_text.insert(tk.END, f"\n... 共{len(data)}发")
            
    def clear_marks(self):
        """清空标记"""
        if messagebox.askyesno("确认", "确定要清空所有标记吗？"):
            self.marks = []
            self.selected_mark = None
            self.update_list()
            self.draw_canvas()
            self.update_preview()
            self.status_label.config(text="已清空所有标记")
            
    def delete_selected(self):
        """删除选中的标记"""
        if self.selected_mark is not None:
            del self.marks[self.selected_mark]
            self.selected_mark = None
            self.update_list()
            self.draw_canvas()
            self.update_preview()
            
    def deselect(self):
        """取消选择"""
        self.selected_mark = None
        self.draw_canvas()
        
    def undo(self):
        """撤销"""
        if self.marks:
            self.marks.pop()
            self.selected_mark = None
            self.update_list()
            self.draw_canvas()
            self.update_preview()
            self.status_label.config(text="已撤销")
            
    def edit_mark(self):
        """编辑标记坐标"""
        if self.selected_mark is None:
            return
            
        x, y, index = self.marks[self.selected_mark]
        
        # 创建编辑对话框
        dialog = tk.Toplevel(self.window)
        dialog.title(f"编辑标记 #{index}")
        dialog.geometry("250x150")
        dialog.configure(bg="#2b2b2b")
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="X坐标:", bg="#2b2b2b", fg="white").pack(pady=5)
        x_entry = tk.Entry(dialog)
        x_entry.insert(0, str(x))
        x_entry.pack(pady=5)
        
        tk.Label(dialog, text="Y坐标:", bg="#2b2b2b", fg="white").pack(pady=5)
        y_entry = tk.Entry(dialog)
        y_entry.insert(0, str(y))
        y_entry.pack(pady=5)
        
        def save():
            try:
                new_x = float(x_entry.get())
                new_y = float(y_entry.get())
                self.marks[self.selected_mark] = (new_x, new_y, index)
                self.update_list()
                self.draw_canvas()
                self.update_preview()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
                
        ttk.Button(dialog, text="保存", command=save).pack(pady=10)
        
    def generate_data(self):
        """生成压枪数据"""
        if not self.marks:
            messagebox.showwarning("警告", "没有标记点数据")
            return
            
        # 获取配置
        self.weapon_name = self.name_entry.get().strip() or "新武器"
        try:
            self.fire_rate = int(self.rate_entry.get())
        except ValueError:
            self.fire_rate = 10
            
        # 生成lua_pattern格式数据
        lua_pattern = []
        for i, (x, y, index) in enumerate(self.marks):
            if i == 0:
                dx, dy = 0, 0
            else:
                prev_x, prev_y, _ = self.marks[i-1]
                dx = x - prev_x
                dy = y - prev_y
                
            lua_pattern.append({
                "x": round(dx, 2),
                "y": round(dy, 2),
                "d": self.fire_rate
            })
            
        # 生成pattern格式（Y值列表）
        pattern = [int(round(m[1])) for m in self.marks]
        
        # 构建武器数据
        weapon_data = {
            "name": self.weapon_name,
            "pattern": pattern,
            "lua_pattern": lua_pattern,
            "fire_rate": self.fire_rate,
            "enabled": True,
            "description": f"轨迹录制: {self.weapon_name}"
        }
        
        # 调用回调
        if self.callback:
            self.callback(weapon_data)
            messagebox.showinfo("成功", f"已生成 {self.weapon_name} 的压枪数据\n共 {len(lua_pattern)} 个点")
        else:
            # 显示数据
            self.show_data_dialog(weapon_data)
            
    def show_data_dialog(self, weapon_data):
        """显示数据对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("生成的压枪数据")
        dialog.geometry("500x400")
        dialog.configure(bg="#2b2b2b")
        dialog.transient(self.window)
        
        # 数据显示
        text = tk.Text(dialog, bg="#1a1a1a", fg="#00ff00", font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text.insert(tk.END, json.dumps(weapon_data, indent=2, ensure_ascii=False))
        
        # 复制按钮
        def copy_data():
            self.window.clipboard_clear()
            self.window.clipboard_append(json.dumps(weapon_data, indent=2, ensure_ascii=False))
            messagebox.showinfo("成功", "已复制到剪贴板")
            
        ttk.Button(dialog, text="复制数据", command=copy_data).pack(pady=10)
        
    def import_data(self):
        """导入数据"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 尝试从lua_pattern导入
            if "lua_pattern" in data:
                lua_pattern = data["lua_pattern"]
                marks = []
                x, y = 0, 0
                
                for i, point in enumerate(lua_pattern):
                    x += point.get("x", 0)
                    y += point.get("y", 0)
                    marks.append((x, y, i + 1))
                    
                self.marks = marks
                self.weapon_name = data.get("name", "导入武器")
                self.fire_rate = data.get("fire_rate", 10)
                
            # 尝试从pattern导入
            elif "pattern" in data:
                pattern = data["pattern"]
                marks = []
                
                for i, y in enumerate(pattern):
                    if isinstance(y, dict):
                        # 完整格式
                        marks.append((y.get("x", 0), y.get("y", 0), i + 1))
                    else:
                        # 简单Y值格式
                        marks.append((0, y, i + 1))
                        
                self.marks = marks
                self.weapon_name = data.get("name", "导入武器")
                self.fire_rate = data.get("fire_rate", 10)
                
            else:
                messagebox.showerror("错误", "无法识别的数据格式")
                return
                
            # 更新UI
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self.weapon_name)
            self.rate_entry.delete(0, tk.END)
            self.rate_entry.insert(0, str(self.fire_rate))
            
            self.update_list()
            self.draw_canvas()
            self.update_preview()
            
            self.status_label.config(text=f"已导入 {len(self.marks)} 个标记点")
            messagebox.showinfo("成功", f"已导入 {len(self.marks)} 个标记点")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")
            
    def export_json(self):
        """导出JSON文件"""
        if not self.marks:
            messagebox.showwarning("警告", "没有标记点数据")
            return
            
        # 生成数据
        self.weapon_name = self.name_entry.get().strip() or "新武器"
        try:
            self.fire_rate = int(self.rate_entry.get())
        except ValueError:
            self.fire_rate = 10
            
        # 生成lua_pattern格式数据
        lua_pattern = []
        for i, (x, y, index) in enumerate(self.marks):
            if i == 0:
                dx, dy = 0, 0
            else:
                prev_x, prev_y, _ = self.marks[i-1]
                dx = x - prev_x
                dy = y - prev_y
                
            lua_pattern.append({
                "x": round(dx, 2),
                "y": round(dy, 2),
                "d": self.fire_rate
            })
            
        # 生成pattern格式（Y值列表）
        pattern = [int(round(m[1])) for m in self.marks]
        
        # 构建武器数据
        weapon_data = {
            "name": self.weapon_name,
            "pattern": pattern,
            "lua_pattern": lua_pattern,
            "fire_rate": self.fire_rate,
            "enabled": True,
            "description": f"轨迹录制: {self.weapon_name}"
        }
        
        # 保存文件
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")],
            initialfile=f"{self.weapon_name}.json"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(weapon_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("成功", f"已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    def on_data_generated(data):
        print("生成的数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    recorder = PatternRecorder(root, callback=on_data_generated)
    recorder.show()
    
    root.mainloop()
