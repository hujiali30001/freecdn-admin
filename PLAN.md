# FreeCDN 开发计划

> 更新于 2026-03-16 | 当前版本 v0.1.7 | P0~P5 全部完成

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

## 版本发布历史

| 版本 | 标签时间 | GitHub Release 产物 | 说明 |
|------|----------|---------------------|------|
| v0.1.0 | 2026-03-15 | 无 Release 产物 | v0.1.0 release prep，确立目录结构和安装脚本基础 |
| v0.1.1 | 2026-03-16 | 无 Release 产物 | release.yml 修复 web/ overlay 覆盖 |
| v0.1.2 | 2026-03-15 | amd64/arm64 tar.gz ✓ | GoEdge v1.3.9 商业版残留清理 |
| v0.1.3 | 2026-03-15 | 无 Release 产物 | 品牌替换（settings 商业版菜单清理）|
| v0.1.4 | 2026-03-15 | 无 Release 产物 | 首个从源码编译的版本，脱离 GoEdge 上游二进制 |
| v0.1.5 | 2026-03-15 | 无 Release 产物 | 编译流程完善，EdgeCommon 依赖指向自有仓库 |
| v0.1.6 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | Docker 完整初始化、install.sh 品牌 SQL 修复 |
| v0.1.7 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 版本号统一至 v0.1.7，PLAN.md 精确同步，服务器验证通过 |

**当前 install.sh 默认版本**：`FREECDN_VERSION="v0.1.7"`  
**下载地址**：`https://github.com/hujiali30001/freecdn-admin/releases/download/v0.1.7/freecdn-v0.1.7-linux-{arch}.tar.gz`

> v0.1.6 Release 包是从 **源码自主编译**（local_build_release.py），包含 edge-admin / edge-api / edge-node 三个组件，不再依赖 GoEdge 官方二进制。

---

## 已完成

- [x] GoEdge v1.3.9 成功部署，CDN 转发 200 验证通过
- [x] 排查并修复三个关键技术坑（edge-api 字段名、http JSON 格式、accessAddrs）
- [x] install.sh 完整实现（管理节点 + 边缘节点模式，非交互参数支持）
- [x] fix_api.sh 运维修复脚本（7 步修复流程）
- [x] ssh_install.py 远程安装辅助工具
- [x] **P0 验收通过**：干净 Ubuntu 22.04 端到端跑通 install.sh，品牌 SQL 写入正确，HTTP 200，admin 账号可登录（v0.1.6）
- [x] Docker Compose + Dockerfile 完整实现（含数据库自动初始化、配置持久化）
- [x] **P1 验收通过**：docker compose up -d 跑通，容器启动正常，管理后台可访问（v0.1.6）
- [x] **P2 完成**：local_build_release.py 从三个自有仓库源码编译 amd64/arm64，手动上传到 GitHub Release（因 Actions 账单问题，CI 不可用）
  - release.yml 存在但账单冻结无法触发，实际通过 local_build_release.py 本地构建
  - v0.1.6 Release 已发布，含 amd64/arm64 tar.gz + SHA256SUMS
- [x] **P4 完成**：upstream-check.yml（每周检查 GoEdge 上游 tag，自动创建审计 Issue）
- [x] **P5 完成**：品牌替换全覆盖
  - JS 文件 goedge.cloud 链接/示例域名替换
  - 所有商业版授权/套餐/计费模块移除
  - settings 商业版菜单项清理
  - ip-library HTML 模板品牌替换
  - web footer、集群节点安装页等静态 HTML 替换
- [x] 文档体系（ARCHITECTURE.md、docs/INSTALL.md、docs/FAQ.md）
- [x] README.md FreeCDN 化
- [x] 完成 GoEdge 全维度研究报告

---

## 当前状态（v0.1.7，main 分支干净）

v0.1.7 于 2026-03-16 发布，包含所有今天的修复（install.sh 品牌 SQL、Docker 完整初始化等）。main 分支目前无未发布提交。

**Release 产物：**
- `freecdn-v0.1.7-linux-amd64.tar.gz`（42.9 MB，amd64 源码编译）
- `freecdn-v0.1.7-linux-arm64.tar.gz`（40.6 MB，arm64 交叉编译）
- `SHA256SUMS`

**服务器验证结果（134.175.67.168）：**
- install.sh 默认版本 v0.1.7 ✓
- tar.gz 可从 ghfast.top 镜像站下载 ✓
- edge-admin ELF 64-bit 静态链接二进制 ✓
- VERSION 文件含正确版本号和构建时间 ✓
- freecdn-admin / freecdn-api 服务均 active ✓

---

## 下一步（待规划）

### 近期优先：P3 — 真实 HTTPS 链路验证

**现状**：测试用 IP 直连，无域名，无 HTTPS。

**目标**：完整 HTTPS 全链路（域名 → 边缘节点 → 源站），Let's Encrypt 自动证书。

**具体工作**：
1. 配置一个子域名 DNS 指向 134.175.67.168
2. 在管理后台申请 Let's Encrypt 证书（验证 ACME 流程）
3. 验证 HTTPS 加速转发
4. 把操作步骤补进 docs/INSTALL.md

### 中期：install-node.sh 验证

**现状**：install-node.sh（边缘节点安装脚本）从未在真实 Linux 上端到端跑过。

**目标**：在第二台服务器（或同台服务器另一个端口）验证边缘节点接入流程，走通「管理后台添加节点 → install-node.sh 一键安装 → 节点在线」全链路。

### 中期：社区运营

- README 补充"为什么不用 GoEdge 官方版本"说明（v1.4.0/v1.4.1 恶意代码事件）
- 补充快速上手截图/GIF
- 考虑在 V2EX / Linux.do / 少数派 发推广帖

---

## 技术架构速查

| 参数 | 值 |
|------|-----|
| 版本基线 | GoEdge v1.3.9 |
| 当前 FreeCDN 版本 | v0.1.7（main 分支干净，无未发布提交） |
| Go 最低版本 | 1.21 |
| MySQL | 5.7.8+（推荐 8.0+），只能 TCP 连接 |
| EdgeAdmin 端口 | 7788 |
| EdgeAPI gRPC 端口 | 8003 |
| 上游许可证 | BSD-3-Clause |
| FreeCDN 许可证 | Apache-2.0 |
| 编译标志 | `-tags community`（开源版） |
| 密码存储 | MD5（非 bcrypt） |
| CI 状态 | GitHub Actions 账单冻结，release 需本地 local_build_release.py 手动构建 |

**架构关键原则**：EdgeNode 和 EdgeAdmin 均不直连 MySQL，所有数据操作通过 EdgeAPI（gRPC 8003）。

**已知坑（必须记住）**：
- `edgeAPINodes.uniqueId` ≠ `adminNodeId`（旧文档错误，真实字段是 `uniqueId`）
- `edgeAPINodes.http` 的 `listen[0].protocol` 必须是 `"http"`（空字符串 → edge-api 无法启动）
- `edgeAPINodes.accessAddrs` 必须含真实 IP（空数组 `[]` → SyncAPINodesTask nil pointer panic）
- `api_admin.yaml` 必须用嵌套 YAML 格式（`rpc:` / `  endpoints:` / `    - "..."``），点号格式会导致 edge-admin "wrong token role"
- `edgeAPITokens.role=admin` 的 nodeId 必须与 `api_admin.yaml` 中一致
- `edgeSysSettings` INSERT 不能有 `updatedAt` 字段（该表无此列）
- 管理员密码 MD5 存储，不是 bcrypt
- curl 访问管理后台返回 403（正常），需要浏览器访问

---

## 不做的事

- **计费/套餐系统**：永远不设付费功能墙
- **Windows 服务端支持**：边缘节点只支持 Linux
- **PostgreSQL/SQLite 支持**：只支持 MySQL（上游限制，不打算改）
- **前端框架升级（近期）**：Vue 2 足够用，不浪费时间升 Vue 3（中期可选）
- **跟踪 GoEdge v1.4.x+**：v1.4.0/v1.4.1 含恶意代码，永不合并
