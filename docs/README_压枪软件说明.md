# IbInputSimulator 压枪软件

## 概述

本项目基于 **IbInputSimulator** 库实现压枪功能，通过驱动级输入模拟绕过游戏反作弊检测，提供更稳定的压枪效果。

## 两种实现方案

### 方案一：AutoHotkey 脚本（推荐新手）

**优点**：无需编译，修改方便，适合快速调整参数。

**文件**：`recoil_control.ahk`

**使用步骤**：
1. 下载 [IbInputSimulator](https://github.com/Chaoses-Ib/IbInputSimulator/releases) 最新版本
2. 将 `IbInputSimulator.dll` 和 `IbInputSimulator.ahk` 放到脚本同目录
3. 双击运行 `recoil_control.ahk`
4. 根据游戏调整 `RECOIL_PATTERN` 参数

**热键**：
- `F1` - 开关压枪功能
- `鼠标左键` - 开火时自动压枪

### 方案二：C++ 程序（推荐进阶用户）

**优点**：性能更好，延迟更低，可独立运行。

**目录**：`recoil_cpp/`

**编译步骤**：
1. 安装 [CMake](https://cmake.org/download/) 和 Visual Studio
2. 下载 IbInputSimulator 源码或预编译库
3. 将 `IbInputSimulator.lib` 放到 `recoil_cpp/lib/` 目录
4. 执行编译命令：
   ```bash
   cd recoil_cpp
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```
5. 将 `IbInputSimulator.dll` 复制到生成的 `recoil_control.exe` 同目录

**热键**：
- `F1` - 开关压枪功能
- `鼠标左键` - 开火时自动压枪
- `ESC` - 退出程序

## 配置说明

### 压枪模式 (RECOIL_PATTERN)

压枪模式是一个数组，每个元素代表对应子弹的鼠标下移像素值。

**示例**：
```cpp
// 基础模式（逐渐增加）
const std::vector<int> RECOIL_PATTERN = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20};

// 稳定模式（固定值）
const std::vector<int> RECOIL_PATTERN = {5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5};

// 脉冲模式（模拟点射）
const std::vector<int> RECOIL_PATTERN = {8, 8, 8, 0, 8, 8, 8, 0, 8, 8, 8, 0, 8, 8, 8, 0, 8, 8, 8};
```

### 驱动选择

IbInputSimulator 支持多种驱动后端，根据你的硬件和游戏选择：

| 驱动类型 | 适用场景 | 注意事项 |
|---------|---------|---------|
| `SendInput` | 通用，无需额外硬件 | 部分游戏可能检测 |
| `Logitech` | 罗技鼠标用户 | 需安装 LGS v9.02.65 |
| `LogitechGHubNew` | 新版 G HUB 用户 | 首次重启后鼠标可能失效 |
| `Razer` | 雷蛇鼠标用户 | 新版需要雷蛇硬件 |
| `DD` | 通用驱动 | 有蓝屏风险，需网络 |

**修改驱动类型**：
- **AutoHotkey**：修改 `IbSendInit()` 调用
- **C++**：修改 `IbSendInit(Send::SendType::SendInput, 0, nullptr)` 中的第一个参数

## 常见问题

### 1. 压枪无效
- 检查是否以管理员权限运行
- 尝试更换驱动类型
- 确认游戏是否支持该驱动

### 2. 鼠标移动不流畅
- 调整 `MOVE_INTERVAL_MS` 参数（默认10ms）
- 减小 `RECOIL_PATTERN` 中的数值

### 3. 程序无法启动
- 确保 `IbInputSimulator.dll` 在正确位置
- 检查是否安装了对应的驱动（如罗技 G HUB）

### 4. 被游戏检测
- 尝试使用驱动级输入（如 Logitech、Razer）
- 调整压枪模式，使其更接近手动操作
- 降低压枪强度

## 安全提示

1. **仅限单机游戏使用**：在多人在线游戏中使用可能违反游戏规则
2. **注意驱动风险**：DD 驱动可能导致蓝屏
3. **备份系统**：首次使用建议创建系统还原点
4. **管理员权限**：某些游戏需要管理员权限才能生效

## 文件结构

```
压枪软件/
├── recoil_control.ahk          # AutoHotkey 压枪脚本
├── recoil_cpp/                 # C++ 压枪程序
│   ├── main.cpp                # 主程序源码
│   ├── CMakeLists.txt          # CMake 配置文件
│   └── include/
│       └── InputSimulator.hpp  # IbInputSimulator 头文件
└── README_压枪软件说明.md      # 本说明文档
```

## 相关链接

- [IbInputSimulator GitHub](https://github.com/Chaoses-Ib/IbInputSimulator)
- [AutoHotkey 官网](https://www.autohotkey.com/)
- [CMake 官网](https://cmake.org/)

## 免责声明

本软件仅供学习和研究使用，使用本软件所产生的任何后果由用户自行承担。请遵守相关游戏的使用条款，不要在多人在线游戏中使用。