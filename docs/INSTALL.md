# FreeCDN 安装指南

## 目录

- [系统要求](#系统要求)
- [方案一：Docker 一键部署（推荐）](#方案一docker-一键部署推荐)
- [方案二：一键脚本安装](#方案二一键脚本安装)
- [添加边缘节点](#添加边缘节点)
- [完成初始化向导](#完成初始化向导)
- [甲骨文免费云零成本部署](#甲骨文免费云零成本部署)

---

## 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 管理节点 (Admin+API+MySQL) | 1 核 1GB | 2 核 2GB |
| 边缘节点 (Node) | 1 核 512MB | 1 核 1GB |
| 操作系统 | Ubuntu 20.04 / Debian 11 / CentOS 7 | Ubuntu 22.04 LTS |
| 架构 | linux/amd64 或 linux/arm64 | - |
| 开放端口 | 管理节点: 7788, 8001 / 边缘节点: 80, 443 | - |

---

## 方案一：Docker 一键部署（推荐）

适合：有 Docker 环境、希望快速验证的用户。

```bash
# 1. 克隆仓库
git clone https://github.com/hujiali30001/freecdn-admin.git
cd freecdn-admin

# 2. 创建配置文件
cp deploy/.env.example deploy/.env
# 编辑 .env，修改数据库密码
nano deploy/.env

# 3. 启动服务
docker compose -f deploy/docker-compose.yml up -d

# 4. 查看启动状态
docker compose -f deploy/docker-compose.yml ps
docker compose -f deploy/docker-compose.yml logs -f edge-admin

# 5. 访问管理台
# http://你的服务器IP:7788
```

### 防火墙配置

```bash
# Ubuntu/Debian (ufw)
ufw allow 7788/tcp  # 管理台（建议只对自己 IP 开放）
ufw allow 8001/tcp  # API 节点（边缘节点需要连接此端口）
ufw allow 80/tcp    # HTTP（边缘节点）
ufw allow 443/tcp   # HTTPS（边缘节点）

# CentOS/Rocky (firewalld)
firewall-cmd --permanent --add-port=7788/tcp
firewall-cmd --permanent --add-port=8001/tcp
firewall-cmd --reload
```

---

## 方案二：一键脚本安装

适合：Linux 服务器，无 Docker 环境。

**国内服务器（推荐，镜像加速）：**
```bash
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | bash
```

**GitHub 直连（境外服务器或镜像不可用时）：**
```bash
curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | bash
```

安装脚本会自动探测最快的下载镜像，国内服务器下载速度通常在 5-20 MB/s，安装全程约 2-5 分钟。安装完成后按提示访问管理台完成向导。

---

## 添加边缘节点

管理台初始化完成后，按以下步骤添加边缘节点：

### 方法一：远程 SSH 安装（最简单）

1. 管理台 → 节点管理 → 添加节点
2. 填写边缘服务器的 SSH 地址、端口、用户名、密码
3. 点击"一键安装"，等待安装完成

### 方法二：Docker 手动安装

在边缘节点服务器上执行：

```bash
# 从管理台"节点 > 安装"页面获取以下三个参数
ENDPOINTS="http://管理节点IP:8001"
CLUSTERID="集群ID"
SECRET="节点密钥"

docker run -d \
  --name freecdn-node \
  --network host \
  --restart always \
  -e ENDPOINTS="$ENDPOINTS" \
  -e CLUSTERID="$CLUSTERID" \
  -e SECRET="$SECRET" \
  -v /var/lib/freecdn/node/configs:/usr/local/freecdn/edge-node/configs \
  -v /var/lib/freecdn/node/caches:/usr/local/freecdn/edge-node/caches \
  ghcr.io/hujiali30001/freecdn-node:latest
```

### 方法三：二进制手动安装

```bash
# 1. 从 FreeCDN Releases 下载对应架构的包
# amd64 (x86_64)
wget https://github.com/hujiali30001/freecdn-admin/releases/download/v0.1.0/freecdn-v0.1.0-linux-amd64.tar.gz
# arm64（甲骨文 ARM 实例）
# wget https://github.com/hujiali30001/freecdn-admin/releases/download/v0.1.0/freecdn-v0.1.0-linux-arm64.tar.gz

tar xzf freecdn-v0.1.0-linux-amd64.tar.gz
FREECDN_DIR=$(tar tf freecdn-v0.1.0-linux-amd64.tar.gz | head -1 | cut -d/ -f1)
mkdir -p /usr/local/freecdn/edge-node
cp "${FREECDN_DIR}/edge-api/deploy/"edge-node-linux-amd64-*.zip /tmp/edge-node.zip
unzip /tmp/edge-node.zip -d /tmp/edge-node-src
NODE_BIN=$(find /tmp/edge-node-src -name edge-node -type f | head -1)
cp "$NODE_BIN" /usr/local/freecdn/edge-node/edge-node
chmod +x /usr/local/freecdn/edge-node/edge-node

# 2. 配置节点
cd /usr/local/freecdn/edge-node
# 编辑 configs/api_node.yaml，填写 endpoints、clusterId、secret
# 从管理台「节点管理 → 安装」页面复制这三个参数

# 3. 注册为系统服务
./edge-node service install
systemctl enable --now edge-node
```

---

## 完成初始化向导

首次访问 `http://服务器IP:7788` 会进入初始化向导：

1. **设置 API 节点**
   - API 节点 Host: `0.0.0.0`（监听所有网卡）
   - API 节点 Port: `8001`

2. **配置数据库**
   - Host: `mysql`（Docker 部署）或 `127.0.0.1`
   - Port: `3306`
   - Database: `freecdn`（或 `.env` 中设置的值）
   - User/Password: 与 `.env` 中一致

3. **创建管理员账号**
   - 设置用户名和密码

4. **完成**，自动跳转到控制台

---

## 甲骨文免费云零成本部署

甲骨文 (Oracle Cloud) 的永久免费资源足以运行完整的 FreeCDN：

| 资源 | 规格 | 用途 |
|------|------|------|
| AMD64 实例 x2 | 各 1 核 1GB | 其中一台运行管理节点 |
| ARM64 实例 | 共 4 核 24GB（可分配为 4 台各 1 核 6GB） | 边缘节点 |

申请地址：https://www.oracle.com/cloud/free/

**注意**：甲骨文免费实例默认安全规则较严，需要在"安全列表"中手动开放端口，不仅要改防火墙，还要改 VCN 安全规则。

```bash
# 甲骨文 ARM64 实例开放端口（同时需要在控制台安全规则中放行）
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
iptables -I INPUT -p tcp --dport 443 -j ACCEPT
iptables -I INPUT -p tcp --dport 7788 -j ACCEPT
iptables -I INPUT -p tcp --dport 8001 -j ACCEPT
# 持久化规则
apt-get install -y iptables-persistent
netfilter-persistent save
```
