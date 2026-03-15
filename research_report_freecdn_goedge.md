# 基于 GoEdge 构建免费开源 CDN 系统（FreeCDN）完整研究报告

> 研究日期：2026年3月15日 | 研究版本基准：GoEdge v1.3.9（社区安全版）

---

## 执行摘要

GoEdge 是目前中文社区中功能最完整的开源 CDN & WAF 系统，基于 Go 语言构建，提供反向代理、内容缓存、SSL 证书自动化、WAF 防护和多节点集群管理。其架构清晰、二次开发门槛适中，是构建 FreeCDN 最合适的基础。

然而，2024 年发生了一起严重的供应链安全事件：v1.4.0/v1.4.1 版本被植入恶意 JS 注入代码，导致逾百万网站流量被劫持。**FreeCDN 必须锁定在经社区验证安全的 v1.3.9 版本**，并谨慎对待任何上游更新。

本报告从架构分析、部署方案、二次开发、开源策略、竞品对比五个维度，为 FreeCDN 提供完整的技术路线图和决策建议。

---

## 一、GoEdge 项目全景概述

GoEdge 由上海茶博士软件有限公司（TeaOSLab）开发，以 BSD-3-Clause 开源协议发布。项目定位是企业级 CDN & WAF 集群管理系统，分为开源社区版和商业版，两者共用同一代码库，通过编译标签 `-tags community`（开源版）和 `-tags plus`（商业版）区分。

主仓库 `TeaOSLab/EdgeAdmin` 拥有 182 颗 GitHub Stars，代码提交超过 2,115 次。2024 年 5 月，原开发者"超哥"失联，项目疑似被黑产接管，随后 v1.4.0 和 v1.4.1 版本的 EdgeNode 被植入恶意代码。中文社区目前普遍推荐使用 **v1.3.9** 作为安全基线，部分项目（如 FlexCDN）直接以此版本为基础进行了分叉维护。

---

## 二、系统架构与技术栈详解

### 2.1 组件架构

GoEdge 采用分层微服务架构，各组件通过 gRPC 通信，高度解耦：

**开源版核心组件**包括 EdgeAdmin（管理平台，默认端口 7788）、EdgeAPI（API 节点，默认端口 8001）、EdgeNode（边缘节点，80/443）和 EdgeCommon（公共 proto3 定义库）。**商业版专属组件**包括 EdgeDNS（智能 DNS 解析）、EdgeUser（多租户计费平台）、EdgeReporter（区域可用性监控）。EdgeLog（日志数据库节点）作为可选组件存在于开源版中。

数据流方向如下：终端用户的 HTTP(S)/TCP/UDP 请求到达 EdgeNode，EdgeNode 通过 gRPC 长连接向 EdgeAPI 拉取配置并上报状态，EdgeAPI 是数据库的唯一访问入口。EdgeAdmin 通过 gRPC/HTTP 调用 EdgeAPI 完成所有管理操作。**EdgeNode 和 EdgeAdmin 均不直连 MySQL**，这是 GoEdge 架构的核心设计原则。

### 2.2 认证体系

组件间认证基于 `nodeId + secret` 对。EdgeAPI 启动时从 `api.yaml` 读取自身的 `nodeId`，在 `edgeAPINodes` 数据库表中校验身份；EdgeAdmin 用 `api_admin.yaml` 里的 `nodeId + secret` 向 EdgeAPI 发起 gRPC 认证，这组凭据存储在 `edgeAPITokens` 表的 `role=admin` 记录中；边缘节点用 `api_node.yaml` 里的集群 ID 和 secret 向 EdgeAPI 注册，凭据存储在 `edgeAPITokens` 表的 `role=node` 记录中。

### 2.3 技术栈

**后端**：Go 1.21+，gRPC（proto3）+ HTTP/JSON 双协议。EdgeAPI 占 Go 代码 99.8%，EdgeNode 占 Go 83.7% + C 15.8%（C 代码用于底层网络和加密处理）。数据库仅支持 MySQL 5.7.8+ / 8.0+ 和 TiDB 3.0+，不支持 PostgreSQL 或 SQLite，且必须通过 TCP 端口连接（不支持 Socket 文件）。依赖管理使用 Go Modules。

**前端**：EdgeAdmin 前端嵌入 Go 项目中，JavaScript 占 51.8%，HTML 占 13.8%，CSS/Less 约 1.7%。使用 Vue 2.x，组件集中定义在 `web/public/js/components.js`。开发模式下修改 `web/` 目录后刷新即可生效，生产构建命令为 `bin/edge-admin build`。

**关键数据库表**：`edgeAPINodes`（API 节点注册，关键字段 `uniqueId/http/accessAddrs`）、`edgeAPITokens`（访问令牌，含 `role` 字段区分 admin/user/node/cluster）、`edgeAdmins`（管理员账户，密码 MD5 存储）、`edgeNodes`（边缘节点注册）、`edgeServers`（网站服务配置）、`edgeCertificates`（SSL 证书）。

### 2.4 核心功能实现

GoEdge 支持 HTTP/HTTPS/HTTP3/TCP/UDP/WebSocket 全协议反向代理，内置多种负载均衡算法（轮询、加权、IP Hash 等），支持主动健康检查。内容缓存在 EdgeNode 本地实现，支持磁盘缓存和内存缓存，策略遵循 Cache-Control 并支持手动刷新。SSL 证书通过 ACME 协议自动向 Let's Encrypt 申请和续期，由 EdgeAPI 统一管理后分发给各 EdgeNode。WAF 功能在 EdgeNode 本地执行，支持 SQL 注入、XSS、CC/DDoS 防护、5 秒盾人机验证和 IP 黑白名单，规则由 EdgeAPI 统一下发。

---

## 三、部署方案选型

### 3.1 资源需求对比

| 部署场景 | CPU | 内存 | 磁盘 | 适用情况 |
|---------|-----|------|------|---------|
| 最小单机（管理+API+MySQL）| 1 核 | 1 GB | 10 GB | 测试/学习 |
| 推荐单机（含边缘节点）| 2 核 | 2 GB | 32 GB SSD | 个人/小团队 |
| 生产集群（每节点）| 4+ 核 | 8+ GB | 100 GB SSD | 中等流量 |
| 高流量生产节点 | 8+ 核 | 16+ GB | 200+ GB SSD | 千万+ 日访问量 |

1 核 1G 的服务器理论上可以运行，但需要将 MySQL 的 `innodb_buffer_pool_size` 调低到 256MB，并关闭不必要的统计功能。不建议在生产环境使用这种配置。

### 3.2 单机部署（脚本安装）

适用于测试环境和个人使用：

```bash
curl -s https://goedge.cloud/install.sh | bash
```

安装后访问 `http://服务器IP:7788` 完成 Web 向导配置。需提前开放防火墙端口：7788（管理 Web UI）、8001（gRPC 通信）、80/443（CDN 服务）。

**注意**：使用 FreeCDN 的 `install.sh` 一键脚本可跳过向导，自动完成数据库初始化、配置文件生成和服务注册，实测在 Ubuntu 20.04 上安装成功。

### 3.3 多节点集群部署

集群架构如下：管理节点（edge-admin + edge-api + MySQL）集中部署在一台服务器，所有边缘节点通过 **TCP 8001 端口**与管理节点通信。边缘节点无需对管理节点开放任何入站端口，仅需开放 80/443。配置变更通过 gRPC 长连接自动下发，边缘节点升级也无需外网，由 API 节点内置安装包分发。

### 3.4 Docker 部署（推荐生产方案）

官方提供了 `docker-compose.yaml`，通过环境变量配置数据库密码和网络前缀，包含 MySQL + goedge-instance（all-in-one 镜像）两个服务。完整的 docker-compose 配置已在子代理研究报告中获取，可直接引用。关键注意点：边缘节点容器**必须使用 `network_mode: host`** 才能正常监听 80/443 端口。

官方一键安装命令：
```bash
curl https://goedge.cloud/docker/instance/install.sh | bash
```

社区还有 `icodex/docker-goedge` 项目提供分离的管理节点和边缘节点镜像（支持 ARM64），但由于供应链安全事件背景，建议基于 FreeCDN 官方 Dockerfile 自行构建。

### 3.5 Kubernetes 部署

目前官方和社区均无成熟的 Helm Chart。边缘节点需要 `hostNetwork: true` 和 `NET_ADMIN` 权限，在 K8s 中限制较多。不推荐初学者使用 K8s 部署方案。

### 3.6 推荐免费/低成本云服务器方案

| 平台 | 方案 | 配置 | 费用 | 推荐用途 |
|------|------|------|------|---------|
| 甲骨文免费云 | ARM A1 实例 | 共 4 核 24GB 内存（可拆分为 4 台）| 永久免费 | 边缘节点首选 |
| 甲骨文免费云 | AMD 微型实例 ×2 | 1 核 1 GB | 永久免费 | 管理节点（合并使用）|
| 腾讯云轻量服务器 | 入门版 | 2 核 2 GB 60 GB SSD | ¥24/月起 | 国内边缘节点 |
| RackNerd VPS | 低价套餐 | 1 核 1 GB 20 GB | ~$12/年 | 海外边缘节点 |

甲骨文 ARM64 实例经社区验证可运行 GoEdge v1.3.9，是零成本搭建 FreeCDN 节点的最佳选择。需额外注意在甲骨文控制台（VCN 安全组）的 Ingress Rules 中开放端口，仅修改系统防火墙是不够的。

---

## 四、二次开发指南

### 4.1 GoedgeWorks 参考分析

GoedgeWorks（`Kuaien/GoedgeWorks`，Apache-2.0，v1.0.3）是 GoEdge 生态的非官方扩展资源库，主要提供以 aiFanCDN（免费）为代表的现代化 UI 模板替换方案，以及批量操作（批量建站、批量 SSL）、支付集成（USDT、彩虹易支付）等商业化插件。

对 FreeCDN 的参考价值：GoedgeWorks 证明了 GoEdge 的二次开发以**替换 `web/` 目录前端文件**为主要方式，技术可行且有实际演示站。FreeCDN 与 GoedgeWorks 的定位差异在于：FreeCDN 是完整可部署的开源系统，GoedgeWorks 是 UI 和插件资源集合。

### 4.2 品牌定制路径

| 替换内容 | 文件路径 | 方法 |
|---------|---------|------|
| 系统名称（GoEdge → FreeCDN）| `web/` 模板文件 + `internal/` 常量 | 全局搜索替换字符串 |
| Logo/图标 | `web/public/` 静态资源目录 | 替换 PNG/SVG 文件 |
| 版权信息 footer | `web/` 模板中的 footer 组件 | 修改 HTML 模板 |
| 浏览器标题 | `web/` 目录下 HTML 模板 | 修改字符串 |
| Vue 组件定义 | `web/public/js/components.js` | 修改 Vue 组件 |

**最小冲突策略**：将所有品牌相关改动集中到独立的 `branding.go` 常量文件和 `web/public/brand/` 目录中，避免散布在业务代码里。品牌相关内容通过配置文件或环境变量注入，不硬编码。

### 4.3 避坑清单（本次实战总结）

在将 FreeCDN 部署到 `134.175.67.168` 的过程中，排查了以下关键技术问题，这些是二次开发和自建安装脚本时必须注意的：

`edgeAPINodes` 表的字段名为 `uniqueId`（不是部分教程中提到的 `adminNodeId`），`http` 字段中 `listen[0].protocol` 必须显式设置为 `"http"`（空字符串会导致 edge-api 报"no listening address"错误，无法启动 gRPC 服务），`accessAddrs` 字段必须包含至少一个含真实 IP 的地址（空数组 `[]` 会触发 `SyncAPINodesTask` 的 nil pointer panic）。

`api_admin.yaml` 的 `nodeId` 必须与 `edgeAPITokens` 表中 `role=admin` 的记录匹配，两者不一致时会报 `can not find api token`。`edgeAdmins` 表存储管理员账号，密码是 MD5（非 bcrypt），安装时需手动插入初始账号。访问管理后台时，GoEdge 通过 User-Agent 判断是否为浏览器请求，只有浏览器请求才会重定向到登录页，`curl` 默认返回 403。

### 4.4 商业功能裁剪

使用 `-tags community` 编译标志确保不包含商业模块。需要裁剪或禁用的模块包括：授权验证（License check）、计费/套餐管理（Fee/Plan）、多租户出租系统（User billing platform）、支付接口（Payment gateway）。开源版中这些功能本不存在，主要是确保不从被污染的上游合并进来。

### 4.5 上游同步策略

鉴于 GoEdge 的供应链安全事件，建议**暂停自动跟踪上游**，改为手动审查每个 commit 后再决定是否合并。建立以下 Git 工作流：以 `v1.3.9` 为 base 创建 `freecdn-main` 主开发分支，品牌定制独立维护在 `freecdn-branding` 分支，上游变更先在 `upstream-eval` 隔离分支评估（含代码安全审计）后再合并。使用 GitHub Actions 每周检查上游变更，但仅创建 Issue 通知，不自动 merge。

---

## 五、免费开源 CDN 建设路线图

### 近期目标（0-3 个月）

完成 FreeCDN 核心功能验证和文档建设，主要包括：修复 `install.sh` 中已知的 SQL 字段错误（`uniqueId`、`http` JSON 格式、`accessAddrs` 格式），基于官方 docker-compose 构建 FreeCDN 专属的 Docker 镜像，完善 `docs/INSTALL.md`、`docs/ARCHITECTURE.md`、`docs/FAQ.md` 三份核心文档，在 GitHub Actions 中实现自动构建 linux/amd64 和 linux/arm64 两个架构的二进制文件。

### 中期目标（3-6 个月）

推进 UI 现代化改造，参考 GoedgeWorks 的 aiFanCDN 模板，将 EdgeAdmin 前端升级为 Vue 3 + Element Plus 架构。开发批量操作功能（批量建站、批量 SSL）作为 FreeCDN 的差异化特性。建立社区机制，包括 CONTRIBUTING.md、issue 模板、PR 流程。

### 长期目标（6-12 个月）

探索基于 CoreDNS 实现智能 DNS 调度功能（弥补开源版缺失的 EdgeDNS 能力）。建立节点共享网络，允许社区成员贡献节点资源，形成去中心化的 CDN 网络。评估 Open Core 商业模式：核心功能永远开源，云托管版本可选付费。

---

## 六、开源策略与许可证建议

### 6.1 许可证选择

**推荐 Apache 2.0**，理由：与上游 BSD-3-Clause 完全兼容（BSD-3 代码可并入 Apache 2.0 项目），只需在 NOTICE 文件中保留 GoEdge 原始版权声明。相比 AGPL-3.0，Apache 2.0 对企业更友好，贡献门槛更低，有利于最大化社区参与度。Apache 2.0 包含专利授权条款，比 BSD-3 提供更强的专利保护。

若后期发现有商业实体搭便车闭源商业化，可参考 Elasticsearch 的做法切换到 AGPL-3.0。

### 6.2 社区建设建议

FreeCDN 的差异化定位应聚焦于三点：安全可信（相比被污染的官方版本，FreeCDN 明确锁定安全基线）、纯开源免费（不设付费功能墙）、中文社区友好（文档和讨论优先中文）。目标社区覆盖 NodeSeek、奶昔论坛（hostloc）、GitHub、V2EX 等中文 VPS/技术社区。

可持续运营方面，早期通过 GitHub Sponsors 和爱发电接受捐助，中期通过技术服务（部署咨询、定制开发）变现，长期探索与国内 VPS 服务商洽谈节点带宽赞助换品牌露出的合作模式。

---

## 七、竞品对比

| 方案 | 类型 | 许可证 | 部署难度 | 社区活跃度 | 适用场景 |
|------|------|--------|---------|-----------|---------|
| FreeCDN/GoEdge v1.3.9 | 自建完整 CDN | BSD-3/Apache 2.0 | 中 | 中（有安全事件背景）| 全功能自建 CDN |
| jsDelivr | 公共 CDN 服务 | MIT/Apache | 极低（SaaS）| 极高 | 仅限开源项目静态资源 |
| Nginx + Varnish | 自建基础 CDN | MIT/BSD | 高 | 极高 | 追求极致性能 |
| Caddy + 反向代理 | 简单自建 | Apache 2.0 | 低 | 高 | 单站点加速，HTTPS 自动化 |
| Cloudflare Workers | 边缘 CDN | 专有 | 低 | 极高 | 无自托管需求、厂商锁定可接受 |
| BunnyCDN | 商业 CDN | 专有 | 极低 | N/A | 低价商业需求（$0.01/GB）|

GoEdge 的核心优势在于提供完整的可视化管理界面、WAF 防护、多节点集群管理，是自建 CDN 中功能最完整的开源方案。主要竞争劣势是部署复杂度高于 Caddy 方案，且供应链安全事件的影响尚未完全消除。

---

## 八、关键技术参数速查

| 参数 | 值 |
|------|-----|
| 推荐版本 | v1.3.9（安全基线）|
| Go 最低版本 | 1.21 |
| MySQL 最低版本 | 5.7.8（推荐 8.0+）|
| EdgeAdmin 默认 Web 端口 | 7788 |
| EdgeAPI 默认 gRPC 端口 | 8001 |
| 上游开源协议 | BSD-3-Clause |
| FreeCDN 建议协议 | Apache 2.0 |
| edgeAPINodes 关键字段 | `uniqueId`, `http`(JSON), `accessAddrs`(JSON) |
| http JSON 关键格式 | `{"isOn":true,"listen":[{"protocol":"http","portRange":"8001"}]}` |
| 管理员密码存储 | MD5（非 bcrypt）|
| 支持数据库 | MySQL 5.7.8+, TiDB 3.0+（不支持 PostgreSQL/SQLite）|

---

## 九、结论

基于 GoEdge v1.3.9 构建 FreeCDN 是可行且有价值的路径。架构清晰、Go 技术栈成熟、功能完整，具备成为优秀开源 CDN 项目的基础条件。

最核心的执行建议有三点：第一，**安全优先**，锁定 v1.3.9 版本，对上游任何更新严格审计；第二，**降低门槛**，以 Docker 一键部署和完善的中文文档为核心竞争力；第三，**差异定位**，在 GoedgeWorks 的 UI 模板方向之外，FreeCDN 聚焦于"安全可信的完整系统"，而非资源集合。

FreeCDN 项目地址：https://github.com/hujiali30001/freecdn-admin

---

## 参考资源

1. [GitHub - TeaOSLab/EdgeAdmin（GoEdge 主仓库）](https://github.com/TeaOSLab/EdgeAdmin)
2. [GitHub - TeaOSLab/EdgeAPI（API 节点）](https://github.com/TeaOSLab/EdgeAPI)
3. [GitHub - TeaOSLab/EdgeNode（边缘节点）](https://github.com/TeaOSLab/EdgeNode)
4. [GitHub - TeaOSLab/EdgeCommon（公共库）](https://github.com/TeaOSLab/EdgeCommon)
5. [GitHub - Kuaien/GoedgeWorks（GoEdge UI/插件扩展）](https://github.com/Kuaien/GoedgeWorks)
6. [GoEdge 官方文档](https://goedge.cloud/docs)
7. [GoEdge 系统架构文档](https://goedge.cloud/docs/Architect.md)
8. [GoEdge API 认证文档](https://goedge.cloud/docs/API/Auth.md)
9. [GoEdge gRPC API 开发文档](https://goedge.cloud/docs/Developer/create-api.md)
10. [GoEdge 源码编译文档](https://goedge.cloud/docs/Developer/Build.md)
11. [GoEdge Vue 前端开发文档](https://goedge.cloud/docs/Developer/Vue.md)
12. [GoEdge 使用 Docker 安装文档](https://goedge.cloud/docs/Admin/install-docker-edge-instance.md)
13. [GoEdge 官方 docker-compose.yaml](https://goedge.cloud/docker/instance/compose.yaml)
14. [GoEdge 手动安装边缘节点](https://goedge.cloud/docs/Node/InstallManual.md)
15. [GoEdge 边缘节点性能优化](https://goedge.cloud/docs/Node/Performance.md)
16. [GoEdge 管理平台升级文档](https://goedge.rip/docs/Admin/Upgrade.md.html)
17. [GitHub - icodex/docker-goedge（社区 Docker 方案）](https://github.com/icodex/docker-goedge)
18. [GoEdge CDN v1.3.9 纯净版部署指南 - blog.vayki.com](https://blog.vayki.com/posts/140)
19. [自建CDN工具GoEdge遭官方投毒事件 - mastercdn.io](https://mastercdn.io/2025/03/19/%E8%87%AA%E5%BB%BAcdn%E5%B7%A5%E5%85%B7goedge%E9%81%AD%E5%AE%98%E6%96%B9%E6%8A%95%E6%AF%92%E4%BA%8B%E4%BB%B6/)
20. [疑似GoEdge被方能收购后官方投毒及解决方案 - vps.la](https://vps.la/2024/07/29/%e7%96%91%e4%bc%bcgoedge%e8%a2%ab%e6%96%b9%e8%83%bd%e6%94%b6%e8%b4%ad%e5%90%8e%e5%ae%98%e6%96%b9%e6%8a%95%e6%af%92%ef%bc%8c%e4%bb%a5%e5%8f%8a%e8%a7%a3%e5%86%b3%e6%96%b9%e6%a1%88/)
21. [GoEdge 投毒事件复盘 - linux.do](https://linux.do/t/topic/160500)
22. [BSD 3-Clause License - choosealicense.com](https://choosealicense.com/licenses/bsd-3-clause/)
23. [Apache License 2.0 - choosealicense.com](https://choosealicense.com/licenses/apache-2.0/)
24. [GNU AGPL v3.0 - choosealicense.com](https://choosealicense.com/licenses/agpl-3.0/)
25. [利用开源GoEdge零成本制作CDN系统 - 缙哥哥博客](https://www.dujin.org/21889.html)
26. [GoEdge 开源CDN技术栈分析 - 技术栈网](https://jishuzhan.net/article/1904705374144507905)
27. [About jsDelivr - 运营模式参考](https://www.jsdelivr.com/about)
28. [GitHub - hujiali30001/freecdn-admin（FreeCDN 项目仓库）](https://github.com/hujiali30001/freecdn-admin)
