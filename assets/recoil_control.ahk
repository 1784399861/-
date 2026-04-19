; IbInputSimulator 压枪脚本示例
; 使用前请确保已安装 IbInputSimulator 并正确配置驱动

#Requires AutoHotkey v2.0
#SingleInstance Force

; 配置参数
global RECOIL_PATTERN := [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] ; 每发子弹的下移像素
global FIRE_BUTTON := "LButton" ; 开火键
global TOGGLE_KEY := "F1" ; 开关热键
global ENABLED := true

; 初始化 IbInputSimulator
InitIbInputSimulator() {
    ; 尝试加载 IbInputSimulator.dll
    ; 使用脚本所在目录的绝对路径
    dllPath := A_ScriptDir "\IbInputSimulator.dll"
    
    ; 检查 DLL 是否存在
    if !FileExist(dllPath) {
        MsgBox "错误：找不到 IbInputSimulator.dll`n请确保 DLL 文件在脚本同一目录下。"
        ExitApp
    }
    
    ; 加载 DLL
    global hModule := DllCall("LoadLibrary", "Str", dllPath, "Ptr")
    if !hModule {
        MsgBox "错误：无法加载 IbInputSimulator.dll"
        ExitApp
    }
    
    ; 初始化 SendInput 驱动（最通用的选择）
    ; SendType: 1 = SendInput
    ; InitFlags: 0
    ; Argument: 0
    result := DllCall("IbInputSimulator\IbSendInit", "UInt", 1, "UInt", 0, "Ptr", 0, "UInt")
    if result != 0 {
        MsgBox "错误：IbSendInit 初始化失败，错误码：" result
        ExitApp
    }
    
    ToolTip "IbInputSimulator 初始化成功"
    SetTimer () => ToolTip(), -2000
}

; 模拟鼠标相对移动
MouseMoveRelative(x, y) {
    ; 使用 IbSendMouseMove 进行相对移动
    ; MoveMode: 1 = Relative
    return DllCall("IbInputSimulator\IbSendMouseMove", "UInt", x, "UInt", y, "UInt", 1, "Int")
}

; 压枪逻辑
RecoilControl() {
    static bulletIndex := 1
    
    if !ENABLED
        return
    
    ; 获取当前子弹对应的下移量
    if bulletIndex > RECOIL_PATTERN.Length
        bulletIndex := RECOIL_PATTERN.Length
    
    moveY := RECOIL_PATTERN[bulletIndex]
    
    ; 执行向下移动
    MouseMoveRelative(0, moveY)
    
    bulletIndex++
}

; 重置子弹计数
ResetBulletIndex() {
    static bulletIndex := 1
    bulletIndex := 1
}

; 主逻辑：监听鼠标按下
#HotIf ENABLED
~$*%FIRE_BUTTON%:: {
    static bulletIndex := 1
    
    ; 检查是否按下开火键
    if GetKeyState(FIRE_BUTTON, "P") {
        ; 开始压枪循环
        SetTimer RecoilControl, 10 ; 每10ms执行一次
    }
}

~$*%FIRE_BUTTON% up:: {
    ; 松开开火键，停止压枪
    SetTimer RecoilControl, 0
    ResetBulletIndex()
}
#HotIf

; 开关热键
%TOGGLE_KEY%:: {
    global ENABLED
    ENABLED := !ENABLED
    if ENABLED {
        ToolTip "压枪已开启"
    } else {
        ToolTip "压枪已关闭"
    }
    SetTimer () => ToolTip(), -1000
}

; 初始化
InitIbInputSimulator()

; 提示信息
MsgBox "IbInputSimulator 压枪脚本已启动`n`n热键说明：`n" TOGGLE_KEY " - 开关压枪功能`n" FIRE_BUTTON " - 开火时自动压枪`n`n请根据游戏调整 RECOIL_PATTERN 参数。", "压枪脚本", "T5"