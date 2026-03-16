# FreeCDN Docker 部署指南

本文档说明如何用 Docker Compose 部署 FreeCDN。

---

## 快速开始

### 前置条件

- Docker 20.10+
- Docker Compose v2（`docker compose` 命令可用）
- 开放防火墙端口：7788（管理后台）、8003（EdgeAPI，边缘节点连接用）

### 部署步骤

```bash
# 1. 克隆仓库
git clone https://github.com/hujiali30001/freecdn-admin.git
cd freecdn-admin

# 2. 复制环境变量配置文件并修改密码
cp deploy/.env.example deploy/.env
# 建议至少修改 MYSQL_PASSWORD 和 ADMIN_PASSWORD
nano deploy/.env

# 3. 构建镜像（首次构建会从 FreeCDN GitHub Releases 下载预编译包，约需 2-5 分钟）
docker compose -f deploy/docker-compose.yml build

# 4. 启动
docker compose -f deploy/docker-compose.yml up -d

# 5. 查看启动日志，等待初始化完成（首次启动约需 60 秒）
docker compose -f deploy/docker-compose.yml logs -f freecdn-admin
```

初始化完成后，访问 `http://你的服务器IP:7788`，使用以下默认账号登录：

- 用户名：`admin`（或 `.env` 中 `ADMIN_USERNAME` 的值）
- 密码：`FreeCDN2026!`（或 `.env` 中 `ADMIN_PASSWORD` 的值）

---

## 添加边缘节点

边缘节点默认不随管理节点一起启动（因为需要先获取节点 ID 和密钥）。

### 步骤

1. 登录管理后台 → 集群 → 节点 → 添加节点
2. 复制节点的 `uniqueId` 和 `secret`
3. 编辑 `deploy/.env`，填入：
   ```
   API_ENDPOINTS=http://你的管理节点IP:8003
   NODE_ID=你复制的节点uniqueId
   NODE_SECRET=你复制的节点secret
   ```
4. 启动边缘节点：
   ```bash
   docker compose -f deploy/docker-compose.yml --profile node up -d freecdn-node
   ```

> 边缘节点使用 `network_mode: host`，直接监听宿主机的 80/443 端口。如果宿主机这两个端口已被占用（如 Nginx），需要先停掉占用进程。

---

## 配置说明

所有配置通过 `deploy/.env` 文件管理（从 `.env.example` 复制）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | `freecdn_root_2026` | MySQL root 密码，建议修改 |
| `MYSQL_PASSWORD` | `freecdn_pass_2026` | FreeCDN 用户密码，建议修改 |
| `ADMIN_PASSWORD` | `FreeCDN2026!` | 管理后台初始密码，建议修改 |
| `ADMIN_PORT` | `7788` | 管理后台端口 |
| `API_PORT` | `8003` | EdgeAPI RPC 端口 |
| `TZ` | `Asia/Shanghai` | 时区 |

---

## 常用操作

```bash
# 查看状态
docker compose -f deploy/docker-compose.yml ps

# 查看管理节点日志
docker compose -f deploy/docker-compose.yml logs -f freecdn-admin

# 重启管理节点
docker compose -f deploy/docker-compose.yml restart freecdn-admin

# 停止所有服务
docker compose -f deploy/docker-compose.yml down

# 完全重置（删除所有数据，重新初始化）
docker compose -f deploy/docker-compose.yml down -v
```

---

## 数据持久化

所有数据通过 Docker 卷持久化，位于以下卷中：

| 卷名 | 内容 |
|------|------|
| `mysql_data` | MySQL 数据库文件 |
| `admin_configs` | edge-admin 配置文件（含自动生成的 nodeId/secret） |
| `admin_logs` | edge-admin 日志 |
| `api_logs` / `api_data` | edge-api 日志和数据 |
| `node_configs` | edge-node 配置 |
| `node_caches` | edge-node 缓存文件 |

备份数据：
```bash
# 备份 MySQL
docker exec freecdn-mysql mysqldump -u root -pfreecdn_root_2026 freecdn > backup.sql

# 备份配置卷
docker run --rm -v freecdn_admin_configs:/data -v $(pwd):/backup alpine tar czf /backup/admin_configs.tar.gz -C /data .
```

---

## 多架构支持

FreeCDN 镜像支持 linux/amd64 和 linux/arm64，可在甲骨文免费 ARM 实例上运行：

```bash
# 多架构构建（需要 docker buildx）
docker buildx build --platform linux/amd64,linux/arm64 \
  -f deploy/Dockerfile -t freecdn/admin:latest --push .
```

---

## 故障排查

**容器启动后访问 7788 端口没有响应**

首次启动需要下载二进制并初始化数据库，约需 60-90 秒。查看日志确认进度：
```bash
docker compose -f deploy/docker-compose.yml logs -f freecdn-admin
```

**MySQL 连接失败**

检查 MySQL 容器是否正常运行：
```bash
docker compose -f deploy/docker-compose.yml ps
docker compose -f deploy/docker-compose.yml logs mysql
```

**edge-api 启动失败（no listening address）**

这通常是 `edgeAPINodes` 表中 `http` 字段的 `protocol` 为空字符串导致的。运行以下命令修复：
```bash
docker exec freecdn-mysql mysql -ufreecdn -pfreecdn_pass_2026 freecdn -e \
  "UPDATE edgeAPINodes SET http='{\"isOn\":true,\"listen\":[{\"protocol\":\"http\",\"host\":\"\",\"portRange\":\"8003\",\"description\":\"\"}]}' WHERE id=1;"
docker compose -f deploy/docker-compose.yml restart freecdn-admin
```

**edge-api 报 "wrong token role, expect: api, but give admin"**

`api_admin.yaml` 格式不正确，或者 token 对不上。正确的格式是嵌套写法：
```yaml
rpc:
  endpoints:
    - "http://127.0.0.1:8003"
nodeId: "你的nodeId"
secret: "你的secret"
```

删除 `admin_configs` 卷重新初始化即可（entrypoint 会自动生成正确格式）：
```bash
docker compose -f deploy/docker-compose.yml down
docker volume rm freecdn_admin_configs
docker compose -f deploy/docker-compose.yml up -d
```

---

**重置初始化（已有数据但想重新初始化）**

删除 `admin_configs` 卷，下次启动会重新初始化：
```bash
docker compose -f deploy/docker-compose.yml down
docker volume rm freecdn_admin_configs
docker compose -f deploy/docker-compose.yml up -d
```
