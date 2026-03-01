# Yamaguchi Platform 子项目与工作流程

本仓库通过 `git subtree` 整合多个子项目。各子项目对应独立 Git 仓库，需分别推送/拉取。

---

## 子项目列表

| 子目录 | 简介 | Git URL | 分支 |
|--------|------|---------|------|
| **ecsite** | 移动端电商网站 (mobile-zone-website) | `git@github.com:zhujiansamuel/mobile-zone-website.git` | main |
| **webapp** | Yamaguchi Web 应用项目 | `git@github.com:zhujiansamuel/YamagotiProjects.git` | master |
| **n8n-auto** | 基于 n8n 的自动化流程 | `git@github.com:zhujiansamuel/n8n-Automation-yamaguchi.git` | main |
| **desktopapp** | iPhone 库存管理系统 | `git@github.com:zhujiansamuel/iPhoneStockManagementSystem.git` | main |
| **dataapp** | 数据整合应用 | `git@github.com:zhujiansamuel/Data-consolidation.git` | master |
| **auto** | Yamaguchi 自动化脚本 | `git@github.com:zhujiansamuel/Automation-yamaguchi.git` | main |
| **dev** | ELK 相关开发 | `git@github.com:zhujiansamuel/ELK.git` | master |
| **dedktoptools** | 重命名工具 UI | `git@github.com:zhujiansamuel/RenameUI.git` | main |

---

## 变更代码后的流程

### 1. 提交到主仓库（本仓库）

在 IDE 或命令行中完成：

```bash
git add .
git commit -m "描述你的修改"
git push origin main   # 或使用 IDE 的 Push 按钮
```

⚠️ **IDE 的 Push 只会推送到本仓库（Yamaguchi-platform）**，不会同步到各子仓库。

### 2. 同步到各子仓库

推送脚本会按 `subtrees.config` 将对应子目录的提交推送到各自的源仓库：

```bash
# 推送到所有子仓库
./push-to-upstream.sh

# 仅推送到指定子仓库（例如 webapp）
./push-to-upstream.sh webapp
```

### 3. 从子仓库拉取更新

当子仓库有其他人提交或你在别处修改过时，拉回本仓库：

```bash
# 从所有子仓库拉取
./pull-from-upstream.sh

# 仅从指定子仓库拉取（例如 dataapp）
./pull-from-upstream.sh dataapp
```

---

## 流程示意

```
修改代码
    │
    ▼
git add + commit + push (主仓库)
    │
    ▼
./push-to-upstream.sh  ←→  各子仓库 (ecsite, webapp, ...)
```

---

## 配置文件

- 子项目映射：项目根目录 `subtrees.config`
- 分支与 URL 变更时，直接编辑该文件即可
