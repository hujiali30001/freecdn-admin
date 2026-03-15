# FreeCDN

**一条命令自建 CDN，免费开源，完全自托管。**

基于 [GoEdge](https://github.com/TeaOSLab/EdgeAdmin) v1.3.9 二次开发，保留完整的 CDN + WAF 能力，去掉商业计费模块，增加一键安装脚本和 Docker 支持。一台 1 核 1GB 服务器就能跑起来。

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Based on GoEdge](https://img.shields.io/badge/based%20on-GoEdge%20v1.3.9-green.svg)](https://github.com/TeaOSLab/EdgeAdmin)

---

## 快速开始

### 方式一：脚本安装（推荐）

**第一步：安装管理节点**（Linux 服务器，需要 root 权限）

```bash
# 国内服务器（镜像加速，推荐）
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash

# 境外服务器 / 镜像不可用时
curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash
```

安装完成后，脚本会直接输出管理后台地址和初始账号密码，用浏览器访问即可。

**第二步：添加边缘节点**

在管理台 → 集群 → 节点 → 添加节点，获取节点 ID 和密钥，然后在边缘节点服务器上执行：

```bash
# 国内服务器
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash -s -- \
  --node \
  --api-endpoint http://管理节点IP:8003 \
  --node-id 你的节点ID \
  --node-secret 你的节点密钥
```

**第三步：添加网站，配置源站，开始加速。**

---

### 方式二：Docker Compose

```bash
# 1. 克隆仓库（推荐直连，ghproxy 类加速有时会丢文件）
git clone https://github.com/hujiali30001/freecdn-admin.git
cd freecdn-admin

# 2. 复制并编辑配置（修改密码等）
cp deploy/.env.example deploy/.env

# 3. 构建并启动
docker compose -f deploy/docker-compose.yml build
docker compose -f deploy/docker-compose.yml up -d

# 4. 等约 60 秒后访问管理后台
# 默认地址：http://localhost:7788
# 默认账号：admin / REDACTED_SSH_PASS
```

**国内服务器提速建议**

`docker build` 过程会从 GitHub 下载约 200MB 的软件包，构建脚本已内置多个国内加速源，一般无需额外配置。如果 `docker pull` 基础镜像（debian/mysql）也很慢，可以配置 Docker 镜像加速：

```bash
# 编辑 /etc/docker/daemon.json（没有则新建）
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://dockerpull.org",
    "https://hub.rat.dev"
  ]
}
EOF
sudo systemctl daemon-reload && sudo systemctl restart docker
```

配置完成后重新执行 `docker compose build`。

---

## 功能

- **全协议代理**：HTTP / HTTPS / HTTP3 / TCP / UDP / WebSocket
- **内容缓存**：磁盘缓存 + 内存缓存，支持缓存刷新
- **WAF 防护**：SQL 注入、XSS、CC/DDoS 防护、IP 黑白名单、人机验证
- **免费 SSL 证书**：ACME 协议自动申请 Let's Encrypt 证书并续期
- **多节点集群**：统一管理多台边缘节点，配置自动下发
- **访问统计**：实时带宽、请求量、缓存命中率等
- **负载均衡**：轮询 / 加权 / IP Hash 等多种算法
- **其他**：URL 重写、限速限流、Gzip/Brotli 压缩、访问日志

---

## 系统要求

| 角色 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 管理节点（Admin + API + MySQL） | 1 核 1GB | 2 核 2GB |
| 边缘节点（Node） | 1 核 512MB | 1 核 1GB |

支持系统：Ubuntu 20.04+、Debian 11+、CentOS 7/8、Rocky Linux 8+、AlmaLinux 8+  
支持架构：linux/amd64、linux/arm64

---

## 零成本搭建方案

[甲骨文云永久免费套餐](https://www.oracle.com/cloud/free/)可以完整跑起一套 FreeCDN：

- AMD64 微型实例 × 1（1 核 1GB）→ 管理节点
- ARM A1 实例共 4 核 24GB，最多拆分为 4 台 → 边缘节点

加上腾讯云 / 阿里云按量付费国内节点，可同时覆盖境内外流量，全程零费用。

---

## 安全说明

FreeCDN **锁定使用 GoEdge v1.3.9**，不跟踪 v1.4.0 及以上版本。

2024 年 7 月，GoEdge v1.4.0/v1.4.1 的 EdgeNode 被植入恶意 JS 注入代码，导致大量网站流量被劫持。中文技术社区普遍推荐以 v1.3.9 作为安全基线。FreeCDN 基于此版本，并在合并任何上游更新前进行严格的代码安全审计。

参考：[GoEdge 投毒事件复盘](https://linux.do/t/topic/160500)

---

## 文档

- [安装指南](docs/INSTALL.md)
- [系统架构](docs/ARCHITECTURE.md)
- [常见问题](docs/FAQ.md)
- [Docker 部署](deploy/README.md)

---

## 与 GoEdge 的关系

FreeCDN 是 GoEdge 社区版（BSD-3-Clause）的 Fork。上游版权归 [TeaOSLab](https://github.com/TeaOSLab) 所有，保留于 [NOTICE](NOTICE) 文件。FreeCDN 以 Apache-2.0 许可证发布，允许商业使用。

---

## License

Apache-2.0 © FreeCDN Contributors  
本项目基于 GoEdge（BSD-3-Clause），见 [NOTICE](NOTICE)。
