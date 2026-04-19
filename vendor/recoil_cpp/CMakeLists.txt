cmake_minimum_required(VERSION 3.10)
project(RecoilControl)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 设置输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 添加可执行文件
add_executable(recoil_control main.cpp)

# 链接 Windows 库
target_link_libraries(recoil_control PRIVATE user32)

# 如果需要链接 IbInputSimulator 库，请取消注释以下行
# 并确保 IbInputSimulator.lib 文件在正确的位置
# target_link_libraries(recoil_control PRIVATE ${CMAKE_SOURCE_DIR}/lib/IbInputSimulator.lib)

# 设置管理员权限（可选，某些游戏需要）
# set_target_properties(recoil_control PROPERTIES LINK_FLAGS "/MANIFESTUAC:\"level='requireAdministrator'\"")

# 安装规则
install(TARGETS recoil_control DESTINATION bin)