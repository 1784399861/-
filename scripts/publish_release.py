#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 发布脚本
用于手动发布新版本，推送代码并创建 Release
"""

import os
import sys
import subprocess
import requests
import json
from datetime import datetime

# ================== 配置区域（请修改这里） ==================

# 版本号（每次发布前修改这里）
VERSION = "1.0.2"

# Release 标题
RELEASE_TITLE = f"v{VERSION} - 更新说明"

# Release 描述（支持 Markdown）
RELEASE_BODY = f"""## 版本 v{VERSION}

发布时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 更新内容
- 请在此处填写更新内容
- 例如：修复了 XXX 问题
- 例如：新增了 XXX 功能

### 使用说明
1. 下载并解压
2. 双击运行 `启动压枪控制中心v2.bat`
3. 点击「检查更新」可获取后续版本
"""

# GitHub 配置（一般不需要修改）
GITHUB_OWNER = "1784399861"
GITHUB_REPO = "-"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Git 路径
GIT_PATH = r"C:\Program Files\Git\cmd\git.exe"

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ================== 代码区域（一般不需要修改） ==================


def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    print(f"$ {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"命令执行失败: {e}")
        return False


def git_commit_and_push():
    """提交代码并推送到 GitHub"""
    print("\n" + "=" * 60)
    print("步骤 1: 提交并推送代码")
    print("=" * 60)
    
    os.chdir(PROJECT_DIR)
    
    # 检查 git 是否存在
    if not os.path.exists(GIT_PATH):
        print(f"错误: 未找到 git: {GIT_PATH}")
        return False
    
    # 添加所有文件
    if not run_cmd(f'"{GIT_PATH}" add .'):
        return False
    
    # 提交
    commit_msg = f"发布版本 v{VERSION}"
    if not run_cmd(f'"{GIT_PATH}" commit -m "{commit_msg}"'):
        print("注意: 可能没有新的修改需要提交")
    
    # 打 tag
    tag_name = f"v{VERSION}"
    run_cmd(f'"{GIT_PATH}" tag -d {tag_name} 2>nul')  # 删除旧 tag（如果有）
    if not run_cmd(f'"{GIT_PATH}" tag {tag_name}'):
        return False
    
    # 推送代码
    if not run_cmd(f'"{GIT_PATH}" push'):
        return False
    
    # 推送 tag
    if not run_cmd(f'"{GIT_PATH}" push origin {tag_name}'):
        return False
    
    print("\n✅ 代码推送成功！")
    return True


def create_github_release():
    """创建 GitHub Release"""
    print("\n" + "=" * 60)
    print("步骤 2: 创建 GitHub Release")
    print("=" * 60)
    
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "tag_name": f"v{VERSION}",
        "name": RELEASE_TITLE,
        "body": RELEASE_BODY,
        "draft": False,
        "prerelease": False
    }
    
    print(f"正在创建 Release: v{VERSION}")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 201:
            release_info = response.json()
            print(f"✅ Release 创建成功！")
            print(f"Release 地址: {release_info['html_url']}")
            return True
        elif response.status_code == 422:
            print("⚠️  Release 已存在，跳过创建")
            return True
        else:
            print(f"❌ 创建 Release 失败: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def update_version_in_files():
    """更新代码中的版本号"""
    print("\n" + "=" * 60)
    print("步骤 0: 更新代码中的版本号")
    print("=" * 60)
    
    # 更新 src/auto_updater.py
    auto_updater_path = os.path.join(PROJECT_DIR, "src", "auto_updater.py")
    if os.path.exists(auto_updater_path):
        content = open(auto_updater_path, 'r', encoding='utf-8').read()
        old = f'CURRENT_VERSION = "{VERSION}"'
        import re
        content = re.sub(r'CURRENT_VERSION = "[^"]+"', f'CURRENT_VERSION = "{VERSION}"', content)
        open(auto_updater_path, 'w', encoding='utf-8').write(content)
        print(f"✅ 已更新: src/auto_updater.py -> CURRENT_VERSION = {VERSION}")
    
    # 更新 src/recoil_ui_v2.py
    recoil_ui_path = os.path.join(PROJECT_DIR, "src", "recoil_ui_v2.py")
    if os.path.exists(recoil_ui_path):
        content = open(recoil_ui_path, 'r', encoding='utf-8').read()
        import re
        content = re.sub(r'SOFTWARE_VERSION = "[^"]+"', f'SOFTWARE_VERSION = "{VERSION}"', content)
        open(recoil_ui_path, 'w', encoding='utf-8').write(content)
        print(f"✅ 已更新: src/recoil_ui_v2.py -> SOFTWARE_VERSION = {VERSION}")


def main():
    print("=" * 60)
    print("GitHub 发布脚本")
    print("=" * 60)
    print(f"当前版本: v{VERSION}")
    print(f"项目目录: {PROJECT_DIR}")
    
    # 确认
    print("\n请确认配置：")
    print(f"  版本号: v{VERSION}")
    print(f"  Release 标题: {RELEASE_TITLE}")
    print(f"  仓库: {GITHUB_OWNER}/{GITHUB_REPO}")
    
    confirm = input("\n确认发布？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return 1
    
    # 步骤 0: 更新代码中的版本号
    update_version_in_files()
    
    # 步骤 1: 提交并推送代码
    if not git_commit_and_push():
        print("\n❌ 代码推送失败")
        return 1
    
    # 步骤 2: 创建 GitHub Release
    release_url = None
    if not create_github_release():
        print("\n⚠️  Release 创建失败，但代码已推送")
        print("你可以手动在 GitHub 网页创建 Release")
    else:
        release_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/v{VERSION}"
    
    print("\n" + "=" * 60)
    print("✅ 发布完成！")
    print("=" * 60)
    print(f"版本: v{VERSION}")
    print(f"仓库: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}")
    
    if release_url:
        print(f"Release: {release_url}")
        
        # 自动打开浏览器到 Release 页面
        try:
            import webbrowser
            print("\n正在打开浏览器...")
            webbrowser.open(release_url)
        except Exception as e:
            print(f"无法自动打开浏览器: {e}")
            print(f"请手动访问: {release_url}")
    
    print("\n" + "=" * 60)
    print("提示：用户现在可以在软件中点击「检查更新」获取新版本！")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
