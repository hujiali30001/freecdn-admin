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
#   构建时从 FreeCDN GitHub Releases 下载预编译包（已完成品牌替换）。
#   国内环境会依次尝试 ghfast.top / mirror.ghproxy.com / gh.llkk.cc 等加速镜像。
#   如需手动指定镜像前缀：
#   docker build --build-arg FREECDN_MIRROR=https://你的镜像 ...
# ==============================================================

# ---- 构建阶段：下载并解压 FreeCDN Release 包 ----
FROM debian:bookworm-slim AS downloader

ARG TARGETARCH=amd64
ARG FREECDN_VERSION=v0.1.6
ARG GITHUB_REPO=hujiali30001/freecdn-admin

# 安装下载工具
RUN apt-get update -qq && apt-get install -y -qq wget ca-certificates && rm -rf /var/lib/apt/lists/*

# 下载 FreeCDN Release 包（含品牌替换后的 web/）
# 可通过 --build-arg FREECDN_MIRROR=https://你的镜像 覆盖镜像前缀
ARG FREECDN_MIRROR=https://ghfast.top
WORKDIR /tmp
RUN ARCH="${TARGETARCH}"; \
    TAR="freecdn-${FREECDN_VERSION}-linux-${ARCH}.tar.gz"; \
    BASE="https://github.com/${GITHUB_REPO}/releases/download/${FREECDN_VERSION}"; \
    \
    echo "==> Downloading FreeCDN ${FREECDN_VERSION} (${ARCH})..."; \
    DOWNLOADED=0; \
    for URL in \
      "${FREECDN_MIRROR}/https://github.com/${GITHUB_REPO}/releases/download/${FREECDN_VERSION}/${TAR}" \
      "https://gh.llkk.cc/https://github.com/${GITHUB_REPO}/releases/download/${FREECDN_VERSION}/${TAR}" \
      "https://mirror.ghproxy.com/${BASE}/${TAR}" \
      "${BASE}/${TAR}"; \
    do \
      echo "  Trying: ${URL}"; \
      if wget -q --timeout=120 "${URL}" -O freecdn.tar.gz 2>/dev/null && [ -s freecdn.tar.gz ]; then \
        SZ=$(wc -c < freecdn.tar.gz); \
        echo "  OK (${SZ} bytes)"; \
        DOWNLOADED=1; \
        break; \
      else \
        rm -f freecdn.tar.gz; \
        echo "  Failed, trying next..."; \
      fi; \
    done; \
    if [ "${DOWNLOADED}" != "1" ]; then echo "All download sources failed!" && exit 1; fi; \
    \
    echo "==> Extracting..."; \
    mkdir -p /tmp/freecdn-src; \
    tar -xzf freecdn.tar.gz -C /tmp/freecdn-src; \
    rm freecdn.tar.gz; \
    \
    # 包解压后根目录是 freecdn-VERSION-linux-ARCH/
    # 找到该目录并重命名为 /tmp/freecdn
    EXTRACTED=$(ls /tmp/freecdn-src/ | head -1); \
    echo "Extracted root: ${EXTRACTED}"; \
    mv "/tmp/freecdn-src/${EXTRACTED}" /tmp/freecdn; \
    \
    # edge-admin 二进制在根目录（不在 bin/ 子目录）
    # 为了让 COPY 指令路径统一，创建 bin/ 目录并移动过去
    mkdir -p /tmp/freecdn/bin; \
    if [ -f /tmp/freecdn/edge-admin ]; then \
      mv /tmp/freecdn/edge-admin /tmp/freecdn/bin/edge-admin; \
    fi; \
    \
    chmod +x /tmp/freecdn/bin/edge-admin; \
    chmod +x /tmp/freecdn/edge-api/bin/edge-api; \
    echo "==> Contents:"; \
    ls -lh /tmp/freecdn/bin/ /tmp/freecdn/edge-api/bin/ 2>/dev/null || true

# ---- 最终镜像 ----
FROM debian:bookworm-slim

# 安装运行时依赖
# netcat-openbsd：entrypoint 用于等待 MySQL 就绪
# default-mysql-client：entrypoint 用于数据库初始化
# curl + python3：entrypoint auto-setup 和健康检查使用
# ca-certificates + tzdata：标准依赖
RUN apt-get update -qq && apt-get install -y -qq \
    ca-certificates \
    tzdata \
    netcat-openbsd \
    default-mysql-client \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# 工作目录
WORKDIR /app/edge-admin

# 从 downloader 阶段复制二进制和 web 资源（品牌替换版）
COPY --from=downloader /tmp/freecdn/bin/edge-admin        ./bin/edge-admin
COPY --from=downloader /tmp/freecdn/edge-api/bin/edge-api ./edge-api/bin/edge-api
COPY --from=downloader /tmp/freecdn/web                   ./web

# 复制 edge-api 部署资源（node zip 等，供参考）
COPY --from=downloader /tmp/freecdn/edge-api/deploy       ./edge-api/deploy

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
# 必须加浏览器 User-Agent，否则 GoEdge 安全中间件会返回 403
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD curl -sf -A "Mozilla/5.0 (compatible; HealthCheck)" http://localhost:7788/ > /dev/null 2>&1 || exit 1

LABEL org.opencontainers.image.title="FreeCDN Admin" \
      org.opencontainers.image.description="FreeCDN management panel with EdgeAPI" \
      org.opencontainers.image.source="https://github.com/hujiali30001/freecdn-admin" \
      org.opencontainers.image.version="${FREECDN_VERSION}"

ENTRYPOINT ["/entrypoint.sh"]
