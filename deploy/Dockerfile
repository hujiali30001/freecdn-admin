# ==============================================================
# FreeCDN Admin + API 镜像
# 包含：edge-admin（管理后台）+ edge-api（内嵌，作为子进程）
#
# 构建命令（在项目根目录）：
#   docker build -f deploy/Dockerfile -t freecdn/admin:latest .
#
# 多架构构建（需要 buildx）：
#   docker buildx build --platform linux/amd64,linux/arm64 \
#     -f deploy/Dockerfile -t freecdn/admin:latest --push .
#
# 说明：
#   构建时直接从 goedge.rip 下载 GoEdge v1.3.9（安全基线版本），
#   无需在宿主机上预先编译二进制。
# ==============================================================

# ---- 构建阶段：下载并解压 GoEdge 二进制 ----
FROM debian:bookworm-slim AS downloader

ARG TARGETARCH=amd64
ARG GOEDGE_VERSION=v1.3.9

# 安装下载工具
RUN apt-get update -qq && apt-get install -y -qq wget unzip ca-certificates && rm -rf /var/lib/apt/lists/*

# 下载 GoEdge 全家桶（包含 edge-admin + edge-api + edge-node）
# 主源：goedge.rip（社区存档镜像，专门保存 v1.3.9 安全版本）
WORKDIR /tmp
RUN set -e; \
    ARCH="$(echo $TARGETARCH | sed 's/arm64/arm64/;s/amd64/amd64/')"; \
    URL="https://goedge.rip/dl/edge/${GOEDGE_VERSION}/edge-admin-linux-${ARCH}-plus-${GOEDGE_VERSION}.zip"; \
    echo "Downloading: ${URL}"; \
    wget -q --timeout=300 "${URL}" -O goedge.zip \
      || ( echo "Primary source failed, trying fallback..." && \
           wget -q --timeout=300 \
             "https://dl.goedge.cloud/edge/${GOEDGE_VERSION}/edge-admin-linux-${ARCH}-plus-${GOEDGE_VERSION}.zip" \
             -O goedge.zip ); \
    unzip -q goedge.zip -d /tmp/goedge-src; \
    rm goedge.zip

# 找到解压根目录（不同版本解压后目录层级可能不同）
RUN set -e; \
    if [ -d /tmp/goedge-src/edge-admin ]; then \
      mv /tmp/goedge-src/edge-admin /tmp/goedge; \
    else \
      mv /tmp/goedge-src /tmp/goedge; \
    fi; \
    chmod +x /tmp/goedge/bin/edge-admin /tmp/goedge/edge-api/bin/edge-api; \
    # 找出嵌套的 edge-node zip（供后续节点安装使用）\
    find /tmp/goedge/edge-api/deploy -name "*.zip" -type f 2>/dev/null | head -5 || true

# ---- 最终镜像 ----
FROM debian:bookworm-slim

# 安装运行时依赖
# netcat-openbsd：entrypoint 用于等待 MySQL 就绪
# default-mysql-client：entrypoint 用于数据库初始化
# ca-certificates + tzdata：标准依赖
RUN apt-get update -qq && apt-get install -y -qq \
    ca-certificates \
    tzdata \
    netcat-openbsd \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 工作目录：模拟 GoEdge 标准目录结构
WORKDIR /app/edge-admin

# 从 downloader 阶段复制 edge-admin 二进制和 web 资源
COPY --from=downloader /tmp/goedge/bin/edge-admin ./bin/edge-admin
COPY --from=downloader /tmp/goedge/web ./web
COPY --from=downloader /tmp/goedge/edge-api/bin/edge-api ./edge-api/bin/edge-api

# 复制 edge-node zip（供参考，用户可通过卷挂载访问）
COPY --from=downloader /tmp/goedge/edge-api/deploy ./edge-api/deploy

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

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -sf http://localhost:7788/ -H "Accept: text/html" > /dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
