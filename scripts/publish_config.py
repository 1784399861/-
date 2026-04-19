#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武器数据（config）推送脚本
将 config/ 目录打包上传到 GitHub Release，供用户端「同步武器配置」使用

使用方式：
  1. 修改下方 DATA_VERSION 为新版本号
  2. 运行脚本：python scripts/publish_config.py
  3. 确认后自动打包 → 创建 Release → 上传 zip
"""

import os
import sys
import json
import shutil
import tempfile
import zipfile
import requests
from datetime import datetime

# ================== 配置区域（请修改这里） ==================

# 武器数据版本号（每次发布前修改这里）
DATA_VERSION = "1.0.1"

# Release 描述（支持 Markdown）
RELEASE_BODY = f"""## 武器数据 v{DATA_VERSION}

更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 更新内容
- 请在此处填写武器数据更新内容
- 例如：新增 XXX 武器压枪数据
- 例如：修正 XXX 武器参数

### 使用说明
在软件中点击「同步武器配置」即可获取最新数据
"""

# GitHub 配置
GITHUB_OWNER = "1784399861"
GITHUB_REPO = "-"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ================== 代码区域 ==================


def update_data_version():
    """更新 config/data_version.json"""
    version_path = os.path.join(PROJECT_DIR, "config", "data_version.json")
    data = {
        "version": DATA_VERSION,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已更新 config/data_version.json -> v{DATA_VERSION}")


def pack_config():
    """将 config/ 目录打包为 zip"""
    config_dir = os.path.join(PROJECT_DIR, "config")
    if not os.path.exists(config_dir):
        print(f"❌ config 目录不存在: {config_dir}")
        return None

    zip_filename = f"weapon_data_v{DATA_VERSION}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

    # 如果已有旧 zip 则删除
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"正在打包 config/ -> {zip_filename} ...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(config_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # zip 内路径：以 config/ 开头
                arcname = os.path.relpath(file_path, PROJECT_DIR)
                zf.write(file_path, arcname)

    # 统计
    file_count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        file_count = len(zf.namelist())

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✅ 打包完成: {file_count} 个文件, {size_mb:.2f} MB")
    print(f"   路径: {zip_path}")
    return zip_path


def create_release_and_upload(zip_path):
    """创建 GitHub Release 并上传 zip 资产"""
    api_base = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    tag_name = f"v{DATA_VERSION}"

    # 1. 创建 Release
    print(f"\n正在创建 Release: {tag_name} ...")
    release_url = f"{api_base}/releases"
    release_data = {
        "tag_name": tag_name,
        "name": f"武器数据 v{DATA_VERSION}",
        "body": RELEASE_BODY,
        "draft": False,
        "prerelease": False
    }

    try:
        resp = requests.post(release_url, headers=headers, json=release_data, timeout=30)
        if resp.status_code == 201:
            release_info = resp.json()
            upload_url = release_info["upload_url"].split("{")[0]  # 去掉模板参数
            release_html = release_info["html_url"]
            print(f"✅ Release 创建成功: {release_html}")
        elif resp.status_code == 422:
            # Release 已存在，获取已有 Release 信息
            print("⚠️  Release 已存在，获取已有 Release ...")
            get_resp = requests.get(f"{api_base}/releases/tags/{tag_name}", headers=headers, timeout=10)
            if get_resp.status_code == 200:
                release_info = get_resp.json()
                upload_url = release_info["upload_url"].split("{")[0]
                release_html = release_info["html_url"]
                # 删除已有的同名资产
                existing_assets = release_info.get("assets", [])
                for asset in existing_assets:
                    if asset["name"] == os.path.basename(zip_path):
                        print(f"   删除旧资产: {asset['name']}")
                        requests.delete(asset["url"], headers=headers, timeout=10)
            else:
                print(f"❌ 获取已有 Release 失败: {get_resp.status_code}")
                return None
        else:
            print(f"❌ 创建 Release 失败: {resp.status_code}")
            print(resp.text)
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

    # 2. 上传 zip 资产
    print(f"\n正在上传: {os.path.basename(zip_path)} ...")
    asset_name = os.path.basename(zip_path)
    upload_headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/zip"
    }

    try:
        with open(zip_path, "rb") as f:
            upload_resp = requests.post(
                f"{upload_url}?name={asset_name}",
                headers=upload_headers,
                data=f,
                timeout=120
            )

        if upload_resp.status_code == 201:
            print(f"✅ 上传成功!")
        else:
            print(f"❌ 上传失败: {upload_resp.status_code}")
            print(upload_resp.text)
            return None
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return None

    # 清理临时 zip
    try:
        os.remove(zip_path)
        print("已清理临时文件")
    except Exception:
        pass

    return release_html


def main():
    print("=" * 60)
    print("武器数据推送脚本")
    print("=" * 60)
    print(f"数据版本: v{DATA_VERSION}")
    print(f"项目目录: {PROJECT_DIR}")
    print(f"仓库: {GITHUB_OWNER}/{GITHUB_REPO}")

    if not GITHUB_TOKEN:
        print("\n❌ 未设置 GITHUB_TOKEN 环境变量！")
        print("请先设置：")
        print("  PowerShell: $env:GITHUB_TOKEN = \"你的token\"")
        print("  CMD: set GITHUB_TOKEN=你的token")
        return 1

    # 确认
    print(f"\n将要执行：")
    print(f"  1. 更新 config/data_version.json -> v{DATA_VERSION}")
    print(f"  2. 打包 config/ 目录")
    print(f"  3. 创建 GitHub Release 并上传")

    confirm = input("\n确认推送？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消")
        return 0

    # 步骤 1: 更新版本号
    update_data_version()

    # 步骤 2: 打包
    zip_path = pack_config()
    if not zip_path:
        return 1

    # 步骤 3: 创建 Release 并上传
    release_url = create_release_and_upload(zip_path)

    if release_url:
        print("\n" + "=" * 60)
        print("✅ 武器数据推送完成！")
        print("=" * 60)
        print(f"版本: v{DATA_VERSION}")
        print(f"Release: {release_url}")

        # 打开浏览器
        try:
            import webbrowser
            webbrowser.open(release_url)
        except Exception:
            pass

        print("\n用户现在可以在软件中点击「同步武器配置」获取最新数据！")
    else:
        print("\n❌ 推送失败，请检查错误信息")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
