# GitHub 项目上传操作说明

本文档整理了将本地项目上传到 GitHub 的标准操作步骤，方便后续参考。

---

## 前提条件

| 项目 | 说明 |
|------|------|
| Git 已安装 | 通过 `winget install Git.Git` 安装 |
| GitHub 账号 | 已注册完成 |
| Personal Access Token (PAT) | 在 `https://github.com/settings/tokens` 生成 classic token，勾选 `public_repo` 权限 |

---

## 完整上传步骤（PowerShell）

```powershell
# 1. 进入项目目录
cd "C:\Users\XOS\Desktop\你的项目目录"

# 2. 初始化 Git 仓库（如果还没有）
"C:\Program Files\Git\cmd\git.exe" init

# 3. 添加远程仓库（替换为你的用户名、仓库名、token）
$token = "你的token这里"
$username = "你的GitHub用户名"
$repo = "仓库名称"
"C:\Program Files\Git\cmd\git.exe" remote set-url origin "https://$token@github.com/$username/$repo.git"

# 4. 如果远程已有初始化文件（README/.gitignore/LICENSE），先拉取合并
"C:\Program Files\Git\cmd\git.exe" pull origin main --allow-unrelated-histories

# 5. 添加所有本地文件
"C:\Program Files\Git\cmd\git.exe" add .

# 6. 提交
"C:\Program Files\Git\cmd\git.exe" commit -m "Initial commit"

# 7. 推送到 GitHub
"C:\Program Files\Git\cmd\git.exe" push -u origin main
```

---

## 后续更新步骤（修改代码后）

```powershell
# 1. 进入项目目录
cd "C:\Users\XOS\Desktop\压枪软件"

# 2. 添加修改的文件
"C:\Program Files\Git\cmd\git.exe" add .

# 3. 提交（填写修改说明）
"C:\Program Files\Git\cmd\git.exe" commit -m "描述你做了什么修改"

# 4. 推送到 GitHub
"C:\Program Files\Git\cmd\git.exe" push
```

---

## 常见问题

### 1. 远程 origin 已存在
```
error: remote origin already exists.
```
**解决**：跳过 `remote add origin`，直接使用 `remote set-url origin` 更新地址即可。

### 2. 网络连接超时
```
fatal: unable to access '...': Failed to connect to github.com port 443 after ... ms
```
**解决**：等待几秒后重试一次 `push` 命令即可。

### 3. 推送冲突
**解决**：先执行 `git pull origin main` 拉取合并，解决冲突后再推送。

### 4. 权限错误 403
**解决**：检查 Token 是否正确，是否勾选了 `public_repo` 权限。

---

## 路径说明

- Git 默认安装路径：`C:\Program Files\Git\cmd\git.exe`
- 使用完整路径避免环境变量未刷新问题
- Token 已经包含在远程 URL 中，无需额外配置用户名密码

---

## 本项目当前配置

| 配置项 | 值 |
|--------|-----|
| GitHub 用户名 | `1784399861` |
| 仓库名称 | `-` |
| 仓库地址 | https://github.com/1784399861/- |
| 本地项目路径 | `C:\Users\XOS\Desktop\压枪软件` |
