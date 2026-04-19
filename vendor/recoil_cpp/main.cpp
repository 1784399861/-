#include <Windows.h>
#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>

// 包含 IbInputSimulator 头文件
// 请确保将 InputSimulator.hpp 放置在正确的位置
#include "InputSimulator.hpp"

// 配置参数
const std::vector<int> RECOIL_PATTERN = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20};
const int FIRE_BUTTON = VK_LBUTTON; // 鼠标左键
const int TOGGLE_KEY = VK_F1; // 开关热键
const int MOVE_INTERVAL_MS = 10; // 移动间隔（毫秒）

// 全局变量
std::atomic<bool> g_enabled(true);
std::atomic<bool> g_firing(false);
std::atomic<int> g_bulletIndex(0);
HHOOK g_mouseHook = NULL;
HHOOK g_keyboardHook = NULL;

// 初始化 IbInputSimulator
bool InitIbInputSimulator() {
    // 尝试初始化 SendInput 驱动（最通用）
    Send::Error result = IbSendInit(Send::SendType::SendInput, 0, nullptr);
    if (result != Send::Error::Success) {
        std::cerr << "IbSendInit 失败，错误码: " << static_cast<int>(result) << std::endl;
        return false;
    }
    std::cout << "IbInputSimulator 初始化成功" << std::endl;
    return true;
}

// 模拟鼠标相对移动
bool MoveMouseRelative(int x, int y) {
    return IbSendMouseMove(static_cast<uint32_t>(x), static_cast<uint32_t>(y), Send::MoveMode::Relative);
}

// 压枪线程函数
void RecoilControlThread() {
    while (true) {
        if (g_enabled && g_firing) {
            int bulletIndex = g_bulletIndex.load();
            if (bulletIndex < RECOIL_PATTERN.size()) {
                int moveY = RECOIL_PATTERN[bulletIndex];
                MoveMouseRelative(0, moveY);
                g_bulletIndex.fetch_add(1);
            } else {
                // 使用最后一个值
                int moveY = RECOIL_PATTERN.back();
                MoveMouseRelative(0, moveY);
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(MOVE_INTERVAL_MS));
    }
}

// 鼠标钩子过程
LRESULT CALLBACK MouseProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        MSLLHOOKSTRUCT* pMouseStruct = reinterpret_cast<MSLLHOOKSTRUCT*>(lParam);
        
        if (wParam == WM_LBUTTONDOWN) {
            g_firing = true;
            g_bulletIndex = 0;
        } else if (wParam == WM_LBUTTONUP) {
            g_firing = false;
            g_bulletIndex = 0;
        }
    }
    return CallNextHookEx(g_mouseHook, nCode, wParam, lParam);
}

// 键盘钩子过程
LRESULT CALLBACK KeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        KBDLLHOOKSTRUCT* pKeyboardStruct = reinterpret_cast<KBDLLHOOKSTRUCT*>(lParam);
        
        if (wParam == WM_KEYDOWN && pKeyboardStruct->vkCode == TOGGLE_KEY) {
            g_enabled = !g_enabled;
            if (g_enabled) {
                std::cout << "压枪已开启" << std::endl;
            } else {
                std::cout << "压枪已关闭" << std::endl;
            }
        }
    }
    return CallNextHookEx(g_keyboardHook, nCode, wParam, lParam);
}

// 安装钩子
bool InstallHooks() {
    g_mouseHook = SetWindowsHookEx(WH_MOUSE_LL, MouseProc, GetModuleHandle(NULL), 0);
    if (!g_mouseHook) {
        std::cerr << "安装鼠标钩子失败" << std::endl;
        return false;
    }
    
    g_keyboardHook = SetWindowsHookEx(WH_KEYBOARD_LL, KeyboardProc, GetModuleHandle(NULL), 0);
    if (!g_keyboardHook) {
        std::cerr << "安装键盘钩子失败" << std::endl;
        UnhookWindowsHookEx(g_mouseHook);
        return false;
    }
    
    std::cout << "钩子安装成功" << std::endl;
    return true;
}

// 卸载钩子
void UninstallHooks() {
    if (g_mouseHook) {
        UnhookWindowsHookEx(g_mouseHook);
        g_mouseHook = NULL;
    }
    if (g_keyboardHook) {
        UnhookWindowsHookEx(g_keyboardHook);
        g_keyboardHook = NULL;
    }
}

// 清理资源
void Cleanup() {
    UninstallHooks();
    IbSendDestroy();
}

int main() {
    std::cout << "=== IbInputSimulator 压枪程序 ===" << std::endl;
    std::cout << "热键说明：" << std::endl;
    std::cout << "  F1 - 开关压枪功能" << std::endl;
    std::cout << "  鼠标左键 - 开火时自动压枪" << std::endl;
    std::cout << "  ESC - 退出程序" << std::endl;
    std::cout << "=================================" << std::endl;
    
    // 初始化 IbInputSimulator
    if (!InitIbInputSimulator()) {
        std::cerr << "初始化失败，按任意键退出..." << std::endl;
        std::cin.get();
        return 1;
    }
    
    // 安装钩子
    if (!InstallHooks()) {
        std::cerr << "安装钩子失败，按任意键退出..." << std::endl;
        std::cin.get();
        Cleanup();
        return 1;
    }
    
    // 启动压枪线程
    std::thread recoilThread(RecoilControlThread);
    recoilThread.detach();
    
    std::cout << "程序启动成功！" << std::endl;
    std::cout << "当前状态：压枪已开启" << std::endl;
    
    // 主消息循环
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
        
        // 检测 ESC 键退出
        if (GetAsyncKeyState(VK_ESCAPE) & 0x8000) {
            break;
        }
    }
    
    // 清理资源
    Cleanup();
    std::cout << "程序已退出" << std::endl;
    
    return 0;
}