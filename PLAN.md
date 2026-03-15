# FreeCDN 开发计划

> 更新于 2026-03-15 | 基于研究报告结论整合
> 版本基线：GoEdge v1.3.9（已确认安全，不跟踪 v1.4.x 及以上）

---

## 项目定位

基于 GoEdge 社区版（BSD-3-Clause）的 Fork，以 Apache-2.0 发布。目标：让任何人能用一条命令在自己的服务器上搭起完整 CDN，全程无需阅读 GoEdge 技术文档，无计费墙，纯免费开源。

核心差异化：**安全可信**（明确锁定 v1.3.9 安全基线）+ **零门槛安装**（脚本一键 + Docker 一键）+ **中文社区优先**。

---

## 当前服务器

| 角色 | IP | 服务 |
|------|----|------|
| 管理节点 + 边缘节点（合一） | 134.175.67.168 | freecdn-admin、freecdn-node |

管理后台：`http://134.175.67.168:7788`  
MySQL：`freecdn:FreeCDN_Mysql2026!@tcp(127.0.0.1:3306)/freecdn`

---

## 已完成

- [x] GoEdge v1.3.9 成功部署，CDN 转发 200 验证通过
- [x] 排查并修复三个关键技术坑（edge-api 字段名、http JSON 格式、accessAddrs）
- [x] install.sh 骨架（管理节点 + 边缘节点模式）
- [x] fix_api.sh 运维修复脚本（7 步修复流程）
- [x] ssh_install.py 远程安装辅助工具（凭据改为参数/环境变量）
- [x] Docker Compose + Dockerfile 骨架
- [x] 文档体系（ARCHITECTURE.md、INSTALL.md、FAQ.md）
- [x] README.md FreeCDN 化
- [x] GitHub Actions release.yml（push tag v* 自动打包 FreeCDN Release）
- [x] GitHub Actions upstream-check.yml（每周检查 GoEdge 上游新 tag，自动创建审计 Issue）
- [x] P5 品牌替换：JS 文件中 goedge.cloud 链接/示例域名全部替换为 FreeCDN
- [x] GitHub 推送（commit 0f421fbb）
- [x] 完成 GoEdge 全维度研究报告

---

## 开发优先级

### P0 — install.sh 真正可用（最高优先）

**现状**：脚本在 Windows 上写的，从未在干净 Linux 上跑过，存在以下已知风险：
- edgeAPINodes 的 INSERT 已修复（uniqueId、http JSON、accessAddrs）
- 但整个脚本流程（下载二进制、初始化 DB、写配置、注册服务）从未端到端验证过

**目标**：在一台干净 Ubuntu 22.04 服务器上 `curl ... | bash` 一次成功。

**具体工作**：
1. 审查 install.sh 完整流程，修复明显的逻辑问题
2. 特别检查：二进制下载地址（目前从哪里下？GoEdge 官方 Release？）
3. 验证 systemd 服务注册（edge-admin.service、edge-api.service）
4. 验证 edgeAPITokens 表的初始化（admin token 必须正确插入）
5. 验证管理后台登录（edgeAdmins 表需要 MD5 密码的初始账号）
6. 同步验证 `--node` 模式

**验收标准**：curl 安装后，访问 `http://IP:7788` 直接进入管理界面，无需再次配置向导。

---

### P1 — Docker 部署可用

**现状**：docker-compose.yml 和 Dockerfile 骨架存在，但：
- Dockerfile 引用 `COPY goedge/edge-admin/...`，这个目录从哪来？没有构建流程
- docker-entrypoint-admin.sh 没有数据库初始化逻辑（只生成配置文件，不 CREATE TABLE）
- 没有自动注入 nodeId/secret 到数据库的逻辑（容器启动后还需要向导）

**目标**：`docker compose up -d` 后直接能登录，无需向导。

**具体工作**：
1. 明确 Dockerfile 的构建方式（从 GoEdge Release 直接下载二进制，不需要本地编译）
2. docker-entrypoint-admin.sh 增加数据库初始化逻辑（等 MySQL 就绪后自动建表 + 插初始数据）
3. 自动生成并注入 nodeId/secret（与 install.sh 逻辑共用）
4. docker-compose.prod.yml 生产版（不暴露 MySQL 端口，配置持久化卷）
5. 写 deploy/README.md 说明构建和使用方法

---

### P2 — GitHub Actions 自动构建 Release

**现状**：没有真正的 FreeCDN Release，install.sh 下载的其实是 GoEdge 官方二进制（界面显示 GoEdge 字样）。

**目标**：每次打 tag 自动构建 linux/amd64 + linux/arm64 二进制，上传到 GitHub Release。

**具体工作**：
1. 理清编译入口（`cmd/` 目录是什么）
2. 写 `.github/workflows/release.yml`，trigger：push tag v*
3. 构建 edge-admin 和 edge-node（含品牌替换编译标志 `-tags community`）
4. 上传产物：`freecdn-admin-linux-amd64.tar.gz`、`freecdn-admin-linux-arm64.tar.gz`、`freecdn-node-linux-amd64.tar.gz`、`freecdn-node-linux-arm64.tar.gz`
5. install.sh 下载链接指向 FreeCDN 自己的 Release

---

### P3 — 真实 HTTPS 链路验证

**现状**：测试用 IP 直连，无域名，无 HTTPS。

**目标**：完整 HTTPS 全链路（域名 → 边缘节点 → 源站），Let's Encrypt 自动证书。

**具体工作**：
1. 配置一个子域名 DNS 指向 134.175.67.168
2. 在管理后台申请 Let's Encrypt 证书（验证 ACME 流程）
3. 验证 HTTPS 加速转发
4. 把操作步骤补进 docs/INSTALL.md

---

### P4 — 上游安全同步机制

**背景**：GoEdge v1.4.0/v1.4.1 被植入恶意代码，必须严格控制上游同步。

**具体工作**：
1. 写 `.github/workflows/upstream-check.yml`，每周检查上游是否有新 tag
2. 有新 tag 时创建 GitHub Issue（附 changelog diff），人工决策是否合并
3. 不自动 merge，所有上游变更必须人工代码审计后才能进入 freecdn-main

---

### P5 — 品牌定制深化（可选）

参考 GoedgeWorks 的 aiFanCDN 模板，将管理界面的 GoEdge 字样、Logo、版权信息全部替换为 FreeCDN。

**集中改动位置**：
- `web/` 目录：HTML 模板中的系统名称、logo 路径、footer 版权
- `internal/` 中的版本常量（`internal/utils/version.go` 等）
- 策略：改动集中到 `web/public/brand/` 和独立常量文件，避免散布

---

## 技术架构速查

| 参数 | 值 |
|------|-----|
| 版本基线 | GoEdge v1.3.9 |
| Go 最低版本 | 1.21 |
| MySQL | 5.7.8+（推荐 8.0+），只能 TCP 连接 |
| EdgeAdmin 端口 | 7788 |
| EdgeAPI gRPC 端口 | 8003 |
| 上游许可证 | BSD-3-Clause |
| FreeCDN 许可证 | Apache-2.0 |
| 编译标志 | `-tags community`（开源版） |
| 密码存储 | MD5（非 bcrypt） |

**架构关键原则**：EdgeNode 和 EdgeAdmin 均不直连 MySQL，所有数据操作通过 EdgeAPI（gRPC 8003）。

**已知坑（必须记住）**：
- `edgeAPINodes.uniqueId` ≠ `adminNodeId`（旧文档错误，真实字段是 `uniqueId`）
- `edgeAPINodes.http` 的 `listen[0].protocol` 必须是 `"http"`（空字符串 → edge-api 无法启动）
- `edgeAPINodes.accessAddrs` 必须含真实 IP（空数组 `[]` → SyncAPINodesTask nil pointer panic）
- `api_admin.yaml` 必须用嵌套 YAML 格式（`rpc:` / `  endpoints:` / `    - "..."``），点号格式 `rpc.endpoints: [...]` 会导致 edge-admin 解析失败，报 "wrong token role"
- `edgeAPITokens.role=admin` 的 nodeId 必须与 `api_admin.yaml` 中一致
- 管理员密码 MD5 存储，不是 bcrypt
- curl 访问管理后台返回 403（正常），需要浏览器访问

---

## 不做的事

- **计费/套餐系统**：GoEdge 商业版计费模块不做，永远不设付费功能墙
- **Windows 服务端支持**：边缑节点只支持 Linux
- **PostgreSQL/SQLite 支持**：只支持 MySQL（上游限制，不打算改）
- **前端框架升级（近期）**：Vue 2 足够用，不浪费时间升 Vue 3（中期可选）
