#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 仓库初始化脚本
创建仓库并上传项目
"""

import os
import sys
import requests
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

# 配置
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = "1784399861"
REPO_NAME = "-"
REPO_DESCRIPTION = "基于 IbInputSimulator 驱动级输入模拟的游戏压枪工具"
REPO_PRIVATE = False  # 设为 True 则创建私有仓库

PROJECT_DIR = Path(__file__).parent
API_BASE = "https://api.github.com"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Python-GitHub-Init"
}


def check_git():
    """检查 git 是否可用"""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except:
        return False


def create_repo():
    """创建 GitHub 仓库"""
    url = f"{API_BASE}/user/repos"
    data = {
        "name": REPO_NAME,
        "description": REPO_DESCRIPTION,
        "private": REPO_PRIVATE,
        "auto_init": False  # 我们自己初始化
    }
    
    print(f"正在创建仓库: {REPO_NAME}")
    response = requests.post(url, headers=HEADERS, json=data)
    
    if response.status_code == 201:
        repo_info = response.json()
        print(f"仓库创建成功: {repo_info['html_url']}")
        return repo_info
    elif response.status_code == 422:
        # 仓库已存在，获取信息
        print("仓库已存在，获取信息...")
        return get_repo_info()
    else:
        print(f"创建仓库失败: {response.status_code}")
        print(response.text)
        return None


def get_repo_info():
    """获取仓库信息"""
    url = f"{API_BASE}/repos/{GITHUB_OWNER}/{REPO_NAME}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None


def init_git_and_push(repo_info):
    """初始化 git 并推送"""
    clone_url = repo_info["clone_url"]
    # 替换为带 token 的 URL
    auth_url = clone_url.replace("https://", f"https://x-access-token:{GITHUB_TOKEN}@")
    
    print(f"\n正在初始化 git 仓库...")
    
    # 切换到项目目录
    os.chdir(PROJECT_DIR)
    
    # 检查是否已初始化
    if not (PROJECT_DIR / ".git").exists():
        subprocess.run(["git", "init"], check=True)
        print("git init 完成")
    else:
        print(".git 目录已存在")
    
    # 创建 .gitignore
    gitignore = PROJECT_DIR / ".gitignore"
    if not gitignore.exists():
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
crash.log
startup_debug.log

# Build artifacts
recoil_ui_v2.dist/
pyinstaller_dist/
*.exe

# Config (可选，视情况而定)
# config/
""")
        print(".gitignore 已创建")
    
    # 添加远程仓库
    try:
        subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    except:
        pass
    
    subprocess.run(["git", "remote", "add", "origin", auth_url], check=True)
    print("远程仓库已添加")
    
    # 添加所有文件
    subprocess.run(["git", "add", "-A"], check=True)
    print("文件已添加")
    
    # 提交
    try:
        subprocess.run(["git", "commit", "-m", "初始提交"], check=True)
    except subprocess.CalledProcessError:
        # 可能已经提交过
        print("可能已经有提交了")
    
    # 推送到 main 分支
    print("\n正在推送到 GitHub...")
    try:
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=True)
        print(f"\n推送成功！")
        print(f"仓库地址: {repo_info['html_url']}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"推送失败: {e}")
        return False


def create_release(repo_info, tag_name="v1.0.0", name="v1.0.0", body="初始版本"):
    """创建 Release"""
    url = f"{API_BASE}/repos/{GITHUB_OWNER}/{REPO_NAME}/releases"
    data = {
        "tag_name": tag_name,
        "name": name,
        "body": body,
        "draft": False,
        "prerelease": False
    }
    
    print(f"\n创建 Release: {tag_name}")
    response = requests.post(url, headers=HEADERS, json=data)
    
    if response.status_code == 201:
        release_info = response.json()
        print(f"Release 创建成功: {release_info['html_url']}")
        return release_info
    elif response.status_code == 422:
        print("Release 已存在")
        # 获取已有 release
        url = f"{API_BASE}/repos/{GITHUB_OWNER}/{REPO_NAME}/releases/tags/{tag_name}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        return None
    else:
        print(f"创建 Release 失败: {response.status_code}")
        print(response.text)
        return None


def update_auto_updater_config():
    """更新 auto_updater.py 中的配置"""
    auto_updater_path = PROJECT_DIR / "src" / "auto_updater.py"
    
    if not auto_updater_path.exists():
        print(f"未找到: {auto_updater_path}")
        return False
    
    content = auto_updater_path.read_text(encoding="utf-8")
    
    # 更新配置
    old_config = '''# GitHub 仓库信息
GITHUB_OWNER = "XOS"  # 会根据实际情况更新
GITHUB_REPO = "压枪软件"'''
    
    new_config = '''# GitHub 仓库信息
GITHUB_OWNER = "XOS"
GITHUB_REPO = "压枪软件"'''
    
    content = content.replace(old_config, new_config)
    
    auto_updater_path.write_text(content, encoding="utf-8")
    print("auto_updater.py 配置已更新")
    return True


def main():
    print("=" * 60)
    print("GitHub 仓库初始化工具")
    print("=" * 60)
    
    # 更新 auto_updater 配置
    update_auto_updater_config()
    
    # 创建仓库
    repo_info = create_repo()
    if not repo_info:
        return 1
    
    # 创建初始 Release
    create_release(
        repo_info,
        tag_name="v1.0.0",
        name="v1.0.0 - 初始版本",
        body="""## 压枪软件 v1.0.0

基于 IbInputSimulator 驱动级输入模拟的游戏压枪工具

### 主要功能
- 驱动级鼠标输入模拟（支持 SendInput、罗技、雷蛇等多种驱动）
- LUA 脚本导入（支持 42 种武器数据）
- 压枪轨迹可视化
- 力度控制滑块（0.1x-3.0x）
- 倍镜切换（1.0x-6.0x）
- 武器列表批量操作
- 自动更新功能

### 使用说明
1. 双击 `启动压枪控制中心v2.bat` 启动
2. 选择武器或导入 LUA 脚本
3. 调整力度和倍镜参数
4. 游戏中按住鼠标左键+右键触发压枪

### 更新方式
点击界面中的「检查更新」按钮即可获取最新版本
"""
    )
    
    print("\n" + "=" * 60)
    print("初始化完成！")
    print(f"仓库地址: {repo_info['html_url']}")
    
    has_git = check_git()
    if not has_git:
        print("\n注意: 未检测到 git，请按以下步骤操作：")
        print("1. 下载并安装 git: https://git-scm.com/downloads")
        print("2. 安装完成后重新运行此脚本")
        print("3. 或访问仓库地址手动上传文件")
    else:
        # 有 git，尝试初始化并推送
        print("\n检测到 git，正在初始化并推送...")
        init_git_and_push(repo_info)
    
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
