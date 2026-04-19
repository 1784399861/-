"""
LUA压枪脚本解析器
解析LUA格式的压枪数据，转换为Python可用的格式
"""

import re
import json
from typing import List, Dict, Any, Optional


class LuaRecoilParser:
    """LUA压枪脚本解析器"""
    
    def __init__(self):
        self.weapons = []
        self.multipliers = []
        self.base_sensitivity_x = 1.0
        self.base_sensitivity_y = 1.0
        self.mode = 2
        self.switch_key = 4
        self.current_multiplier_index = 0
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析LUA文件
        
        Args:
            file_path: LUA文件路径
            
        Returns:
            包含武器数据、倍率等信息的字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析基础配置
            self._parse_config(content)
            
            # 解析武器数据
            self._parse_weapons(content)
            
            return {
                'weapons': self.weapons,
                'multipliers': self.multipliers,
                'base_sensitivity_x': self.base_sensitivity_x,
                'base_sensitivity_y': self.base_sensitivity_y,
                'mode': self.mode,
                'switch_key': self.switch_key
            }
            
        except Exception as e:
            print(f"解析LUA文件失败: {e}")
            return None
    
    def _parse_config(self, content: str):
        """解析基础配置"""
        # 解析模式
        mode_match = re.search(r'local\s+MODE\s*=\s*(\d+)', content)
        if mode_match:
            self.mode = int(mode_match.group(1))
        
        # 解析基础灵敏度
        base_y_match = re.search(r'local\s+BASE_YQXS_Y\s*=\s*([\d.]+)', content)
        if base_y_match:
            self.base_sensitivity_y = float(base_y_match.group(1))
        
        base_x_match = re.search(r'local\s+BASE_YQXS_X\s*=\s*([\d.]+)', content)
        if base_x_match:
            self.base_sensitivity_x = float(base_x_match.group(1))
        
        # 解析倍率列表
        multipliers_match = re.search(r'local\s+RECOIL_MULTIPLIERS\s*=\s*\{([^}]+)\}', content)
        if multipliers_match:
            multipliers_str = multipliers_match.group(1)
            # 提取所有数字
            numbers = re.findall(r'[\d.]+', multipliers_str)
            self.multipliers = [float(n) for n in numbers]
        
        # 解析倍率切换热键
        switch_key_match = re.search(r'local\s+KEY_SWITCH_MULTIPLIER\s*=\s*(\d+)', content)
        if switch_key_match:
            self.switch_key = int(switch_key_match.group(1))
        
        # 解析当前倍率索引（LUA从1开始，Python从0开始）
        index_match = re.search(r'local\s+CURRENT_MULTIPLIER_INDEX\s*=\s*(\d+)', content)
        if index_match:
            self.current_multiplier_index = max(0, int(index_match.group(1)) - 1)  # 转换为0-based
        else:
            self.current_multiplier_index = 0
    
    def _parse_weapons(self, content: str):
        """解析武器数据"""
        # 查找WEAPON_DATA表的开始位置
        start_match = re.search(r'local\s+WEAPON_DATA\s*=\s*\{', content)
        if not start_match:
            return
        
        start_pos = start_match.end()
        
        # 找到对应的结束位置（匹配大括号）
        brace_count = 1
        pos = start_pos
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        # 提取WEAPON_DATA表的内容
        weapon_data_str = content[start_pos:pos-1]
        
        # 使用更简单的方法匹配每个武器块
        # 查找所有 name = "..." 的位置
        name_pattern = re.compile(r'name\s*=\s*"([^"]+)"')
        name_matches = list(name_pattern.finditer(weapon_data_str))
        
        print(f"找到 {len(name_matches)} 个武器名称")
        
        for i, name_match in enumerate(name_matches):
            name = name_match.group(1)
            
            # 确定这个武器块的范围
            block_start = name_match.start()
            
            # 找到这个武器块的结束位置（下一个name或表结束）
            if i + 1 < len(name_matches):
                block_end = name_matches[i + 1].start()
            else:
                block_end = len(weapon_data_str)
            
            # 提取这个武器块的内容
            block_content = weapon_data_str[block_start:block_end]
            
            # 解析pattern - 使用括号匹配处理嵌套结构
            pattern_match = re.search(r'pattern\s*=\s*\{', block_content)
            if pattern_match:
                # 找到pattern开始位置
                pattern_start = pattern_match.end()
                # 使用括号匹配找到pattern结束位置
                brace_count = 1
                pos = pattern_start
                while pos < len(block_content) and brace_count > 0:
                    if block_content[pos] == '{':
                        brace_count += 1
                    elif block_content[pos] == '}':
                        brace_count -= 1
                    pos += 1
                
                # 提取整个pattern表内容
                pattern_str = block_content[pattern_start:pos-1]
                pattern = self._parse_pattern(pattern_str)
                
                # 解析key
                key_match = re.search(r'key\s*=\s*(\d+)', block_content)
                key = int(key_match.group(1)) if key_match else 0
                
                # 解析key_ctrl
                key_ctrl_match = re.search(r'key_ctrl\s*=\s*(\w+)', block_content)
                key_ctrl = 0
                if key_ctrl_match:
                    key_ctrl_str = key_ctrl_match.group(1)
                    if key_ctrl_str.isdigit():
                        key_ctrl = int(key_ctrl_str)
                    else:
                        # 如果是变量名，尝试从内容中查找对应的值
                        var_match = re.search(rf'local\s+{key_ctrl_str}\s*=\s*(\d+)', content)
                        if var_match:
                            key_ctrl = int(var_match.group(1))
                
                if pattern:
                    weapon = {
                        'name': name,
                        'pattern': pattern,
                        'key': key,
                        'key_ctrl': key_ctrl,
                        'fire_rate': self._calculate_fire_rate(pattern),
                        'enabled': True,
                        'description': f'从LUA导入: {name}'
                    }
                    self.weapons.append(weapon)
    
    def _parse_pattern(self, pattern_str: str) -> List[Dict[str, float]]:
        """
        解析压枪轨迹
        
        Args:
            pattern_str: 轨迹字符串，如 "{x=0,y=0,d=3.5},{x=1.08,y=5.16,d=20.0},..."
            
        Returns:
            轨迹列表，每个元素包含x, y, d
        """
        pattern = []
        
        # 匹配每个点 {x=...,y=...,d=...}
        point_pattern = re.compile(r'\{x=([-\d.]+),y=([-\d.]+),d=([\d.]+)\}')
        
        for match in point_pattern.finditer(pattern_str):
            x = float(match.group(1))
            y = float(match.group(2))
            d = float(match.group(3))
            
            pattern.append({
                'x': x,
                'y': y,
                'd': d
            })
        
        return pattern
    
    def _calculate_fire_rate(self, pattern: List[Dict[str, float]]) -> int:
        """
        计算平均射速（毫秒）
        
        Args:
            pattern: 压枪轨迹
            
        Returns:
            平均延迟时间（毫秒）
        """
        if not pattern:
            return 10
        
        # 跳过第一个点（通常是初始点）
        if len(pattern) > 1:
            delays = [p['d'] for p in pattern[1:]]
            avg_delay = sum(delays) / len(delays)
            return int(avg_delay)
        
        return int(pattern[0]['d']) if pattern else 10
    
    def convert_to_json_format(self) -> Dict[str, Any]:
        """
        转换为JSON格式（兼容现有weapons.json格式）
        
        Returns:
            JSON格式的武器配置
        """
        weapons_json = {}
        
        for weapon in self.weapons:
            # 转换pattern格式：从[{x,y,d}]转换为[y值列表]
            # 注意：这里只保留Y值，因为现有系统只使用Y轴
            pattern_y = [int(p['y']) for p in weapon['pattern']]
            
            weapons_json[weapon['name']] = {
                'name': weapon['name'],
                'pattern': pattern_y,
                'fire_rate': weapon['fire_rate'],
                'enabled': weapon['enabled'],
                'description': weapon['description'],
                # 保存原始数据用于高级功能
                'lua_pattern': weapon['pattern'],
                'lua_key': weapon['key'],
                'lua_key_ctrl': weapon['key_ctrl'],
                # 添加倍率数组（默认使用全局倍率）
                'multipliers': self.multipliers if self.multipliers else [1.0],
                'current_multiplier_index': self.current_multiplier_index,
                # 保存基础灵敏度（与LUA的BASE_YQXS对应）
                'base_yqxs_y': self.base_sensitivity_y,
                'base_yqxs_x': self.base_sensitivity_x,
                # 保存触发模式（与LUA的MODE对应：1=仅左键，2=左键+右键）
                'mode': self.mode
            }
        
        return weapons_json
    
    def save_to_json(self, output_path: str) -> bool:
        """
        保存为JSON文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否保存成功
        """
        try:
            weapons_json = self.convert_to_json_format()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(weapons_json, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
            return False


def test_parser():
    """测试解析器"""
    parser = LuaRecoilParser()
    
    # 解析LUA文件
    lua_file = r"c:\Users\XOS\Desktop\压枪软件\新脚本 V4.10.lua"
    
    # 读取文件内容进行调试
    with open(lua_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查WEAPON_DATA是否存在
    if 'WEAPON_DATA' in content:
        print("找到WEAPON_DATA")
        # 查找WEAPON_DATA表
        weapon_data_match = re.search(r'local\s+WEAPON_DATA\s*=\s*\{(.*?)\n\}\s*$', content, re.DOTALL)
        if weapon_data_match:
            print(f"匹配到WEAPON_DATA表，长度: {len(weapon_data_match.group(1))}")
            # 显示前500个字符
            print(f"内容预览: {weapon_data_match.group(1)[:500]}...")
        else:
            print("未匹配到WEAPON_DATA表")
            # 尝试其他模式
            weapon_data_match2 = re.search(r'local\s+WEAPON_DATA\s*=\s*\{', content)
            if weapon_data_match2:
                print(f"找到WEAPON_DATA开始位置: {weapon_data_match2.start()}")
                # 找到对应的结束位置
                start_pos = weapon_data_match2.end()
                brace_count = 1
                pos = start_pos
                while pos < len(content) and brace_count > 0:
                    if content[pos] == '{':
                        brace_count += 1
                    elif content[pos] == '}':
                        brace_count -= 1
                    pos += 1
                print(f"WEAPON_DATA结束位置: {pos}")
                print(f"内容长度: {pos - start_pos}")
    
    result = parser.parse_file(lua_file)
    
    if result:
        print(f"\n解析成功!")
        print(f"武器数量: {len(result['weapons'])}")
        print(f"倍率列表: {result['multipliers']}")
        print(f"基础灵敏度: X={result['base_sensitivity_x']}, Y={result['base_sensitivity_y']}")
        print(f"模式: {result['mode']}")
        
        print("\n武器列表:")
        for i, weapon in enumerate(result['weapons'], 1):
            print(f"{i}. {weapon['name']} - {len(weapon['pattern'])}个点, 射速{weapon['fire_rate']}ms")
        
        # 保存为JSON
        output_file = r"c:\Users\XOS\Desktop\压枪软件\config\weapons_lua.json"
        if parser.save_to_json(output_file):
            print(f"\n已保存到: {output_file}")
    else:
        print("解析失败!")


if __name__ == "__main__":
    test_parser()