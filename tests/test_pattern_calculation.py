"""
测试轨迹计算逻辑
"""

import math

# 模拟lua_pattern数据
lua_pattern = [
    {"x": 0.0, "y": 0.0, "d": 3.5},
    {"x": 1.08, "y": 5.16, "d": 20.0},
    {"x": 0.25, "y": 5.55, "d": 20.0},
    {"x": -0.13, "y": 6.64, "d": 20.0},
    {"x": -1.14, "y": 6.88, "d": 20.0},
]

# 将相对位移转换为绝对坐标
absolute_points = []
x, y = 0, 0
for point in lua_pattern:
    dx = point.get("x", 0)
    dy = point.get("y", 0)
    x += dx
    y += dy
    absolute_points.append((x, y))

print("相对位移转绝对坐标:")
for i, (abs_x, abs_y) in enumerate(absolute_points):
    print(f"点{i+1}: ({abs_x:.2f}, {abs_y:.2f})")

# 计算边界
x_values = [p[0] for p in absolute_points]
y_values = [p[1] for p in absolute_points]

max_x = max(x_values) if x_values else 10
min_x = min(x_values) if x_values else -10
max_y = max(y_values) if y_values else 10
min_y = min(y_values) if y_values else 0

print(f"\n边界:")
print(f"X范围: {min_x:.2f} 到 {max_x:.2f}")
print(f"Y范围: {min_y:.2f} 到 {max_y:.2f}")

# 模拟Canvas坐标转换
canvas_width = 400
canvas_height = 300
margin = 40

# 计算缩放比例
x_range = max_x - min_x
y_range = max_y - min_y

scale_x = (canvas_width - 2 * margin) / x_range if x_range > 0 else 1
scale_y = (canvas_height - 2 * margin) / y_range if y_range > 0 else 1
scale = min(scale_x, scale_y) * 0.85

print(f"\n缩放比例: {scale:.2f}")

# 计算原点位置
origin_canvas_x = canvas_width / 2
origin_canvas_y = canvas_height / 2

# 转换为Canvas坐标
canvas_points = []
for abs_x, abs_y in absolute_points:
    canvas_x = origin_canvas_x + abs_x * scale
    canvas_y = origin_canvas_y + abs_y * scale
    canvas_points.append((canvas_x, canvas_y))

print(f"\nCanvas坐标:")
for i, (canvas_x, canvas_y) in enumerate(canvas_points):
    print(f"点{i+1}: ({canvas_x:.1f}, {canvas_y:.1f})")

# 检查是否有负数处理问题
print(f"\n检查负数处理:")
for i, point in enumerate(lua_pattern):
    x_val = point.get("x", 0)
    y_val = point.get("y", 0)
    print(f"点{i+1}: x={x_val}, y={y_val}, floor(x)={math.floor(x_val)}, floor(y)={math.floor(y_val)}")

print("\n测试完成！")