# FreeCDN 开发计划

> 更新于 2026-03-16 | 当前版本 v0.2.0 | 下一阶段：后台功能验收 → UI 升级

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
| v0.1.8 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 修复 MySQL socket 认证（加 -h 127.0.0.1），修复 node 模式覆盖运行中二进制 (Text file busy) |
| v0.1.9 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | P3 HTTPS 链路验证通过：DuckDNS + Let's Encrypt DNS-01 + TLS 1.3 + HTTP/2 全链路跑通 |
| v0.2.0 | 2026-03-16 | **amd64/arm64 tar.gz ✓ + SHA256SUMS ✓** | 文档完善：install.md 补 HTTPS 证书申请流程，faq.md 扩充 HTTPS FAQ，README 「为什么不用 GoEdge」段落展开，推广帖草稿 |

**当前 install.sh 默认版本**：`FREECDN_VERSION="v0.2.0"`  
**下载地址**：`https://github.com/hujiali30001/freecdn-admin/releases/download/v0.2.0/freecdn-v0.2.0-linux-{arch}.tar.gz`

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
- [x] **边缘节点接入验证**：install.sh --node 端到端跑通，freecdn-node active，日志无错误（2026-03-16）
- [x] **v0.1.8 修复**：MySQL socket 认证 bug + node 模式 Text file busy bug（2026-03-16）
- [x] **P3 HTTPS 链路验证**：DuckDNS + Let's Encrypt DNS-01 + TLS 1.3/HTTP2 全链路跑通，freecdntest.duckdns.org（2026-03-16）
- [x] **文档完善（v0.2.0）**：install.md 补 HTTPS 申请流程（DuckDNS + certbot DNS-01）；faq.md 扩充 HTTPS FAQ（9 个 Q&A）；README「为什么不用 GoEdge 官方」段落展开；推广帖草稿（docs/promo_post_draft.md）（2026-03-16）

---

## 当前状态（v0.2.0，main 分支干净）

v0.2.0 于 2026-03-16 发布，完成文档体系完善和社区推广准备：

**文档更新：**
- `docs/install.md`：新增「配置 HTTPS 证书」完整章节，涵盖管理台 UI 申请（HTTP-01）和 certbot DNS-01 两种方案，含 DuckDNS 注册、certbot 安装、证书申请、验证全流程 ✅
- `docs/faq.md`：HTTPS 部分从 3 个 Q 扩充到 9 个 Q，覆盖「没有域名怎么办」「端口 80 被安全组挡」「DNS-01 插件安装」「证书申请成功但未启用」等实际遇到的问题 ✅
- `README.md`：「为什么不用 GoEdge 官方」段落展开，详述 v1.4.0/v1.4.1 恶意代码事件始末和 FreeCDN 的应对策略 ✅
- `docs/promo_post_draft.md`：V2EX / Linux.do 推广帖草稿 ✅

**Release 产物：**
- `freecdn-v0.2.0-linux-amd64.tar.gz`
- `freecdn-v0.2.0-linux-arm64.tar.gz`
- `SHA256SUMS`

---

## 下一步：后台功能验收

**方向**：逐一验证后台管理页面的每个功能是否正常工作。所有功能验收完毕后，再进行 UI 界面升级。不做推广，自己用为主。

测试环境：`http://134.175.67.168:7788`（管理后台）

---

### 阶段一：后台核心功能验收

按模块逐一验证，发现 bug 即时修复，验收通过后打 ✅。

#### 1. 集群与节点管理（clusters/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 集群列表 / 创建集群 | /clusters | ⬜ |
| 集群详情 / 基本设置 | /clusters/cluster/detail | ⬜ |
| 节点列表（边缘节点） | /clusters/nodes | ⬜ |
| 节点详情 / 基本信息 | /clusters/cluster/node | ⬜ |
| 节点缓存配置 | /clusters/cluster/node/cache | ⬜ |
| 节点日志配置 | /clusters/cluster/node/log | ⬜ |
| 集群缓存策略 | /clusters/cluster/cache | ⬜ |
| 集群 WAF 配置 | /clusters/cluster/waf | ⬜ |
| 访问日志列表 | /clusters/logs | ⬜ |
| 定时任务列表 | /clusters/tasks | ⬜ |
| 地区 / 运营商管理 | /clusters/regions | ⬜ |

#### 2. HTTP 服务（servers/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 服务列表 | /servers | ⬜ |
| 创建 HTTP 服务 | /servers/create | ⬜ |
| 服务详情 / 基本信息 | /servers/server/detail | ⬜ |
| 源站配置 | /servers/server/origins | ⬜ |
| HTTPS 配置 / 证书绑定 | /servers/server/https | ⬜ |
| 缓存规则 | /servers/server/cache | ⬜ |
| WAF 规则 | /servers/server/waf | ⬜ |
| 重写规则 | /servers/server/rewrites | ⬜ |
| Header 规则 | /servers/server/headers | ⬜ |
| 访问控制（IP 黑白名单） | /servers/server/access | ⬜ |
| 带宽 / 流量统计 | /servers/server/stat | ⬜ |
| 访问日志查询 | /servers/logs | ⬜ |
| IP 黑名单管理 | /servers/iplists | ⬜ |
| 服务分组管理 | /servers/groups | ⬜ |
| 指标监控 | /servers/metrics | ⬜ |

#### 3. 证书管理（servers/certs/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 证书列表 | /servers/certs | ⬜ |
| 申请证书（ACME HTTP-01） | /servers/certs/apply | ⬜ |
| 上传自定义证书 | /servers/certs/upload | ⬜ |
| 证书详情 / 到期时间 | /servers/certs/cert | ⬜ |
| 证书自动续期状态 | 任务管理页面 | ⬜ |

#### 4. DNS 解析（dns/）

| 功能 | 路径 | 状态 |
|------|------|------|
| DNS 域名列表 | /dns | ⬜ |
| 添加 DNS 域名 | /dns/create | ⬜ |
| DNS 记录管理 | /dns/domain/records | ⬜ |

#### 5. 管理员与权限（admins/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 管理员列表 | /admins | ⬜ |
| 创建管理员 | /admins/create | ⬜ |
| 权限组管理 | /admins/grants | ⬜ |
| 修改密码 / 个人信息 | /admins/profile | ⬜ |

#### 6. 用户系统（users/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 用户列表 | /users | ⬜ |
| 用户详情 / 服务归属 | /users/user | ⬜ |

#### 7. 系统设置（settings/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 基本设置（系统名称等） | /settings | ⬜ |
| 安全设置 | /settings/safety | ⬜ |
| 通知设置（邮件/Webhook） | /settings/notifications | ⬜ |
| IP 库配置 | /settings/ip-library | ⬜ |
| NS 配置 | /settings/ns | ⬜ |
| 数据库连接状态 | /db | ⬜ |

#### 8. 日志与监控（log/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 系统操作日志 | /log | ⬜ |
| 登录日志 | /log/login | ⬜ |

#### 9. Dashboard

| 功能 | 路径 | 状态 |
|------|------|------|
| 首页概览（流量/请求数图表） | /dashboard | ⬜ |
| 节点状态概览 | /dashboard | ⬜ |

---

### 验收规则

- ⬜ = 未验收
- ✅ = 正常（页面加载、操作成功）
- ❌ = 有 bug（需记录具体表现）
- ⚠️ = 功能受限（如需要第二台节点才能验证）

每个 ❌ 条目需在下方「已知 Bug 列表」中记录复现步骤和修复方案。

---

### 已知 Bug 列表

_验收过程中发现的问题记录于此_

---

### 阶段二：UI 界面升级（功能验收完毕后进行）

**背景**：当前后台 UI 是 GoEdge 原版风格（Vue 2 + 自定义 CSS），较为陈旧。计划在功能全部验收后，系统性升级视觉风格。

**升级原则**：
- 不改变功能逻辑，只改 CSS/HTML 模板
- 保持 Vue 2（不升 Vue 3，避免大规模重构）
- 优先改高频页面：Dashboard、服务列表、服务详情

**待定方案**（功能验收完后再选）：
- 方案 A：统一配色 + 字体，换掉蓝色主题为更现代的深色/灰色风格
- 方案 B：引入 TDesign Vue 2 组件库，逐页替换原有 UI 组件
- 方案 C：直接替换为 Vue 3 + Vite + TDesign，彻底重写前端（工程量最大，暂不考虑）

---

## 技术架构速查

| 参数 | 值 |
|------|-----|
| 版本基线 | GoEdge v1.3.9 |
| 当前 FreeCDN 版本 | v0.2.0（main 分支干净，无未发布提交） |
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
- **前端框架升级（近期）**：后台功能验收完毕前不动前端框架；UI 升级在验收后进行，具体方案待定
- **跟踪 GoEdge v1.4.x+**：v1.4.0/v1.4.1 含恶意代码，永不合并
