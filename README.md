# FreeCDN

**一套命令自建 CDN，免费开源，无需购买商业服务。**

基于 [GoEdge](https://github.com/TeaOSLab/EdgeAdmin) 二次开发，保留全部 CDN 和 WAF 核心能力，去掉商业计费模块，加了一键安装脚本。一台 1 核 1G 的服务器就能跑起来。

---

## 快速开始

**第一步：安装管理节点**（新建一台 Linux 服务器）

```bash
curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash
```

安装完成后，浏览器访问 `http://你的服务器IP:7788`，完成初始化向导。

**第二步：添加边缘节点**（可以用另一台服务器，也可以同机）

在管理台 → 节点管理 → 添加节点，获取节点 ID 和密钥，然后在边缘节点服务器上执行：

```bash
curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash -s -- \
  --node \
  --api-endpoint http://管理节点IP:8001 \
  --node-id 你的节点ID \
  --node-secret 你的节点密钥
```

**第三步：添加网站，配置源站，开始加速。**

---

## 功能

HTTP/HTTPS/TCP/UDP 全协议代理，WAF，缓存，免费 SSL 证书自动申请续期，DNS 自动解析，IP 黑白名单，访问日志，带宽统计，多节点集群，WebSocket，URL 重写，限速限流，Gzip/Brotli 压缩。

---

## 系统要求

| 角色 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 管理节点（Admin + API + MySQL） | 1 核 1GB | 2 核 2GB |
| 边缘节点（Node） | 1 核 512MB | 1 核 1GB |

支持系统：Ubuntu 20.04+、Debian 11+、CentOS 7/8、Rocky Linux 8+  
支持架构：linux/amd64、linux/arm64（甲骨文免费 ARM 实例可用）

---

## 零成本方案

[甲骨文免费云](https://www.oracle.com/cloud/free/) 提供永久免费资源，足以跑一套完整的 FreeCDN：

- AMD64 实例 × 1（1 核 1GB）→ 管理节点
- ARM64 实例共 4 核 24GB，可拆分为 4 台 → 边缘节点

加上腾讯云 / 阿里云按量付费的国内节点，可以同时覆盖境内外流量。

---

## 文档

- [安装指南](docs/INSTALL.md)
- [架构说明](docs/ARCHITECTURE.md)
- [常见问题](docs/FAQ.md)

---

## 与 GoEdge 的关系

FreeCDN 是 GoEdge 社区版（BSD-3-Clause）的 Fork。上游版权归 [TeaOSLab](https://github.com/TeaOSLab) 所有，保留于 `NOTICE` 文件。FreeCDN 以 Apache 2.0 许可证发布，可商业使用。

如需企业级支持，参考 [GoEdge 官方版本](https://goedge.cloud)。
