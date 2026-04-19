#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新模块
通过 GitHub Releases 实现软件自动更新
"""

import sys
import os
import json
import requests
import zipfile
import tempfile
import shutil
import subprocess
from packaging import version as pkg_version
from typing import Optional, Dict, Any, Tuple

# 当前软件版本（打包时会被替换）
CURRENT_VERSION = "1.0.2"

# GitHub 仓库信息
GITHUB_OWNER = "1784399861"
GITHUB_REPO = "-"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get_app_dir() -> str:
    """获取应用目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # 开发模式：__file__ 在 src/ 下，项目根目录是上一级
        src_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(src_dir)


class AutoUpdater:
    def __init__(self, owner: str = None, repo: str = None, token: str = None):
        self.owner = owner or GITHUB_OWNER
        self.repo = repo or GITHUB_REPO
        self.token = token or GITHUB_TOKEN
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        self.session.headers["User-Agent"] = f"{self.repo}-AutoUpdater"

    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """发起 GitHub API 请求"""
        url = f"{self.api_base}{endpoint}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """获取最新 Release 信息"""
        endpoint = f"/repos/{self.owner}/{self.repo}/releases/latest"
        return self._make_request(endpoint)

    def get_all_releases(self) -> Optional[list]:
        """获取所有 Release 列表"""
        endpoint = f"/repos/{self.owner}/{self.repo}/releases"
        return self._make_request(endpoint)

    def check_update(self, current_version: str = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """检查是否有更新

        Returns:
            (是否有更新, 最新 Release 信息)
        """
        current = current_version or CURRENT_VERSION
        latest = self.get_latest_release()

        if not latest:
            return False, None

        latest_tag = latest.get("tag_name", "").lstrip("v")
        try:
            has_update = pkg_version.parse(latest_tag) > pkg_version.parse(current)
            return has_update, latest
        except Exception as e:
            print(f"版本比较失败: {e}")
            return False, latest

    def find_asset(self, release: Dict[str, Any], asset_name: str = None) -> Optional[Dict[str, Any]]:
        """查找 Release 中的资产文件

        Args:
            release: Release 信息
            asset_name: 资产文件名（支持模糊匹配）

        Returns:
            匹配的资产信息
        """
        assets = release.get("assets", [])
        if not assets:
            return None

        if not asset_name:
            # 默认找 exe 或 zip
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe") or name.endswith(".zip"):
                    return asset
            return assets[0] if assets else None

        # 模糊匹配
        for asset in assets:
            if asset_name in asset.get("name", ""):
                return asset
        return None

    def download_asset(self, asset: Dict[str, Any], save_path: str = None) -> Optional[str]:
        """下载资产文件

        Args:
            asset: 资产信息
            save_path: 保存路径（None则保存到临时目录）

        Returns:
            下载后的文件路径
        """
        if not save_path:
            save_dir = tempfile.gettempdir()
            save_path = os.path.join(save_dir, asset.get("name", "update.zip"))

        download_url = asset.get("browser_download_url")
        if not download_url:
            print("未找到下载地址")
            return None

        print(f"正在下载: {download_url}")
        try:
            response = self.session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}%", end="", flush=True)

            print("\n下载完成")
            return save_path
        except Exception as e:
            print(f"\n下载失败: {e}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return None

    def extract_zip(self, zip_path: str, extract_to: str = None) -> Optional[str]:
        """解压 ZIP 文件"""
        if not extract_to:
            extract_to = tempfile.mkdtemp(prefix="update_")

        print(f"正在解压到: {extract_to}")
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
            return extract_to
        except Exception as e:
            print(f"解压失败: {e}")
            return None

    def perform_update(self, release: Dict[str, Any], asset_name: str = None,
                      backup: bool = True) -> bool:
        """执行更新

        Args:
            release: Release 信息
            asset_name: 资产文件名
            backup: 是否备份当前版本

        Returns:
            是否成功
        """
        # 1. 查找资产
        asset = self.find_asset(release, asset_name)
        if not asset:
            print("未找到更新文件")
            return False

        # 2. 下载
        zip_path = self.download_asset(asset)
        if not zip_path:
            return False

        # 3. 解压
        extract_dir = self.extract_zip(zip_path)
        if not extract_dir:
            return False

        # 4. 备份当前版本
        app_dir = get_app_dir()
        backup_dir = None
        if backup:
            backup_dir = f"{app_dir}.backup"
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            try:
                shutil.copytree(app_dir, backup_dir)
                print(f"已备份到: {backup_dir}")
            except Exception as e:
                print(f"备份失败: {e}")
                backup_dir = None

        # 5. 替换文件
        print(f"正在更新: {app_dir}")
        try:
            # 复制解压后的文件到应用目录
            for item in os.listdir(extract_dir):
                src = os.path.join(extract_dir, item)
                dst = os.path.join(app_dir, item)

                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)

            # 清理
            os.remove(zip_path)
            shutil.rmtree(extract_dir)

            print("更新完成！请重启程序")
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            # 尝试恢复备份
            if backup_dir and os.path.exists(backup_dir):
                print("正在恢复备份...")
                try:
                    shutil.rmtree(app_dir)
                    shutil.copytree(backup_dir, app_dir)
                    shutil.rmtree(backup_dir)
                    print("备份已恢复")
                except Exception as e2:
                    print(f"备份恢复失败: {e2}")
            return False

    def launch_updater_script(self, release: Dict[str, Any], asset_name: str = None) -> bool:
        """启动独立的更新脚本（避免正在运行的文件被占用）

        创建一个临时的更新脚本，然后启动它来完成更新
        """
        app_dir = get_app_dir()
        asset = self.find_asset(release, asset_name)
        if not asset:
            return False

        # 创建更新脚本
        updater_script = os.path.join(tempfile.gettempdir(), f"update_{self.repo}.py")

        script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
import requests
import zipfile
import shutil

# 等待主程序退出
print("等待程序退出...")
time.sleep(2)

# 配置
APP_DIR = r"{app_dir}"
DOWNLOAD_URL = r"{asset.get('browser_download_url', '')}"
ASSET_NAME = r"{asset.get('name', '')}"
BACKUP_DIR = r"{app_dir}.backup"

print("开始更新...")
print(f"应用目录: {{APP_DIR}}")
print(f"下载地址: {{DOWNLOAD_URL}}")

# 1. 下载
zip_path = os.path.join(os.environ.get('TEMP', '.'), ASSET_NAME)
print(f"下载到: {{zip_path}}")

try:
    response = requests.get(DOWNLOAD_URL, stream=True, timeout=60)
    response.raise_for_status()
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print("下载完成")
except Exception as e:
    print(f"下载失败: {{e}}")
    input("按回车退出...")
    sys.exit(1)

# 2. 备份
if os.path.exists(BACKUP_DIR):
    shutil.rmtree(BACKUP_DIR)
try:
    shutil.copytree(APP_DIR, BACKUP_DIR)
    print(f"已备份到: {{BACKUP_DIR}}")
except Exception as e:
    print(f"备份警告: {{e}}")

# 3. 解压
extract_dir = os.path.join(os.environ.get('TEMP', '.'), 'update_extract')
if os.path.exists(extract_dir):
    shutil.rmtree(extract_dir)

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print("解压完成")
except Exception as e:
    print(f"解压失败: {{e}}")
    input("按回车退出...")
    sys.exit(1)

# 4. 替换文件
print("正在替换文件...")
try:
    for item in os.listdir(extract_dir):
        src = os.path.join(extract_dir, item)
        dst = os.path.join(APP_DIR, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    print("文件替换完成")
except Exception as e:
    print(f"替换失败: {{e}}")
    input("按回车退出...")
    sys.exit(1)

# 5. 清理
try:
    os.remove(zip_path)
    shutil.rmtree(extract_dir)
except:
    pass

print("\\n更新完成！")
print(f"备份在: {{BACKUP_DIR}}")
print("正在启动程序...")

# 启动主程序
exe_name = "游戏工具中心.exe"
exe_path = os.path.join(APP_DIR, exe_name)
if os.path.exists(exe_path):
    os.startfile(exe_path)
else:
    print(f"未找到: {{exe_path}}")
    input("按回车退出...")

sys.exit(0)
'''

        try:
            with open(updater_script, "w", encoding="utf-8") as f:
                f.write(script_content)

            # 启动更新脚本
            print(f"启动更新脚本: {updater_script}")
            subprocess.Popen([sys.executable, updater_script],
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
            return True
        except Exception as e:
            print(f"启动更新脚本失败: {e}")
            return False


# 便捷函数
def check_for_updates(owner: str = None, repo: str = None,
                     token: str = None, current_version: str = None) -> Dict[str, Any]:
    """检查更新的便捷函数

    Returns:
        {
            "has_update": bool,
            "current_version": str,
            "latest_version": str,
            "release": dict,
            "error": str (optional)
        }
    """
    result = {
        "has_update": False,
        "current_version": current_version or CURRENT_VERSION,
        "latest_version": None,
        "release": None,
        "error": None
    }

    try:
        updater = AutoUpdater(owner, repo, token)
        has_update, release = updater.check_update(current_version)

        result["has_update"] = has_update
        result["release"] = release

        if release:
            result["latest_version"] = release.get("tag_name", "").lstrip("v")

    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    # 测试
    print(f"当前版本: {CURRENT_VERSION}")

    updater = AutoUpdater()
    has_update, release = updater.check_update()

    if has_update:
        print(f"发现新版本: {release.get('tag_name')}")
        print(f"发布说明:\n{release.get('body', '')}")
    else:
        print("已是最新版本")
