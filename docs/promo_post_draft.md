# 推广帖草稿

> 适用平台：V2EX（节点：分享创造）/ Linux.do  
> 风格：直接、有料、不装，避免广告腔

---

## 标题（二选一）

- **「自建 CDN，一条命令，免费开源」—— FreeCDN v0.1.9 发布**
- **GoEdge 投毒事件后，我 Fork 了一个干净版本**

---

## 正文

去年 7 月 GoEdge v1.4.0/v1.4.1 被植入恶意 JS，劫持了用 GoEdge 搭 CDN 的网站的访客流量。这件事很多人知道，但 GoEdge v1.3.9 之前的版本其实是干净的，功能也相当完整：HTTP/HTTPS 代理、WAF、多节点集群、Let's Encrypt 自动证书、缓存刷新、访问统计……该有的都有。

我 Fork 了 v1.3.9，做了三件事：

**1. 彻底品牌化，去掉计费模块**  
GoEdge 社区版残留了不少商业版的 UI 痕迹（套餐、授权、计费菜单），全部删掉。纯 CDN 工具，没有任何付费功能墙。

**2. 一键安装脚本**  
不需要看 GoEdge 文档，也不需要手动配数据库。一条命令装好管理节点，第二条命令接入边缘节点：

```bash
# 管理节点（国内服务器推荐）
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash

# 边缘节点（装完管理节点后，在边缘服务器上跑）
curl -sSL ... | sudo bash -s -- --node --api-endpoint http://管理节点IP:8003 --node-id xxx --node-secret xxx
```

**3. 锁版本 + 上游安全审计**  
永远基于 v1.3.9，上游每周自动扫新 tag，有新版本时创建 Issue 等人工审查，不自动合并。

---

**实测验证过的功能（截至 v0.1.9）：**

- 干净 Ubuntu 22.04 端到端安装，全程约 3 分钟
- Docker Compose 一键部署（含 MySQL 自动初始化）
- 边缘节点接入（install.sh --node 端到端跑通）
- HTTPS 全链路：DuckDNS 免费域名 + Let's Encrypt DNS-01 验证 + TLS 1.3 + HTTP/2

---

**零成本部署方案：**

甲骨文永久免费套餐（A1 ARM 共 4 核 24GB + AMD 微型实例 2 台）完全够用。AMD 实例跑管理节点，ARM 实例拆成 4 台跑边缘节点，加上腾讯云按量计费国内节点，境内外都覆盖，全程零费用。

---

**为什么做这个而不是直接推荐 GoEdge v1.3.9？**

v1.3.9 的安装方式对新手不友好，文档分散，而且商业版 UI 残留让人困惑。FreeCDN 的目标是让没用过 GoEdge 的人也能 10 分钟内跑起来一套 CDN。

---

GitHub：https://github.com/hujiali30001/freecdn-admin  
文档：https://github.com/hujiali30001/freecdn-admin/blob/main/docs/install.md

有问题欢迎开 Issue，或者直接回帖。

---

## 发帖注意事项

- **V2EX**：发在「分享创造」节点，标题里带上「开源」「免费」关键词，正文不要太长，直接贴核心功能 + GitHub 链接
- **Linux.do**：可以把 GoEdge 投毒事件背景写得更详细，这个社区对这件事比较熟悉，可以直接引用相关帖子
- **发帖时间**：工作日上午 10 点前或晚上 9-11 点曝光最高

---

## 备选更短版本（适合 Twitter/X 或微博）

> 自建 CDN 从没这么简单过：一条 curl 命令装管理节点，一条命令接边缘节点，Let's Encrypt 证书自动申请，全程不需要看文档。基于 GoEdge v1.3.9（投毒事件之前最后一个干净版本），Apache 2.0 开源，永久免费。
> 
> https://github.com/hujiali30001/freecdn-admin
