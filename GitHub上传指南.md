# GitHub 上传指南

## 仓库信息
- **仓库地址**: https://github.com/1784399861/-
- **当前版本**: v1.0.0

## 方法一：使用 git 命令行上传（推荐）

### 1. 安装 git
下载地址: https://git-scm.com/downloads

### 2. 配置 git（首次使用）
```bash
git config --global user.name "你的用户名"
git config --global user.email "你的邮箱"
```

### 3. 初始化并上传
```bash
cd "c:\Users\XOS\Desktop\压枪软件"

# 初始化 git 仓库（如果还没初始化）
git init

# 添加远程仓库
git remote add origin https://github.com/1784399861/-.git

# 添加所有文件
git add -A

# 提交
git commit -m "初始提交"

# 推送到 main 分支
git branch -M main
git push -u origin main
```

## 方法二：使用 GitHub Desktop（图形界面）

1. 下载 GitHub Desktop: https://desktop.github.com/
2. 登录你的 GitHub 账号
3. File → Add Local Repository
4. 选择 `c:\Users\XOS\Desktop\压枪软件`
5. 点击 "Publish repository"

## 方法三：网页直接上传

1. 访问: https://github.com/1784399861/-
2. 点击 "uploading an existing file"
3. 拖拽文件到网页或选择文件
4. 提交

---

# 自动更新功能使用说明

## 在软件中检查更新

1. 启动压枪控制中心
2. 点击左上角的「检查更新」按钮
3. 如有新版本，会提示是否更新
4. 确认后程序会启动独立更新脚本并退出

## 发布新版本

### 1. 更新版本号

修改以下文件中的版本号：
- `src/auto_updater.py`: `CURRENT_VERSION = "1.0.0"`
- `src/recoil_ui_v2.py`: `SOFTWARE_VERSION = "1.0.0"`

### 2. 打包新版本

使用 PyInstaller 打包：
```bash
cd scripts
build_pyinstaller.bat
```

### 3. 创建 GitHub Release

1. 访问: https://github.com/1784399861/-/releases/new
2. Tag version: `v1.0.1`（注意前面的 v）
3. Release title: `v1.0.1 - 更新说明`
4. 描述更新内容
5. 上传打包好的 exe 文件或 zip 压缩包
6. 点击 "Publish release"

### 4. 用户更新

用户点击「检查更新」按钮后：
- 自动检测到新版本
- 下载 Release 中的资产文件
- 解压并替换文件
- 自动重启程序

## 注意事项

- Release 的资产文件名建议包含版本号，如 `压枪软件_v1.0.1.zip`
- 更新时会自动备份当前版本到 `压枪软件.backup`
- 如更新失败，可从备份目录恢复
