# GitHub 上传指南

本文档指导如何将 AntBox 项目上传到 GitHub。

---

## 📋 前置准备

### 1. 创建 GitHub 账号

如果没有 GitHub 账号，访问 https://github.com 注册。

### 2. 配置 Git 用户信息

```bash
# 设置用户名（替换为你的 GitHub 用户名）
git config --global user.name "YourGitHubUsername"

# 设置邮箱（替换为你的 GitHub 邮箱）
git config --global user.email "your-email@example.com"
```

### 3. 生成 SSH 密钥（推荐）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your-email@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 复制公钥内容，添加到 GitHub
# 访问：https://github.com/settings/keys → New SSH key
```

---

## 🚀 上传步骤

### 方式一：使用 SSH（推荐）

#### 步骤 1：在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `antbox-monitor`
   - **Description**: `AntBox 矿机冷却系统监控平台 - 高性能分布式工业级监控系统`
   - **Visibility**: Public（开源）或 Private（私有）
   - **不要勾选** "Add a README file"（我们已有代码）
   - **不要勾选** "Add .gitignore"（我们已有）
   - **不要勾选** "Choose a license"（我们已有 LICENSE）
3. 点击 "Create repository"

#### 步骤 2：关联远程仓库

```bash
# 进入项目目录
cd /root/.openclaw/workspace

# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin git@github.com:YOUR_USERNAME/antbox-monitor.git

# 验证远程仓库
git remote -v
```

#### 步骤 3：推送代码

```bash
# 推送到 GitHub
git push -u origin master

# 如果是主分支叫 main，使用：
# git branch -M main
# git push -u origin main
```

---

### 方式二：使用 HTTPS

#### 步骤 1：在 GitHub 创建仓库

同上。

#### 步骤 2：关联远程仓库

```bash
cd /root/.openclaw/workspace

# 使用 HTTPS 方式（需要输入用户名密码或 Token）
git remote add origin https://github.com/YOUR_USERNAME/antbox-monitor.git
```

#### 步骤 3：推送代码

```bash
git push -u origin master
```

> **注意**：如果使用 HTTPS 且开启了双因素认证（2FA），需要使用 Personal Access Token 代替密码。

---

## 🔑 使用 Personal Access Token（如果开启 2FA）

### 创建 Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 填写描述（如 "antbox-monitor upload"）
4. 选择权限：
   - ✅ `repo` (Full control of private repositories)
5. 点击 "Generate token"
6. **复制 Token**（只显示一次，妥善保存）

### 使用 Token

推送代码时：
- Username: 你的 GitHub 用户名
- Password: 粘贴刚才复制的 Token

或者在 URL 中包含 Token（不推荐，仅用于脚本）：
```bash
git push https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/antbox-monitor.git master
```

---

## ✅ 验证上传

### 1. 在 GitHub 查看

访问 `https://github.com/YOUR_USERNAME/antbox-monitor`，确认文件已上传。

### 2. 检查提交历史

```bash
git log --oneline
```

### 3. 克隆验证（可选）

```bash
# 临时克隆到 /tmp 验证
cd /tmp
git clone git@github.com:YOUR_USERNAME/antbox-monitor.git
cd antbox-monitor
ls -la
```

---

## 🔄 后续更新

### 日常提交流程

```bash
# 1. 修改代码
# ... 编辑文件 ...

# 2. 查看变更
git status
git diff

# 3. 添加变更
git add <文件名>
# 或添加所有变更
git add -A

# 4. 提交
git commit -m "描述你的修改"

# 5. 推送到 GitHub
git push origin master
```

### 查看远程状态

```bash
# 查看远程仓库
git remote -v

# 查看远程分支
git branch -r

# 拉取远程更新
git pull origin master
```

---

## 📝 推荐的项目设置

### 1. 添加项目主题

在 GitHub 仓库页面：
- 点击右上角 "⚙️ Settings"
- 在 "About" 区域添加 topics：
  - `monitoring`
  - `fastapi`
  - `postgresql`
  - `industrial-iot`
  - `mining`
  - `cooling-system`
  - `python`
  - `dashboard`

### 2. 启用 GitHub Pages（可选）

如果想让文档可在线访问：

1. Settings → Pages
2. Source: Deploy from branch
3. Branch: master, Folder: / (root)
4. Save

访问：`https://YOUR_USERNAME.github.io/antbox-monitor/`

### 3. 添加项目徽章

在 README.md 中添加徽章，显示项目状态：

```markdown
![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/antbox-monitor?style=social)
![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/antbox-monitor?style=social)
![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/antbox-monitor)
![GitHub license](https://img.shields.io/github/license/YOUR_USERNAME/antbox-monitor)
```

### 4. 启用 Issues

默认启用，用于接收 Bug 报告和功能请求。

### 5. 添加贡献指南（可选）

创建 `CONTRIBUTING.md` 文件，说明如何贡献代码。

---

## 🛡️ 安全注意事项

### 1. 敏感信息检查

上传前确认没有包含：

- ❌ 数据库密码
- ❌ API 密钥
- ❌ SSH 私钥
- ❌ 服务器 IP（如果是公网）
- ❌ 个人隐私信息

**检查命令**：
```bash
# 搜索可能的敏感信息
grep -r "password" --include="*.py" --include="*.json" .
grep -r "secret" --include="*.py" --include="*.json" .
grep -r "token" --include="*.py" --include="*.json" .
```

### 2. 使用环境变量

建议将敏感配置移到环境变量：

```python
# 不推荐（硬编码）
DB_PASSWORD = "antmonitor2024"

# 推荐（环境变量）
import os
DB_PASSWORD = os.getenv("DB_PASSWORD", "default_password")
```

### 3. 更新 .gitignore

确认 `.gitignore` 已包含敏感文件：

```gitignore
# 敏感信息
.env
*.key
*.pem
secrets.json
credentials.json
config/sites.json  # 如果包含真实 IP
```

---

## 📊 项目统计

上传后可以在 GitHub 查看：

- **Commits**: 提交历史
- **Branches**: 分支
- **Releases**: 版本发布
- **Contributors**: 贡献者
- **Stars**: 星标数
- **Forks**: 派生数

---

## 🎉 完成清单

- [ ] 创建 GitHub 账号
- [ ] 配置 Git 用户信息
- [ ] 生成 SSH 密钥并添加到 GitHub
- [ ] 在 GitHub 创建仓库
- [ ] 关联远程仓库
- [ ] 推送代码到 GitHub
- [ ] 验证上传成功
- [ ] 添加项目主题（topics）
- [ ] 更新 README.md 中的链接
- [ ] 启用 Issues
- [ ] 检查敏感信息

---

## 📞 遇到问题？

### 常见错误及解决方案

**错误 1**: `fatal: remote origin already exists`
```bash
# 删除现有远程，重新添加
git remote remove origin
git remote add origin git@github.com:YOUR_USERNAME/antbox-monitor.git
```

**错误 2**: `Permission denied (publickey)`
```bash
# 检查 SSH 密钥是否添加到 GitHub
ssh -T git@github.com
```

**错误 3**: `failed to push some refs`
```bash
# 先拉取远程更新
git pull origin master --allow-unrelated-histories
git push origin master
```

**错误 4**: `Authentication failed`
```bash
# HTTPS 方式需要使用 Token（如果开启 2FA）
# 或重新配置 SSH 密钥
```

---

## 🔗 相关资源

- [GitHub 文档](https://docs.github.com/)
- [Git 官方文档](https://git-scm.com/doc)
- [SSH 密钥配置指南](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Personal Access Token 指南](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

<div align="center">

**祝上传顺利！** 🚀

如有问题，请联系：Rainbow (彩虹)

</div>
