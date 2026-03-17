# FreeCDN 开发计划

> 更新于 2026-03-17 | 当前版本 v0.9.2（已发布）| 当前阶段：**阶段二 — UI 升级**

---

## 项目定位

基于 GoEdge 社区版（BSD-3-Clause）的 Fork，以 Apache-2.0 发布。目标：让任何人能用一条命令在自己的服务器上搭起完整 CDN，全程无需阅读文档，无计费墙，纯免费开源。

**新战略（2026-03-17 起）**：彻底与 GoEdge 上游切割，完全独立自主，一次性系统性解决所有部署问题，不再缝缝补补。

---

## 当前服务器

| 角色 | IP | 服务 |
|------|----|------|
| 管理节点（WSL 本地） | 172.24.213.247 | freecdn-admin、edge-api |

管理后台：`http://172.24.213.247:7788`  
账号：`admin` / `FreeCDN2026!!`  
MySQL：`freecdn:****@tcp(127.0.0.1:3306)/freecdn`

> 腾讯云服务器已退订，改用 WSL 本地环境开发测试。重启 WSL 后运行：  
> `python.exe c:\Users\Administrator\.workbuddy\FreeCDN\dist\wsl_restart.py`

---

## 四仓库架构全貌（代码梳理 2026-03-17）

### 仓库列表

| 仓库 | Go module 名（现状） | 当前版本号 | 角色 |
|------|----------------------|------------|------|
| freecdn-admin | `github.com/TeaOSLab/EdgeAdmin` | 0.1.0（const.go） | 管理后台 Web + CLI，端口 7788 |
| freecdn-api | `github.com/TeaOSLab/EdgeAPI` | 1.3.9（const.go） | gRPC API 服务，端口 8003，直连 MySQL |
| freecdn-node | `github.com/TeaOSLab/EdgeNode` | 1.3.9（const.go） | 边缘节点，含 CGO（mattn/go-sqlite3 等） |
| EdgeCommon | `github.com/TeaOSLab/EdgeCommon` | — | 共享库：protobuf 生成的 pb/、dao 接口、配置结构体、serverconfigs 等 |

### 依赖关系图

```
freecdn-admin ──→ EdgeCommon (replace → hujiali30001/EdgeCommon)
freecdn-api   ──→ EdgeCommon (replace → hujiali30001/EdgeCommon)
freecdn-node  ──→ EdgeCommon (replace → hujiali30001/EdgeCommon)

freecdn-admin ──gRPC 8003──→ freecdn-api ──MySQL 3306──→ MySQL
freecdn-node  ──gRPC 8003──→ freecdn-api
```

### EdgeCommon 关键内容

EdgeCommon 是整个系统的"合同层"，包含：
- `pkg/rpc/pb/` — 300+ protobuf 生成文件（约 40 个 gRPC Service，每个含 .pb.go + _grpc.pb.go）
- `pkg/rpc/dao/` — 客户端 DAO 接口（rpc_client.go 定义 RPCClient interface，含 40+ 方法）
- `pkg/rpc/protos/` — 原始 .proto 文件（180+ 文件）
- `pkg/nodeconfigs/` — 节点配置结构体
- `pkg/serverconfigs/` — 服务配置结构体（HTTP/HTTPS/反代/缓存/WAF 等）
- `pkg/configutils/` / `pkg/iplibrary/` — 工具包
- `pkg/langs/messages/` — 国际化消息（admin/api/node 均 import）

### 现状问题清单（系统性）

#### 问题一：Go module 名仍是 GoEdge 路径
三个主仓库的 `module` 声明仍为 `github.com/TeaOSLab/Edge*`，虽然内部已品牌替换，但 go.mod 模块名、import 路径均未改成 `github.com/hujiali30001/freecdn-*`。这意味着：
- 内部包互相 import 时写的是 `github.com/TeaOSLab/EdgeAdmin/internal/...`，不是 `github.com/hujiali30001/freecdn-admin/...`
- 对外表现（go get、go doc）仍是 GoEdge 路径

#### 问题二：版本号分裂
- freecdn-admin const.go: `Version = "0.1.0"`（未随 Release 更新）
- freecdn-api const.go: `Version = "1.3.9"`（GoEdge 原始版本号）
- freecdn-node const.go: `Version = "1.3.9"`（GoEdge 原始版本号）
- install.sh: `FREECDN_VERSION="v0.5.0"`
- deploy/Dockerfile ARG: `FREECDN_VERSION=v0.3.0`（未更新）
- deploy/docker-compose.yml: `FREECDN_VERSION:-v0.1.6`（未更新）

#### 问题三：数据库初始化流程过于脆弱（部署失败主要来源）
install.sh 中的数据库初始化依赖多步骤 MySQL INSERT，每一步都有格式陷阱：
- `edgeAPINodes.http` JSON 中 `listen[0].protocol` 必须是 `"http"`（空字符串 → api 无法启动）
- `edgeAPINodes.accessAddrs` 必须含真实 IP（空 → SyncAPINodesTask nil pointer panic）
- `api_admin.yaml` 必须嵌套 YAML 格式（点号格式 → "wrong token role"）
- `edgeSysSettings` INSERT 不能含 `updatedAt` 字段（该表无此列）
- `edgeAPITokens.role=admin` 的 nodeId 必须与 `api_admin.yaml` 一致
- setup confirm HTTP 回调必须在 api 启动后才能成功（有竞争）

#### 问题四：GoEdge 兜底下载源残留
install.sh 中仍保留：
- `https://goedge.rip/...` 作为备用下载源
- `https://dl.goedge.cloud/...` 作为备用下载源
下载策略：FreeCDN GitHub Release → 镜像站 → GoEdge 官方兜底（不可接受）

#### 问题五：CGO 编译环境约束
freecdn-node 依赖 `mattn/go-sqlite3`（CGO），只能在 Linux 环境编译，导致本地构建必须走 WSL，GitHub Actions 不可用（账单冻结）。

#### 问题六：配置文件管理分散
- `api_admin.yaml`（admin 连 api 的认证凭据）
- `api.yaml`（api 自身身份）
- `db.yaml`（MySQL 连接）
- `server.yaml`（HTTP 监听配置）
- `api_node.yaml`（node 连接 api 的配置）
各文件分散在 `configs/` 目录，格式敏感，无统一验证工具。

---

## 独立自主路线图（新战略，2026-03-17 制定）

### 战略目标

1. **Go module 名完全改为 FreeCDN 命名空间**（`github.com/hujiali30001/freecdn-*`）
2. **版本号统一**：三个仓库 const.go 版本号与 Release tag 完全一致
3. **一键部署零报错**：install.sh 数据库初始化彻底重构，消除所有已知坑
4. **彻底移除 GoEdge 兜底下载**：install.sh 只从 FreeCDN GitHub Releases 下载
5. **构建自动化**：本地构建脚本覆盖全流程，不依赖 GitHub Actions

### 分阶段实施计划

---

## 阶段 A：快速止血（v0.6.0，一键部署彻底修复）

**目标**：不改 Go module 名，先把部署成功率提到 100%。

### A-1：版本号统一（最高优先级）

| 文件 | 当前值 | 目标值 |
|------|--------|--------|
| freecdn-admin `internal/const/const.go` | `Version = "0.1.0"` | `Version = "0.6.0"` |
| freecdn-api `internal/const/const.go` | `Version = "1.3.9"` | `Version = "0.6.0"` + `GoEdgeVersion = "1.3.9"` |
| freecdn-node `internal/const/const.go` | `Version = "1.3.9"` | `Version = "0.6.0"` + `GoEdgeVersion = "1.3.9"` |
| deploy/Dockerfile ARG | `FREECDN_VERSION=v0.3.0` | `FREECDN_VERSION=v0.6.0` |
| deploy/docker-compose.yml | `FREECDN_VERSION:-v0.1.6` | `FREECDN_VERSION:-v0.6.0` |

> freecdn-api 和 freecdn-node 的版本号在两个独立仓库中，需要分别 push。

### A-2：install.sh 数据库初始化重构

彻底重写 `install.sh` 中的 DB 初始化逻辑，解决已知所有格式陷阱：

**当前 6 步骤痛点 → 重构目标：edge-api setup 命令代替手动 SQL**

重构方案：
1. 运行 `edge-api upgrade`（执行增量 SQL 迁移）
2. 运行 `edge-api setup -api-node-protocol=http -api-node-host=127.0.0.1 -api-node-port=8003`（官方 setup 命令，自动创建 APINode + Token + SysSetting，返回 adminNodeId + adminNodeSecret）
3. 用返回的 adminNodeId + adminNodeSecret 生成 `api_admin.yaml`（嵌套格式，硬编码保证格式正确）
4. 调用 `edge-api` 创建管理员（用 create-admin 工具或 SQL）
5. 启动 edge-admin，触发 setup confirm

> `edge-api setup` 命令已在 freecdn-api `cmd/edge-api/main.go` 中实现，输出 JSON：`{"isOk":true,"adminNodeId":"...","adminNodeSecret":"..."}`。这是正确的初始化路径，install.sh 应完全切换到这条路径。

**当前问题**：install.sh 目前走的是纯手工 MySQL INSERT 路径，容易出错。

### A-3：移除 GoEdge 兜底下载源

install.sh 下载逻辑改为：
1. 主：`https://github.com/hujiali30001/freecdn-admin/releases/download/v{VERSION}/...`
2. 备1：`https://ghfast.top/https://github.com/...`（镜像加速）
3. 备2：`https://gh-proxy.com/...`（镜像加速）
4. **移除** goedge.rip 和 dl.goedge.cloud 所有引用

### A-4：api_admin.yaml 生成保证格式正确

install.sh 中写 `api_admin.yaml` 时，改用 heredoc 严格嵌套格式：

```yaml
rpc:
  endpoints:
    - "http://127.0.0.1:8003"
  nodeId: "XXXXXXXX"
  secret: "YYYYYYYY"
```

不再用字符串拼接，消除格式错误可能。

### A-5：三进程启动顺序加健康检查

install.sh 中的启动顺序加入重试等待机制：
1. 启动 edge-api，轮询 TCP 8003 端口最长等待 30 秒（每秒一次）
2. edge-api ready 后再启动 edge-admin
3. edge-admin 启动后轮询 HTTP 7788 端口最长等待 30 秒
4. 全部就绪后输出访问地址

**systemd 方案**：edge-api.service → edge-admin.service（`After=edge-api.service` + `Requires=edge-api.service`），自动依赖顺序。

### A-6：deploy/docker-entrypoint-admin.sh 健壮性升级

- 移除 `_auto_setup_confirm()` 竞态（当前用 `sleep 5` 等待，不可靠）
- 改为：edge-api ready 后立即调用 setup，不依赖定时轮询
- 增加 setup 失败时的明确错误输出和退出码

---

## 阶段 B：Go module 名重命名（v0.7.0，彻底独立自主）

**目标**：三个主仓库的 Go module 名从 `github.com/TeaOSLab/Edge*` 改为 `github.com/hujiali30001/freecdn-*`，包括 EdgeCommon。

### 工作量评估

| 仓库 | import 路径涉及文件数（估算） | 改名复杂度 |
|------|-------------------------------|------------|
| EdgeCommon | 约 200+ 文件（pb/ 生成代码） | 高（需重新 protoc 生成或 sed 批量替换） |
| freecdn-api | 约 400+ 文件 | 高（大量 import EdgeCommon + 自引用） |
| freecdn-node | 约 500+ 文件 | 高（同上） |
| freecdn-admin | 约 100 文件 | 中 |

### 执行方案

**方案一（推荐）：sed 批量替换 + go mod tidy**

```bash
# EdgeCommon 仓库：改 module 名
sed -i 's|github.com/TeaOSLab/EdgeCommon|github.com/hujiali30001/freecdn-common|g' go.mod
find . -name "*.go" -exec sed -i 's|github.com/TeaOSLab/EdgeCommon|github.com/hujiali30001/freecdn-common|g' {} +
go mod tidy

# freecdn-api 仓库
sed -i 's|module github.com/TeaOSLab/EdgeAPI|module github.com/hujiali30001/freecdn-api|g' go.mod
sed -i 's|github.com/TeaOSLab/EdgeAPI/|github.com/hujiali30001/freecdn-api/|g' go.mod
find . -name "*.go" -exec sed -i \
  -e 's|github.com/TeaOSLab/EdgeAPI/|github.com/hujiali30001/freecdn-api/|g' \
  -e 's|github.com/TeaOSLab/EdgeCommon|github.com/hujiali30001/freecdn-common|g' {} +
# 删除 replace 指令（EdgeCommon 已是独立仓库）
go mod tidy

# 同理处理 freecdn-admin、freecdn-node
```

**方案二：保持 replace 机制，仅改 EdgeCommon module 名**
- 最小改动：仅将 EdgeCommon 的 module 名改为 `github.com/hujiali30001/freecdn-common`
- 三个主仓库的 `replace` 指令更新到新路径
- 主仓库自身 module 名暂不改（推迟到 v1.0.0）

> 推荐先做方案二（v0.7.0），方案一（完整改名）留到 v1.0.0。

### EdgeCommon protobuf 重生成

当前 `pkg/rpc/pb/` 下的 .go 文件是由 .proto 文件生成的，package 名是 `pb`，不含模块路径，因此：
- **改模块名不需要重新 protoc**，只需 sed 替换 pb.go 文件头部的 `package` import 引用
- `pkg/rpc/protos/` 下的 .proto 的 `option go_package` 需要同步更新

---

## 阶段 C：一键部署终极版（v0.8.0）

### C-1：单二进制模式（stretch goal）

将 edge-admin + edge-api 合并为单一进程（`freecdn-server`），内嵌 gRPC 通信改为进程内直调：
- 减少配置文件（api_admin.yaml 不再需要）
- 消除三进程启动顺序依赖
- 新用户只需 `./freecdn-server start` + MySQL 即可运行

> 工程量大，暂列为 stretch goal，视 B 阶段完成情况决定。

### C-2：数据库自动迁移工具

用 Go 实现一个 `freecdn-init` 工具，替代 install.sh 中的所有 MySQL 手工操作：
- 自动检测数据库版本
- 自动执行增量迁移 SQL
- 自动初始化 APINode、Token、Admin
- 输出 api_admin.yaml（格式保证正确）

### C-3：健康检查端点

在 freecdn-api 和 freecdn-admin 各增加 `/health` HTTP 端点，install.sh 和 Docker 健康检查均使用此端点，替代端口探测。

---

## 阶段 D：构建自动化（持续，不阻塞其他阶段）

### 现状

GitHub Actions 账单冻结，所有 Release 由 `scripts/local_build_release.py` 本地构建：
- edge-node：WSL Ubuntu-24.04 编译（CGO 需要 Linux）
- edge-admin / edge-api：Windows Go 编译（CGO_ENABLED=0）

### 目标

- 保持 local_build_release.py 作为主构建方式（稳定可靠）
- 在 local_build_release.py 中加入版本号一致性检查（三个仓库 const.go 版本号必须与 Release tag 一致，否则拒绝构建）
- 探索 Gitea/Woodpecker CI 作为 GitHub Actions 替代（非必须，长期考虑）

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
| v0.1.8 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 修复 MySQL socket 认证（加 -h 127.0.0.1），修复 node 模式覆盖运行中二进制 (Text file busy) |
| v0.1.9 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | P3 HTTPS 链路验证通过：DuckDNS + Let's Encrypt DNS-01 + TLS 1.3 + HTTP/2 全链路跑通 |
| v0.2.0 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 文档完善：install.md 补 HTTPS 证书申请流程，faq.md 扩充 HTTPS FAQ，README 「为什么不用 GoEdge」段落展开，推广帖草稿 |
| v0.3.0 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 安全加固（审计 51 项中 41 项）：文件权限整改(0600/0640)、TLS 配置化、XSS 防护、安全响应头、Docker 非特权用户、entrypoint YAML 修复 |
| v0.4.0 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | ORA-08 密码哈希升级（MD5 → bcrypt cost=12），透明迁移，存量账号首次登录自动升级 |
| v0.4.1 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 修复 edgeAdmins.password varchar(32→64)，修复创建管理员 Data too long 错误（ORA-08 follow-up）|
| v0.5.0 | 2026-03-17 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 安全加固全部完成：脚本密码改环境变量、清理133个调试脚本、git 历史明文密码清除、GitHub PAT 轮换、grpc.NewClient 迁移 |
| **v0.6.0** | 2026-03-17 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | **阶段 A：版本号统一 + install.sh 彻底重构（edge-api setup）+ 移除 GoEdge 兜底 + Docker 竞态修复** |
| **v0.7.0** | 2026-03-17 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | **阶段 B：EdgeCommon module 名改为 freecdn-common，freecdn-api/node 自身 module 名改为 hujiali30001 命名空间** |
| **v0.9.0** | 2026-03-17 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | **阶段 C-2：freecdn-init Go 工具（替代 bash DB 初始化）；版本号统一 v0.9.0** |
| **v0.8.0** | 2026-03-17 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | **阶段 C：/health 端点（freecdn-admin:7788/health、freecdn-api:8004/health），freecdn-api/node module 名重命名确认完成，faq.md 版本更新** |
| **v0.9.1** | 2026-03-17 | **amd64 tar.gz ✓ + SHA256SUMS ✓ + install.sh ✓** | **SSH 安装节点专项修复（7 个坑全部解决）**：install.sh 自动上传到 Release；CRLF 换行符修复；zip 存放路径修正；zip 内部目录结构修正；unzip.go MkdirAll 防御性修复；helper 需重新编译后推到服务器；zipfile create_system=3 修复目录权限 |
| **v1.0.0** | 待规划 | — | **完整重命名（三主仓库 module 名全部改为 freecdn-* 命名空间）** |

**当前 install.sh 默认版本**：`FREECDN_VERSION="v0.9.1"`

> v0.1.6 起所有 Release 包均从**源码自主编译**（local_build_release.py），包含 edge-admin / edge-api / edge-node 三个组件，不依赖 GoEdge 官方二进制。

---

## 已完成

- [x] GoEdge v1.3.9 成功部署，CDN 转发 200 验证通过
- [x] 排查并修复三个关键技术坑（edge-api 字段名、http JSON 格式、accessAddrs）
- [x] install.sh 完整实现（管理节点 + 边缘节点模式，非交互参数支持）
- [x] fix_api.sh 运维修复脚本（7 步修复流程）
- [x] **P0 验收通过**：干净 Ubuntu 22.04 端到端跑通 install.sh，品牌 SQL 写入正确，HTTP 200，admin 账号可登录（v0.1.6）
- [x] Docker Compose + Dockerfile 完整实现（含数据库自动初始化、配置持久化）
- [x] **P1 验收通过**：docker compose up -d 跑通，容器启动正常，管理后台可访问（v0.1.6）
- [x] **P2 完成**：local_build_release.py 从三个自有仓库源码编译 amd64/arm64，手动上传到 GitHub Release
- [x] **P4 完成**：upstream-check.yml（每周检查 GoEdge 上游 tag，自动创建审计 Issue）
- [x] **P5 完成**：品牌替换全覆盖（JS/HTML/CSS/Go 常量）
- [x] 文档体系（ARCHITECTURE.md、docs/INSTALL.md、docs/FAQ.md）
- [x] README.md FreeCDN 化
- [x] 完成 GoEdge 全维度研究报告
- [x] **边缘节点接入验证**：install.sh --node 端到端跑通，freecdn-node active（2026-03-16）
- [x] **v0.1.8 修复**：MySQL socket 认证 bug + node 模式 Text file busy bug
- [x] **P3 HTTPS 链路验证**：DuckDNS + Let's Encrypt DNS-01 + TLS 1.3/HTTP2 全链路跑通
- [x] **文档完善（v0.2.0）**：install.md 补 HTTPS 申请流程；faq.md 扩充 HTTPS FAQ；推广帖草稿
- [x] **源码安全审计**：全量扫描 500+ Go 文件，发现 51 项问题，输出 research_report_source_code_audit.md
- [x] **安全加固 v0.3.0**：完成 41 项代码修复
- [x] **ORA-08 密码哈希升级（v0.4.0）**：bcrypt cost=12 取代 MD5，透明迁移
- [x] **阶段一路由验收**：25/25 路由全通
- [x] **品牌修复**：数据库写入 adminUIConfig，systemName/teaTitle/teaName → FreeCDN 管理系统
- [x] **安全加固全部完成（v0.5.0）**：RED-01/02/03/07 + YEL-06/07/10 全部清零
- [x] **阶段一功能操作验收（端到端）**：53/53 PASS（100%）
- [x] **四仓库代码全面梳理（2026-03-17）**：完整分析 freecdn-admin/api/node/EdgeCommon 架构，识别所有独立自主障碍，制定路线图
- [x] **阶段 A 完成（v0.6.0，2026-03-17）**：版本号统一（三仓库全改 0.6.0）、install.sh 彻底重构（edge-api setup 替代 7 步手工 SQL）、移除 GoEdge 兜底下载源、Docker entrypoint sleep 竞态修复、local_build_release.py 加版本一致性检查；amd64/arm64 Release 发布完成
- [x] **阶段 B 完成（v0.7.0，2026-03-17）**：EdgeCommon go.mod module 名改为 freecdn-common，595 处 import 路径批量替换，基于 v1.3.9 分支打 freecdn 专用 tag（v1.3.9-freecdn.2），三主仓库 go.mod/go.sum 全部更新，freecdn-admin/api/node 编译全部通过；amd64/arm64 Release 发布完成
- [x] **阶段 C-3 完成（v0.8.0，2026-03-17）**：freecdn-admin 在 7788 端口加 `/health` 端点，freecdn-api 在 8004 端口加 `/health` 端点，freecdn-api/node module 名确认重命名完成（B-3/B-4），faq.md 版本更新；amd64/arm64 Release 发布完成
- [x] **阶段 C-2 完成（v0.9.0，2026-03-17）**：新增 `freecdn-init` Go 工具（cmd/freecdn-init + internal/initdb），替代 install.sh 中 7 步 bash 数据库初始化，支持 upgrade/setup/api_admin.yaml 写入/api.yaml 同步/管理员创建/品牌写入全流程，保留 bash 兜底路径；版本号统一至 v0.9.0；amd64/arm64 Release 发布完成
- [x] **SSH 安装节点专项修复（v0.9.1，2026-03-17）**：完整走通从管理后台 SSH 安装边缘节点全流程，累计修复 7 个坑：(1) install.sh 自动上传到 Release；(2) CRLF 换行符转 LF；(3) edge-node zip 存放路径修正（`${API_DIR}/deploy/` + 版本号文件名）；(4) zip 内部目录结构修正（`edge-node/bin/edge-node` + `edge-node/configs/`）；(5) `unzip.go` 加 `MkdirAll` 防止 zip 缺目录条目时 OpenFile 失败；(6) 修复代码需重新编译并手动推到服务器（仅重启 api 不够）；(7) Python zipfile 在 Windows 上 create_system=0 导致目录权限 0664（缺 x 位），修复为 create_system=3（Unix）；amd64 Release 已更新并部署

---

## v0.6.0 任务清单（阶段 A，**已完成**）

### A-1：版本号统一

- [x] **freecdn-admin** `internal/const/const.go`：`Version = "0.6.0"`
- [x] **freecdn-api** `internal/const/const.go`：`Version = "0.6.0"`，保留 `GoEdgeVersion = "1.3.9"` 备注
- [x] **freecdn-node** `internal/const/const.go`：`Version = "0.6.0"`，同上
- [x] **deploy/Dockerfile** ARG：`FREECDN_VERSION=v0.6.0`
- [x] **deploy/docker-compose.yml**：`FREECDN_VERSION:-v0.6.0`
- [x] **install.sh**：`FREECDN_VERSION="v0.6.0"`
- [x] **local_build_release.py**：加版本号一致性检查断言

### A-2：install.sh 初始化重构

- [x] 重写 DB 初始化：用 `edge-api upgrade` + `edge-api setup` 替代手工 SQL
- [x] 解析 setup 命令 JSON 输出（`adminNodeId` + `adminNodeSecret`）
- [x] 用解析结果写 `api_admin.yaml`（heredoc 嵌套格式，0600 权限）
- [x] 三进程启动加 TCP 健康探测（轮询等待，超时 30 秒）
- [x] systemd Unit 文件加 `After=edge-api.service` 依赖

### A-3：移除 GoEdge 兜底

- [x] install.sh：删除 `goedge.rip` 和 `dl.goedge.cloud` 所有引用
- [x] install.sh：下载策略改为 GitHub Release → ghfast.top → gh-proxy.com
- [x] 搜索全仓库 `goedge.rip` / `dl.goedge.cloud` 确保无遗漏

### A-4：Docker 升级

- [x] docker-entrypoint-admin.sh：移除 sleep 竞态，改为 api ready 后立即 setup
- [x] 验证 docker compose up -d 端到端通过

### A-5：local_build_release.py 版本一致性检查

- [x] 构建前读取三个仓库的 `internal/const/const.go`，断言 Version == 当前 Release tag
- [x] 不一致则打印错误，终止构建

---

## v0.7.0 任务清单（阶段 B，**已完成**）

### B-1：freecdn-common module 名重命名

- [x] `go.mod` module 声明改为 `github.com/hujiali30001/freecdn-common`
- [x] 所有 `.go` 文件中 `github.com/TeaOSLab/EdgeCommon` 批量替换为 `github.com/hujiali30001/freecdn-common`
- [x] `go mod tidy`，确保编译通过
- [x] push 到 `hujiali30001/EdgeCommon` 仓库（分支 freecdn-v1.3.9）

### B-2：三主仓库 go.mod replace 指令更新

- [x] `replace github.com/hujiali30001/freecdn-common => github.com/hujiali30001/EdgeCommon v1.3.9-freecdn.2`
- [x] 所有 `.go` import 路径 `github.com/TeaOSLab/EdgeCommon` → `github.com/hujiali30001/freecdn-common`
- [x] `go mod tidy`，确保各仓库编译通过
- [x] 分别 push freecdn-api、freecdn-node

### B-3 / B-4 / B-5：freecdn-api/node/admin 自身 module 名

> freecdn-admin module 名已是 `hujiali30001/freecdn-admin`（v0.5.0 时已完成）
> freecdn-api/node module 名重命名留到阶段 C（不影响当前功能，延后处理）

### B-6：版本号更新至 v0.7.0 + 构建发布

- [x] 三仓库 `internal/const/const.go`：`Version = "0.7.0"`
- [x] 运行 `local_build_release.py --version v0.7.0` 构建并上传 Release

---

## 阶段一：后台核心功能验收（已完成 53/53）

**验收结论（`scripts/e2e_full.py` 最终结果）**：11个板块，53个验收项，全部 PASS（2026-03-17）

技术发现：
- 登录需三个凭证：GET /csrf/token 获取一次性 csrfToken + GET / 获取 token（TokenKey+时间戳）+ POST MD5(password)
- 节点列表路由：`/clusters/nodes?clusterId=X`（/nodes prefix 下仅注册 /delete 和 IP 子路由，无列表页）
- HttpOnly session cookie 在 curl netscape jar 中以 `#HttpOnly_` 前缀写入

正确路由路径映射：

| PLAN.md 记录路径 | 实际路由 |
|---|---|
| /clusters/cluster/detail | /clusters/cluster?clusterId=X → 307 → /clusters/cluster/nodes?clusterId=X |
| /clusters/cluster/node | /clusters/cluster/node?nodeId=X → 307 → /clusters/cluster/node/detail?clusterId=X&nodeId=X |
| /clusters/cluster/node/cache | /clusters/cluster/node/settings/cache?nodeId=X |
| /clusters/cluster/node/log | /clusters/cluster/node/logs?nodeId=X |
| /servers/server/detail | /servers/server/settings?serverId=X |
| /servers/server/origins | /servers/server/settings/reverseProxy?serverId=X |
| /servers/server/https | /servers/server/settings/https?serverId=X |
| /servers/server/cache | /servers/server/settings/cache?serverId=X |
| /servers/server/waf | /servers/server/settings/waf?serverId=X |
| /servers/server/rewrites | /servers/server/settings/rewrite?serverId=X |
| /servers/server/headers | /servers/server/settings/headers?serverId=X |
| /servers/server/access | /servers/server/settings/access?serverId=X |
| /servers/certs/cert | /servers/certs/certPopup?certId=X（弹窗） |

---

## 阶段二：UI 界面升级（功能验收完毕后进行）

**背景**：当前后台 UI 是 GoEdge 原版风格（Vue 2 + 自定义 CSS）。计划在功能验收后，系统性升级视觉风格。

**升级原则**：不改变功能逻辑，只改 CSS/HTML 模板；保持 Vue 2（不升 Vue 3）；优先改高频页面。

**待定方案**（功能验收完后再选）：
- 方案 A：统一配色 + 字体，换掉蓝色主题为更现代的深色/灰色风格
- 方案 B：引入 TDesign Vue 2 组件库，逐页替换原有 UI 组件
- 方案 C：直接替换为 Vue 3 + Vite + TDesign，彻底重写前端（暂不考虑）

---

## 技术架构速查

| 参数 | 值 |
|------|-----|
| 版本基线（GoEdge 安全锁定） | GoEdge v1.3.9（v1.4.x+ 含恶意代码，永不合并） |
| 当前 FreeCDN 版本 | v0.9.0（已发布）|
| Go 最低版本 | 1.21 |
| MySQL | 5.7.8+（推荐 8.0+），只能 TCP 连接（-h 127.0.0.1） |
| EdgeAdmin 端口 | 7788 |
| EdgeAPI gRPC 端口 | 8003 |
| 上游许可证 | BSD-3-Clause |
| FreeCDN 许可证 | Apache-2.0 |
| 编译标志 | `-tags community`（开源版） |
| 密码存储 | bcrypt cost=12（v0.4.0 升级，存量 MD5 账号首次登录自动迁移）|
| CI 状态 | GitHub Actions 账单冻结，release 需本地 local_build_release.py 手动构建 |
| EdgeCommon 依赖方式 | go.mod replace → github.com/hujiali30001/EdgeCommon（fork 版） |

**架构关键原则**：EdgeNode 和 EdgeAdmin 均不直连 MySQL，所有数据操作通过 EdgeAPI（gRPC 8003）。

**已知坑（必须记住）**：
- `edgeAPINodes.uniqueId` ≠ `adminNodeId`（旧文档错误，真实字段是 `uniqueId`）
- `edgeAPINodes.http` 的 `listen[0].protocol` 必须是 `"http"`（空字符串 → edge-api 无法启动）
- `edgeAPINodes.accessAddrs` 必须含真实 IP（空数组 `[]` → SyncAPINodesTask nil pointer panic）
- `api_admin.yaml` 必须用嵌套 YAML 格式（`rpc:` / `  endpoints:` / `    - "..."``），点号格式会导致 edge-admin "wrong token role"
- `edgeAPITokens.role=admin` 的 nodeId 必须与 `api_admin.yaml` 中一致
- `edgeSysSettings` INSERT 不能有 `updatedAt` 字段（该表无此列）
- 管理员密码 bcrypt 存储（v0.4.0 起），旧 MD5 账号首次登录自动升级
- curl 访问管理后台返回 403（正常），需要浏览器访问
- `deploy/.env` 不能提交 Git（已加入 `.gitignore`），使用 `.env.example` 作为模板
- 所有配置文件应以 0600 权限写入（含 RPC 密钥 `api_admin.yaml`、数据库配置 `db.yaml`）
- `docker-entrypoint-node.sh` 中 `api_admin.yaml` 必须用嵌套 YAML，点号格式会导致解析失败
- edge-api setup 命令输出 JSON：`{"isOk":true,"adminNodeId":"...","adminNodeSecret":"..."}`，是正确的初始化入口

**SSH 安装节点专项踩坑（v0.9.0～v0.9.1，2026-03-17）**：
- **坑1：Release 缺 install.sh**：`install.sh` 不会自动打进 tar.gz，需要在构建脚本末尾单独上传为 Release asset；已加入 `local_build_release.py` 自动化上传逻辑
- **坑2：install.sh CRLF 换行符**：在 Windows 上编辑过的 `.sh` 文件会带 CRLF，服务器 bash 解析时报 `\r: command not found`；已用 WSL `sed -i s/$'\r'//` 转换，`.gitattributes` 已配置 `*.sh eol=lf`（对现有文件需手动刷新）
- **坑3：edge-node zip 放置路径错误**：`install.sh` 之前将 zip 存到 `/var/lib/freecdn/edge-node.zip`，但 `LookupLatestInstaller()` 查找路径是 `Tea.Root/deploy/edge-node-linux-<arch>-v*.zip`（即 `/usr/local/freecdn/edge-admin/edge-api/deploy/`）；已修复 `install.sh`，zip 存到 `${API_DIR}/deploy/` 并保留带版本号的原始文件名
- **坑4：zip 内部目录结构错误（最初版本）**：`_make_node_zip()` 最初将二进制以 `arcname="edge-node"` 写在根目录，但 `installer_node.go` 期望解压后路径为 `<dir>/edge-node/bin/edge-node` 和 `<dir>/edge-node/configs/api_node.yaml`；已修复为 `edge-node/bin/edge-node` + `edge-node/configs/api_node.yaml`
- **坑5：zip 缺少目录条目导致 unzip 失败**：Python `zipfile.writestr("edge-node/configs/api_node.yaml", "")` 只写文件条目，不自动创建父目录条目；`unzip.go` 在写文件前不做 `MkdirAll`，导致 `write '...configs/api_node.yaml': file does not exist`；**双修**：(a) `unzip.go` 写文件前加 `filepath.Dir` + `MkdirAll`；(b) `_make_node_zip()` 显式写入 `edge-node/`、`edge-node/bin/`、`edge-node/configs/` 目录条目
- **坑6：修复代码未编译进已部署的 helper**：`unzip.go` 修复在 push 之前就触发了构建，服务器上的 `edge-installer-helper-linux-amd64` 还是旧版本（无 MkdirAll）；仅重启 freecdn-api 不够——helper 是独立二进制，必须重新编译整个 api 包再手动推到服务器；二进制大小相同不代表内容相同（Go `-trimpath -s -w` 编译会压缩）；**修复**：重新构建 v0.9.1、手动上传 helper+edge-api+zip 到服务器、验证方式是在服务器用 helper 解压无目录条目的测试 zip
- **坑7：Python zipfile 在 Windows 上 create_system=0 导致目录权限 0664**：Python `zipfile.ZipInfo` 在 Windows 宿主机上默认 `create_system=0`（Windows），Go 的 `archive/zip` 读到 `CreatorVersion>>8 != 3(Unix)` 时走 Windows 分支，忽略 `external_attr` 里的 Unix 权限位，用默认 `0666` 创建目录（umask 后变 `0664`），目录缺少执行位导致 `stat .../bin/: permission denied`；**修复**：`_make_node_zip()` 里所有 `ZipInfo` 对象显式设置 `create_system=3`（Unix），并同时设置 `compress_type=ZIP_STORED`（目录条目）；这也是本次安装失败的根本原因
- **坑8：SFTP 写 api_node.yaml 报 Permission Denied（root chown 文件本身漏掉）**：helper 以 root 解压 zip，`api_node.yaml` 归属 root:root 0644；`installer_node.go` 的 sudo 分支只 chown 了 `configs/` 目录，但文件本身仍属 root，SFTP（以 ubuntu 身份）直接写时被拒绝；**修复**：chown configs 目录的同时也 chown `api_node.yaml` 文件本身；helper 不需要每次手动推——`install.sh` 已将其安装到 `${API_DIR}/installers/`，代码用 `Tea.Root+"/installers/"+exeName` 找它，完全自动

---

## 不做的事

- **计费/套餐系统**：永远不设付费功能墙
- **Windows 服务端支持**：边缘节点只支持 Linux
- **PostgreSQL/SQLite 支持**：只支持 MySQL（上游限制，不打算改）
- **前端框架升级（近期）**：后台功能验收完毕前不动前端框架；UI 升级在验收后进行，具体方案待定
- **跟踪 GoEdge v1.4.x+**：v1.4.0/v1.4.1 含恶意代码，永不合并
- **重写 protobuf 定义**：EdgeCommon 的 .proto 文件是整个系统的接口契约，不重新设计，只做必要的模块重命名
