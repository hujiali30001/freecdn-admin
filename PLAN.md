# FreeCDN 项目计划

> 当前状态（2026-03-15）：CDN 核心功能运行正常，GitHub 已推送，一键安装脚本已写完但未实测。

---

## 项目定位

基于 GoEdge 社区版的 Fork，做品牌化、简化和完善，目标是让任何人都能用一条命令搭起自己的 CDN 系统，而不需要读懂 GoEdge 的技术文档。

---

## 已完成

- GoEdge 品牌替换（UI 字样、文档）
- 管理节点 + 边缘节点联调打通，CDN 转发验证 200
- 踩坑并记录三个关键坑（edge-api.service 冲突、nodeId 格式、originType=primary）
- 一键安装脚本骨架（install.sh、install-node.sh）
- 文档体系（ARCHITECTURE.md、INSTALL.md、FAQ.md）
- GitHub 推送完成

---

## 下一步（按优先级排序）

### P0 — 让安装脚本真正可用

**问题**：install.sh 是在 Windows 上写的，从未在干净 Linux 服务器上跑过，大概率有路径、权限、变量问题。

**做法**：
1. 用一台干净的 Ubuntu 22.04 服务器（可以是腾讯云按量付费，用完销毁）跑一遍 `curl ... | bash`
2. 记录每一个失败点，修到成功
3. 同样验证 node 模式（`bash install.sh --node ...`）
4. 把验证过程更新进 FAQ.md

这是整个项目价值的核心，没有一个真正能跑的安装脚本，其他都是空谈。

---

### P1 — README 改成 FreeCDN 的脸

**问题**：现在 README.md 还是 GoEdge 原版内容，访客一进仓库看到的是"GoEdge目标"，完全没有 FreeCDN 的自我介绍。

**做法**：重写 README，包含：
- 一句话介绍 + 截图
- 快速开始（三步命令）
- 功能列表
- 和 GoEdge 的关系说明
- License

---

### P2 — 接真实域名，走完整 HTTPS 流程

**问题**：现在测试用的是 `nip.io` 这种临时域名，没有 HTTPS，无法给真实用户用。

**做法**：
1. 把一个真实域名（哪怕是子域名）的 DNS 指向边缘节点 IP
2. 在管理台申请 Let's Encrypt 证书
3. 验证 HTTPS 加速全链路工作正常
4. 把操作步骤补进 INSTALL.md

---

### P3 — Docker Compose 部署验证

**问题**：`deploy/docker-compose.yml` 存在，但从未验证过能不能用。INSTALL.md 把它写成"推荐方案"，但可能压根跑不起来。

**做法**：在一台干净服务器上跑 docker compose 方案，修到能用，或者如果太麻烦就把 INSTALL.md 里的推荐顺序调整为"脚本优先"。

---

### P4 — GitHub Actions 自动构建

**问题**：仓库里有 `.github/workflows/build.yml`，但 FreeCDN 目前没有自己发布 Release，安装脚本下载的其实是 GoEdge 的官方二进制，界面上还会显示 GoEdge 字样。

**做法**：
1. 把 build workflow 跑通，能成功编译并上传 Release 产物
2. 这样 install.sh 才能真正下载 FreeCDN 品牌的二进制
3. 不急，等 P0 和 P1 完成后再做

---

### P5 — 上游同步机制

**问题**：GoEdge 上游还在持续更新，现在靠手动 merge，容易滞后或出冲突。

**做法**：写一个 GitHub Actions workflow，定期（比如每月一次）自动检测上游是否有新 tag，如果有就创建一个 PR，人工确认后合并。不需要完全自动化，有 PR 提醒就够了。

---

## 不做的事

- **计费系统**：GoEdge 商业版的多租户计费不做，FreeCDN 定位是个人/团队自建，不是 SaaS
- **控制面板 UI 大改**：GoEdge 的 UI 足够用，不重写前端
- **支持 Windows 服务器**：边缘节点只支持 Linux

---

## 当前服务器信息

| 角色 | IP | 服务 |
|------|----|------|
| 管理节点 + 边缘节点（合一） | 134.175.67.168 | freecdn-admin、freecdn-node |

MySQL DSN：`freecdn:FreeCDN_Mysql2026!@tcp(127.0.0.1:3306)/freecdn`  
管理后台：`http://134.175.67.168:7788`
