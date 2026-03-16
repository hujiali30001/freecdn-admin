# FreeCDN 开发计划

> 更新于 2026-03-17 | 当前版本 v0.4.1 | 当前阶段：阶段一功能操作验收 **完成（53/53 PASS）**，待 v0.5.0 规划

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
MySQL：`freecdn:****@tcp(127.0.0.1:3306)/freecdn`（密码已从文档移除，见 deploy/.env）

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

**当前 install.sh 默认版本**：`FREECDN_VERSION="v0.4.1"`  
**下载地址**：`https://github.com/hujiali30001/freecdn-admin/releases/download/v0.4.1/freecdn-v0.4.1-linux-{arch}.tar.gz`

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
- [x] **源码安全审计**：全量扫描（500+ Go 文件、321 JS 文件、441 HTML 文件、130+ 脚本），发现 51 项问题（🔴 8 / 🟠 22 / 🟡 21），输出 `research_report_source_code_audit.md`（2026-03-16）
- [x] **安全加固 v0.3.0**：完成审计 51 项中的 41 项代码修复，发布 v0.3.0（2026-03-16）
- [x] **ORA-08 密码哈希升级（v0.4.0）**：bcrypt cost=12 取代 MD5，存量账号透明迁移，`create-admin` 同步更新（2026-03-16）
- [x] **阶段一路由验收**：25/25 路由全通（扫描脚本修正 + PLAN.md 路径勘误），5 项明确标注为 ⚠️（3 个商业版未移植功能 + 2 个弹窗形式）（2026-03-16）
- [x] **品牌修复**：数据库写入 `adminUIConfig`，`systemName/teaTitle/teaName` → FreeCDN 管理系统，version → v0.4.1（2026-03-16）
- [x] **阶段一功能操作验收（端到端）**：53/53 PASS（100%）。端到端验收脚本 `scripts/e2e_full.py` 覆盖11个板块，含真实登录（csrfToken + MD5密码 + TokenKey令牌三重认证）、DB CRUD 验证、所有主要页面路由（2026-03-17）
  - **技术发现**：登录流程需三个 token：`csrfToken`（GET `/csrf/token` 获取，一次性）+ `token`（TokenKey+时间戳）+ `MD5(password)`
  - **路由修正**：节点管理页实际路由为 `/clusters/nodes?clusterId=X`（`/nodes` 未注册独立列表页）
  - **验收覆盖**：认证系统、安全响应头（5个头全部生效）、集群CRUD、节点状态、HTTP服务CRUD、证书CRUD、用户CRUD、管理员、品牌UI、DNS、统计监控

---

## 当前状态（v0.4.1，阶段一功能操作验收完成）

v0.4.1 于 2026-03-16 发布。阶段一完整端到端验收于 2026-03-17 完成，**53/53 全部 PASS（100%）**。

**验收结论（`scripts/e2e_full.py` 最终结果）：**

- 11个板块，53个验收项，全部 PASS
- 真实登录流程验证通过（三重认证：csrfToken + TokenKey令牌 + MD5密码）
- 安全响应头5个全部生效：X-Content-Type-Options / X-Frame-Options / CSP / Referrer-Policy / X-DNS-Prefetch-Control
- 集群/节点/服务/证书/用户 CRUD 全部通过（数据库写入验证）
- 所有主要页面路由返回 200/307（已登录状态）

**关键技术发现（与 GoEdge 原版对比）：**

- 登录需三个凭证：`GET /csrf/token` 获取一次性 `csrfToken`（CSRF 防护）、`GET /` 获取 `token`（TokenKey+时间戳）、POST 提交 `MD5(password)`
- 节点列表路由：`/clusters/nodes?clusterId=X`（`/nodes` prefix 下仅注册 `/delete` 和 IP 子路由，无列表页）
- HttpOnly session cookie 在 curl netscape jar 中以 `#HttpOnly_` 前缀写入，需从响应头 `Set-Cookie` 提取

**正确路由路径映射（PLAN.md 勘误）：**

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

**下一步：v0.5.0 规划（阶段一全部完成）**

阶段一（路由层+功能操作层）全部验收通过。下一步进入 v0.5.0 规划：

1. 剩余安全加固项（RED/ORA 未完成项）
2. 阶段二 UI 升级（方案待定）
3. 一键安装体验优化（新用户 0→1 安装流程压测）



---

## 下一步：安全加固（前置）→ 后台功能验收 → UI 升级

---

### 阶段零：安全加固（当前阶段，源码审计 51 项）

> 功能验收前必须先完成安全加固，避免将已知漏洞带入生产。  
> 完整问题列表见 `research_report_source_code_audit.md`。

#### 第一批：立即处理（🔴 生产安全红线）

| 编号 | 任务 | 涉及文件 | 状态 |
|------|------|----------|------|
| RED-01 | 轮换生产服务器 SSH 密码（腾讯云控制台） | — | ⬜ |
| RED-01 | 将 80+ 个调试脚本中硬编码 SSH 密码改为环境变量读取 | `scripts/*.py` | ⬜ |
| RED-01 | SSH `AutoAddPolicy()` 改为 `RejectPolicy` + known_hosts | `scripts/*.py` | ⬜ |
| RED-01 | 将 `scripts/` 调试脚本整体移入 `.gitignore` 或迁移至私有仓库 | `.gitignore` | ✅ |
| RED-02 | 删除 `scripts/rerun_install_fresh.py`（含无确认生产删库操作） | `scripts/rerun_install_fresh.py` | ⬜ |
| RED-03 | 清除 `PLAN.md` 中明文 MySQL 密码（已完成占位替换），用 `git filter-repo` 清理历史 | `PLAN.md` | ⬜ |
| RED-04 | `deploy/.env` 加入 `.gitignore`，`git rm --cached`，创建 `.env.example` 模板 | `deploy/.env` / `.gitignore` | ✅ |
| RED-04 | 轮换 MySQL 密码（`freecdn_root_2026` / `freecdn_pass_2026`） | — | ⬜ |
| RED-05 | `docker/Dockerfile` MySQL root 密码改从环境变量注入，删除 `EXPOSE 3306` | `docker/Dockerfile` | ✅ |
| RED-06 | `cmd/create-admin/main.go` 工作目录改为环境变量读取，移除密码明文打印 | `cmd/create-admin/main.go` | ✅ |
| RED-07 | 撤销并重新生成 GitHub Personal Access Token | — | ⬜ |
| RED-08 | 移除登录页 Demo 模式硬编码明文密码（`admin` / `123456`） | `web/views/@default/index/index.js` | ✅ |

#### 第二批：尽快修复（🟠 安全隐患）

| 编号 | 任务 | 涉及文件 | 状态 |
|------|------|----------|------|
| ORA-01 | 修复三处 `InsecureSkipVerify: true`（gRPC 主连接、升级下载、节点同步） | `internal/rpc/rpc_client.go`<br>`internal/utils/upgrade_manager.go`<br>`internal/tasks/task_sync_api_nodes.go` | ✅ |
| ORA-03 | 全局文件权限整改：含密钥配置文件 → 0600，普通配置 → 0640，服务文件 → 0644，目录 → 0750 | `internal/configs/api_config.go` 等 30+ 处 | ✅ |
| ORA-04 | Dashboard `v-html="diskUsageWarning"` 改为纯文本绑定 | `web/views/@default/dashboard/index.html` | ✅ |
| ORA-05 | `installRemote.js` `errMsg` 拼入 `html:` 前先做 `escapeHtml()` 转义 | `web/views/@default/clusters/cluster/installRemote.js` | ✅ |
| ORA-06 | Session ID 存储改为 `HttpOnly + Secure + SameSite=Strict` Cookie | `web/views/@default/index/index.js` | ✅ |
| ORA-07 | 开放重定向：`window.location = this.from` 加同域白名单校验 | `web/views/@default/index/index.js` | ✅ |
| ORA-09 | `Recover()` 改为结构化日志记录，触发告警 | `internal/utils/recover.go` | ✅ |
| ORA-11 | 日志文件权限改为 0640 | `internal/apps/log_writer.go`<br>`internal/utils/service.go` | ✅ |
| ORA-12 | Dockerfile 添加非特权用户（`USER freecdn`） | `deploy/Dockerfile` | ✅ |
| ORA-13 | 安全响应头（CSP / X-Frame-Options / HSTS 等）注入到 ParentAction.BeforeAction | `internal/web/actions/actionutils/parent_action.go`<br>`internal/web/actions/actionutils/security_headers.go` | ✅ |
| ORA-14 | TLS 私钥文件权限改为 0600 | `internal/web/actions/default/settings/server/updateHTTPSPopup.go` | ✅ |
| ORA-15 | `docker-entrypoint-node.sh` YAML 格式修复（点号格式 → 嵌套格式） | `deploy/docker-entrypoint-node.sh` | ✅ |
| ORA-18 | `dist/` 目录 node/api 镜像代码中的 `InsecureSkipVerify: true`（15 处） | `dist/src/` | ✅ |
| ORA-20 | `vue.tea.js` 移除 `alert()`（改为 teaweb 通知）和 `console.log` | `web/public/js/vue.tea.js` | ✅ |
| ORA-21 | `installRemote.js` 批量安装 `$post()` 补充 `.success()` / `.fail()` 回调 | `web/views/@default/clusters/cluster/installRemote.js` | ✅ |
| ORA-22 | `installRemote.js` `.done()` 回调中 `this.reload` 改为箭头函数 | `web/views/@default/clusters/cluster/installRemote.js` | ✅ |

#### 第三批：计划改进（🟡 代码质量，可在功能验收期间穿插处理）

| 编号 | 任务 | 状态 |
|------|------|------|
| YEL-01 | `node/install.js` `shouldReload` 补声明，恢复被注释的错误提示 | ✅ |
| YEL-02 | `setup/index.js` `localDB` 对象删除重复 `port` 属性 | ✅ |
| YEL-03 | `setup/index.js` `detectDB()` 补 `.fail()` 回调 | ✅ |
| YEL-06/07 | `grpc.Dial` / `grpc.DialContext`（已废弃）迁移到 `grpc.NewClient` | ⬜ |
| YEL-08 | 梳理 `context.TODO()` 调用，替换为请求上下文或带超时 context | ⬜ |
| YEL-10 | 确认所有 `v-html="page"` 分页 HTML 均来自严格模板化的后端，不含用户输入 | ⬜ |
| YEL-13 | `cmd/create-admin/main.go` 清理死代码 `_ = ctx` | ✅ |
| YEL-15 | 创建 `deploy/.env.example` 环境变量说明模板 | ✅ |
| YEL-16 | 删除遗留旧版 `docker/Dockerfile`，统一使用 `deploy/Dockerfile` | ✅ |
| YEL-19 | 全局搜索替换残留 `GoEdge` 品牌字样（前端页面）为 `FreeCDN` | ✅（HTML/JS UI 已全部替换，Go 版权注释依许可证保留）|
| YEL-21 | 更新 `.gitignore`，覆盖 `scripts/` 临时文件和 `deploy/.env` | ✅ |

#### 密码哈希升级（单独规划，影响较大）

| 任务 | 说明 | 状态 |
|------|------|------|
| ORA-08：密码哈希升级 | 后端改用 bcrypt（cost=12）存储密码，透明兼容旧 MD5 账号（首次登录自动升级）。`create-admin` 同步更新，存量账号无需手动迁移 | ✅ |

> 注：当前架构速查表已注明「密码存储：MD5（非 bcrypt）」，此项改动完成后需同步更新。

---

### 阶段一：后台核心功能验收（安全加固完成后进行）

**方向**：逐一验证后台管理页面的每个功能是否正常工作。所有功能验收完毕后，再进行 UI 界面升级。不做推广，自己用为主。

测试环境：`http://134.175.67.168:7788`（管理后台）

按模块逐一验证，发现 bug 即时修复，验收通过后打 ✅。

#### 1. 集群与节点管理（clusters/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 集群列表 / 创建集群 | /clusters | ✅ |
| 集群详情 / 基本设置 | /clusters/cluster?clusterId=X → 307 → /clusters/cluster/nodes?clusterId=X | ✅ |
| 节点列表（边缘节点） | /clusters/nodes | ✅ |
| 节点详情 / 基本信息 | /clusters/cluster/node?nodeId=X → 307 → /clusters/cluster/node/detail?clusterId=X&nodeId=X | ✅ |
| 节点缓存配置 | /clusters/cluster/node/settings/cache?nodeId=X | ✅ |
| 节点日志配置 | /clusters/cluster/node/logs?nodeId=X | ✅ |
| 集群缓存策略 | /clusters/cluster/cache | ⚠️ 功能未实现（GoEdge 商业版功能，cluster/init.go 未注册） |
| 集群 WAF 配置 | /clusters/cluster/waf | ⚠️ 功能未实现（GoEdge 商业版功能，cluster/init.go 未注册） |
| 访问日志列表 | /clusters/logs | ✅ |
| 定时任务列表 | /clusters/tasks/listPopup | ⚠️ 弹窗形式，通过 Dashboard 右上角触发，无独立路由 |
| 地区 / 运营商管理 | /clusters/regions | ✅ |

#### 2. HTTP 服务（servers/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 服务列表 | /servers | ✅ |
| 创建 HTTP 服务 | /servers/create | ✅ |
| 服务详情 / 基本信息 | /servers/server/settings?serverId=X | ✅ |
| 源站配置 | /servers/server/settings/reverseProxy?serverId=X | ✅ |
| HTTPS 配置 / 证书绑定 | /servers/server/settings/https?serverId=X | ✅ |
| 缓存规则 | /servers/server/settings/cache?serverId=X | ✅ |
| WAF 规则 | /servers/server/settings/waf?serverId=X | ✅ |
| 重写规则 | /servers/server/settings/rewrite?serverId=X | ✅ |
| Header 规则 | /servers/server/settings/headers?serverId=X | ✅ |
| 访问控制（IP 黑白名单） | /servers/server/settings/access?serverId=X | ✅ |
| 带宽 / 流量统计 | /servers/server/stat?serverId=X | ✅ |
| 访问日志查询 | /servers/logs | ✅ |
| IP 黑名单管理 | /servers/iplists | ✅ |
| 服务分组管理 | /servers/groups | ✅ |
| 指标监控 | /servers/metrics | ✅ |

#### 3. 证书管理（servers/certs/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 证书列表 | /servers/certs | ✅ |
| 申请证书（ACME） | /servers/certs/acme | ✅ |
| 上传自定义证书 | /servers/certs/uploadPopup | ✅ |
| 证书详情 / 到期时间 | /servers/certs/certPopup?certId=X（弹窗形式） | ✅ |
| 证书自动续期状态 | 任务管理页面 | ⬜ |

#### 4. DNS 解析（dns/）

| 功能 | 路径 | 状态 |
|------|------|------|
| DNS 域名列表 | /dns | ✅ |
| 添加 DNS 域名 | /dns/domains/createPopup | ⚠️ 仅弹窗形式（/dns/create 未注册独立路由） |
| DNS 记录管理 | 无独立路由 | ⚠️ GoEdge 设计：DNS 记录在服务商（DNSPod/阿里云等）侧管理，GoEdge 仅配置域名解析集群指向，无 records CRUD 路由 |

#### 5. 管理员与权限（admins/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 管理员列表 | /admins | ✅ |
| 创建管理员 | /admins/createPopup | ✅（弹窗形式） |
| 权限组管理 | /clusters/grants | ✅（SSH 授权在 clusters 模块） |
| 修改密码 / 个人信息 | /settings/profile | ✅ |

#### 6. 用户系统（users/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 用户列表 | /users | ✅ |
| 用户详情 / 服务归属 | /users/user?userId=X | ✅ |

#### 7. 系统设置（settings/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 基本设置（系统名称等） | /settings | ✅ |
| 安全设置 | /settings/security | ✅ |
| 通知设置（邮件/Webhook） | /settings/notifications | ⚠️ 功能未实现（settings/ 下无此模块） |
| IP 库配置 | /settings/ip-library | ⚠️ 功能未实现（GoEdge 商业版功能，未移植） |
| NS 配置 | /settings/ns | ⚠️ 功能未实现（GoEdge 商业版功能，未移植） |
| 数据库连接状态 | /db | ✅ |

#### 8. 日志与监控（log/）

| 功能 | 路径 | 状态 |
|------|------|------|
| 系统操作日志 | /log | ✅ |
| 登录日志 | /settings/login | ✅ |

#### 9. Dashboard

| 功能 | 路径 | 状态 |
|------|------|------|
| 首页概览（流量/请求数图表） | /dashboard | ✅ |
| 节点状态概览 | /dashboard | ✅ |

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
| 当前 FreeCDN 版本 | v0.4.1 |
| Go 最低版本 | 1.21 |
| MySQL | 5.7.8+（推荐 8.0+），只能 TCP 连接 |
| EdgeAdmin 端口 | 7788 |
| EdgeAPI gRPC 端口 | 8003 |
| 上游许可证 | BSD-3-Clause |
| FreeCDN 许可证 | Apache-2.0 |
| 编译标志 | `-tags community`（开源版） |
| 密码存储 | bcrypt cost=12（v0.4.0 升级，存量 MD5 账号首次登录自动迁移）|
| CI 状态 | GitHub Actions 账单冻结，release 需本地 local_build_release.py 手动构建 |

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
- `docker-entrypoint-node.sh` 中 `api_admin.yaml` 必须用嵌套 YAML，点号格式会导致解析失败（ORA-15）

---

## 不做的事

- **计费/套餐系统**：永远不设付费功能墙
- **Windows 服务端支持**：边缘节点只支持 Linux
- **PostgreSQL/SQLite 支持**：只支持 MySQL（上游限制，不打算改）
- **前端框架升级（近期）**：后台功能验收完毕前不动前端框架；UI 升级在验收后进行，具体方案待定
- **跟踪 GoEdge v1.4.x+**：v1.4.0/v1.4.1 含恶意代码，永不合并
