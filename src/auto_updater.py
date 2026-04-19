#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武器数据同步模块
通过 GitHub Releases 同步 config/ 文件夹内的武器配置数据
"""

import sys
import os
import json
import requests
import zipfile
import tempfile
import shutil
from packaging import version as pkg_version
from typing import Optional, Dict, Any, Tuple

# GitHub 仓库信息
GITHUB_OWNER = "1784399861"
GITHUB_REPO = "-"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 数据版本文件名
DATA_VERSION_FILE = "data_version.json"


def get_app_dir() -> str:
    """获取应用目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        src_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(src_dir)


def get_config_dir() -> str:
    """获取 config 目录路径"""
    return os.path.join(get_app_dir(), "config")


def get_local_data_version() -> str:
    """读取本地数据版本号，无则返回 '0.0.0'"""
    version_path = os.path.join(get_config_dir(), DATA_VERSION_FILE)
    try:
        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"


def set_local_data_version(ver: str):
    """写入本地数据版本号"""
    version_path = os.path.join(get_config_dir(), DATA_VERSION_FILE)
    try:
        data = {}
        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["version"] = ver
        data["update_time"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写入数据版本失败: {e}")


class ConfigSyncer:
    """武器配置数据同步器 — 只同步 config/ 目录"""

    def __init__(self, owner: str = None, repo: str = None, token: str = None):
        self.owner = owner or GITHUB_OWNER
        self.repo = repo or GITHUB_REPO
        self.token = token or GITHUB_TOKEN
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        self.session.headers["User-Agent"] = f"{self.repo}-ConfigSyncer"

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

    def check_update(self) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """检查配置数据是否有更新

        Returns:
            (是否有更新, 最新版本号, Release 信息)
        """
        latest = self.get_latest_release()
        if not latest:
            return False, None, None

        latest_tag = latest.get("tag_name", "").lstrip("v")
        local_ver = get_local_data_version()

        try:
            has_update = pkg_version.parse(latest_tag) > pkg_version.parse(local_ver)
            return has_update, latest_tag, latest
        except Exception as e:
            print(f"版本比较失败: {e}")
            return False, latest_tag, latest

    def find_config_asset(self, release: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """在 Release 资产中查找配置数据 zip

        优先匹配名称含 config/weapon/data 的 zip 文件，
        兜底取第一个 zip。
        """
        assets = release.get("assets", [])
        if not assets:
            return None

        # 优先匹配
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".zip") and any(kw in name for kw in ("config", "weapon", "data")):
                return asset

        # 兜底：第一个 zip
        for asset in assets:
            if asset.get("name", "").lower().endswith(".zip"):
                return asset

        return None

    def sync_config(self, release: Dict[str, Any], on_progress=None) -> Tuple[bool, str]:
        """同步配置数据：下载 zip → 备份 config → 解压替换 → 写入版本号

        Args:
            release: GitHub Release 信息
            on_progress: 进度回调 callable(msg: str)

        Returns:
            (是否成功, 消息)
        """
        def _log(msg):
            print(msg)
            if on_progress:
                on_progress(msg)

        # 1. 查找资产
        asset = self.find_config_asset(release)
        if not asset:
            return False, "Release 中未找到配置数据文件"

        download_url = asset.get("browser_download_url")
        asset_name = asset.get("name", "config.zip")
        if not download_url:
            return False, "未找到下载地址"

        # 2. 下载
        _log(f"正在下载: {asset_name}")
        try:
            response = self.session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            zip_path = os.path.join(tempfile.gettempdir(), asset_name)
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = (downloaded / total_size) * 100
                            _log(f"下载进度: {pct:.0f}%")

            _log("下载完成")
        except Exception as e:
            return False, f"下载失败: {e}"

        # 3. 备份当前 config
        config_dir = get_config_dir()
        backup_dir = f"{config_dir}.backup"
        if os.path.exists(backup_dir):
            try:
                shutil.rmtree(backup_dir)
            except Exception:
                pass

        if os.path.exists(config_dir):
            try:
                shutil.copytree(config_dir, backup_dir)
                _log(f"已备份配置到: {backup_dir}")
            except Exception as e:
                _log(f"备份警告: {e}")
        else:
            os.makedirs(config_dir, exist_ok=True)

        # 4. 解压并替换 config 内文件
        _log("正在解压并更新配置...")
        extract_dir = tempfile.mkdtemp(prefix="config_sync_")
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            # 智能合并：如果 zip 内有 config/ 子目录，取其内容；否则直接取内容
            src_dir = extract_dir
            inner_config = os.path.join(extract_dir, "config")
            if os.path.isdir(inner_config):
                src_dir = inner_config

            # 复制文件到 config 目录（覆盖同名文件，保留本地独有文件）
            file_count = 0
            for item in os.listdir(src_dir):
                src = os.path.join(src_dir, item)
                dst = os.path.join(config_dir, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    file_count += 1
                elif os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    file_count += 1

            _log(f"配置更新完成，更新了 {file_count} 个文件/目录")

        except Exception as e:
            # 尝试恢复备份
            if os.path.exists(backup_dir):
                try:
                    shutil.rmtree(config_dir)
                    shutil.copytree(backup_dir, config_dir)
                    _log("已恢复备份")
                except Exception:
                    pass
            return False, f"解压/替换失败: {e}"
        finally:
            # 清理临时文件
            try:
                os.remove(zip_path)
                shutil.rmtree(extract_dir)
            except Exception:
                pass
            # 清理备份
            try:
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
            except Exception:
                pass

        # 5. 写入版本号
        new_version = release.get("tag_name", "").lstrip("v")
        set_local_data_version(new_version)
        _log(f"数据版本已更新至: v{new_version}")

        return True, f"武器数据已同步至 v{new_version}"


def check_for_config_update(owner: str = None, repo: str = None,
                             token: str = None) -> Dict[str, Any]:
    """检查配置数据更新的便捷函数

    Returns:
        {
            "has_update": bool,
            "local_version": str,
            "latest_version": str,
            "release": dict,
            "error": str (optional)
        }
    """
    result = {
        "has_update": False,
        "local_version": get_local_data_version(),
        "latest_version": None,
        "release": None,
        "error": None
    }

    try:
        syncer = ConfigSyncer(owner, repo, token)
        has_update, latest_ver, release = syncer.check_update()
        result["has_update"] = has_update
        result["latest_version"] = latest_ver
        result["release"] = release
    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    # 测试
    print(f"本地数据版本: v{get_local_data_version()}")

    syncer = ConfigSyncer()
    has_update, latest_ver, release = syncer.check_update()

    if has_update:
        print(f"发现新数据版本: v{latest_ver}")
        print(f"发布说明:\n{release.get('body', '')}")
    else:
        print("武器数据已是最新")
