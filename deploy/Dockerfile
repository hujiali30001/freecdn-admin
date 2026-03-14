# ==============================================================
# FreeCDN Admin + API 镜像
# 包含：edge-admin（管理后台）+ edge-api（内嵌，作为子进程）
#
# 构建命令（在项目根目录）：
#   docker build -f deploy/Dockerfile -t freecdn/admin:latest .
#
# 构建要求：
#   先在 WSL 里编译好二进制：
#     bash scripts/build.sh
#   然后在 Windows 下构建 Docker 镜像（或在 WSL 里 docker buildx build）
# ==============================================================

FROM debian:bookworm-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    ca-certificates \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 工作目录：模拟 GoEdge 标准目录结构
WORKDIR /app/edge-admin

# 复制 edge-admin 二进制
COPY goedge/edge-admin/bin/edge-admin ./bin/edge-admin
RUN chmod +x ./bin/edge-admin

# 复制 edge-admin 前端静态文件
COPY goedge/edge-admin/web ./web

# 复制 edge-api 到 edge-admin 子目录（GoEdge 标准部署结构）
COPY goedge/edge-api/bin/edge-api ./edge-api/bin/edge-api
RUN chmod +x ./edge-api/bin/edge-api

# 创建必要目录
RUN mkdir -p \
    ./configs \
    ./logs \
    ./edge-api/configs \
    ./edge-api/logs \
    ./edge-api/data

# 复制 entrypoint 脚本
COPY deploy/docker-entrypoint-admin.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 设置时区
ENV TZ=Asia/Shanghai

# 暴露端口
# 7788: 管理后台 Web
# 8003: EdgeAPI RPC（边缘节点连接用）
EXPOSE 7788 8003

ENTRYPOINT ["/entrypoint.sh"]
