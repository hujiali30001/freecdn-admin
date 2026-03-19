# FreeCDN

**一条命令自建 CDN，免费开源，完全自托管。**

基于 GoEdge v1.3.9 二次开发，保留完整的 CDN + WAF 能力，去掉商业计费模块，更新 UI 界面，并与上游发布渠道切割，实现完全自主可控。一台 1 核 1GB 服务器就能跑起来。

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Based on GoEdge](https://img.shields.io/badge/based%20on-GoEdge%20v1.3.9-green.svg)](docs/ARCHITECTURE.md)

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

离线或弱网环境请参考 [离线/私有源安装](docs/INSTALL.md#离线私有源安装)。

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
# 账号密码：使用 deploy/.env 中配置的 ADMIN_USERNAME / ADMIN_PASSWORD
```

WSL 本地快速启动（避免本机 7788/8003 端口冲突）：

```bash
bash deploy/run-wsl.sh
```

脚本会自动打印 Windows 与 WSL 可访问地址，默认可访问：`http://127.0.0.1:17788`

也可以覆盖默认参数：

```bash
ADMIN_PASSWORD=你的密码 ADMIN_PORT=17788 API_PORT=18003 bash deploy/run-wsl.sh
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

## 为什么不用 GoEdge 官方版本？

**2024 年 7 月，GoEdge v1.4.0 和 v1.4.1 的 EdgeNode 被植入了恶意代码。** 具体表现为：EdgeNode 会在代理的网页响应中自动注入第三方 JavaScript，绕过用户配置直接劫持访客流量，将流量重定向至攻击者控制的广告系统。受影响的 CDN 运营者在不知情的情况下向终端用户投放了第三方广告。

事件被中文技术社区曝光后引发大量讨论（参见：[Linux.do 投毒事件复盘](https://linux.do/t/topic/160500)）。GoEdge 官方随后发布了 v1.4.2 声称修复，但已有相当一部分社区用户永久失去信任。

**FreeCDN 的应对策略：**

- **版本锁定**：基于 v1.3.9，这是恶意代码植入前最后一个干净版本，也是中文社区公认的安全基线
- **不自动跟踪上游**：v1.4.x 及以后的所有版本，必须经过逐行代码审计后才会考虑合并，永远不会自动同步
- **定期人工审计**：定期审查上游关键变更，只选择安全且必要的改动合入
- **供应链透明**：从源码编译，三个依赖仓库（EdgeAdmin、EdgeAPI、EdgeCommon）均为自有 Fork，不依赖 GoEdge 官方的分发渠道

### 治理模型（简版）

```
上游变更情报（仅输入）
        │
        ▼
安全审计与差异评估
        │
        ▼
FreeCDN 内部实现 / 选择性合并
        │
        ▼
FreeCDN 版本发布（唯一输出）
```

完整版本治理和发布说明见：[系统架构](docs/ARCHITECTURE.md) 与 [常见问题](docs/FAQ.md#版本治理与发布)。

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
