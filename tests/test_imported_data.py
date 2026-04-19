"""
测试导入的武器数据格式
"""

import sys
import os
import json

# 添加 src 目录到 Python 路径
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "src"))

try:
    # 导入解析器
    from lua_parser import LuaRecoilParser
    
    # 创建解析器实例
    parser = LuaRecoilParser()
    
    # 解析LUA文件
    lua_file = os.path.join(_project_root, "assets", "新脚本 V4.10.lua")
    
    if not os.path.exists(lua_file):
        print(f"[FAIL] LUA文件不存在: {lua_file}")
        sys.exit(1)
    
    print(f"[INFO] 开始解析LUA文件: {lua_file}")
    
    result = parser.parse_file(lua_file)
    
    if not result:
        print("[FAIL] 解析LUA文件失败")
        sys.exit(1)
    
    # 转换为JSON格式
    weapons_json = parser.convert_to_json_format()
    
    # 检查第一个武器的数据格式
    if weapons_json:
        first_name = list(weapons_json.keys())[0]
        first_weapon = weapons_json[first_name]
        
        print(f"\n[INFO] 第一个武器: {first_name}")
        print(f"[INFO] 武器数据键: {list(first_weapon.keys())}")
        
        # 检查pattern
        pattern = first_weapon.get('pattern', [])
        print(f"[INFO] pattern类型: {type(pattern)}")
        print(f"[INFO] pattern长度: {len(pattern)}")
        if pattern:
            print(f"[INFO] pattern前5个元素: {pattern[:5]}")
            print(f"[INFO] pattern第一个元素类型: {type(pattern[0])}")
        
        # 检查lua_pattern
        lua_pattern = first_weapon.get('lua_pattern', [])
        print(f"\n[INFO] lua_pattern类型: {type(lua_pattern)}")
        print(f"[INFO] lua_pattern长度: {len(lua_pattern)}")
        if lua_pattern:
            print(f"[INFO] lua_pattern第一个元素: {lua_pattern[0]}")
            print(f"[INFO] lua_pattern第一个元素类型: {type(lua_pattern[0])}")
        
        # 保存到文件以便检查
        with open('config/test_weapon.json', 'w', encoding='utf-8') as f:
            json.dump(first_weapon, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 已保存到 config/test_weapon.json")
    
    print("\n[OK] 测试完成！")
    
except Exception as e:
    print(f"[FAIL] 测试失败: {e}")
    import traceback
    traceback.print_exc()