# Cangjie Nightly 通过 Scoop 安装（Windows）

本仓库同时作为 Scoop bucket 使用，提供 `cangjie-nightly`（每日构建，基于 main 分支每天构建）。

## 安装

```powershell
# 1. 添加 bucket（只需一次）
scoop bucket add cangjie https://gitcode.com/Cangjie/nightly_build.git

# 2. 安装 nightly（每天基于 main 分支构建）
scoop install cangjie-nightly

# 3. 升级到最新 nightly
scoop update
scoop update cangjie-nightly
```

安装后 `CANGJIE_HOME` 与 PATH 由 Scoop 自动配置（等价于 SDK 自带 `envsetup.ps1`），新开终端生效；可用 `cjc --version`、`cjpm --version` 验证。

## 安装近 30 天内的指定 nightly 版本

> 说明：`scoop search` 仅按**应用名**匹配，且每个应用只显示 manifest 当前指向的最新版本；历史版本不会出现在搜索结果里，请用下方 `@版本号` 方式安装。

nightly 版本仅保留 30 天，30 天内的任意版本都可通过版本号安装（多版本可共存，`scoop reset cangjie-nightly@<版本>` 切换）。**版本号必须为完整 tag、逐字符精确**（如 `1.3.0-alpha.20260901010012`，写错任何一位都会 404）：

```powershell
# 查看最近 30 天的版本列表（[0] 最新，[1] 前一天…）
# 注意：GitCode releases API 默认按时间升序，必须带 &direction=desc
(Invoke-RestMethod 'https://gitcode.com/api/v5/repos/Cangjie/nightly_build/releases?per_page=30&direction=desc').tag_name

# 安装前一天版本
$v = (Invoke-RestMethod 'https://gitcode.com/api/v5/repos/Cangjie/nightly_build/releases?per_page=2&direction=desc')[1].tag_name
scoop install "cangjie-nightly@$v"
```

> 注意：超过 30 天的版本已被归档，下载地址失效（404）。

## 维护（发布流水线）

每日 nightly 发布后，发布流水线执行 `tools/update_manifest.py`（纯 python3）回写 `bucket/cangjie-nightly.json` 的版本/hash/URL。
