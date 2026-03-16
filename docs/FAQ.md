# FreeCDN 常见问题

## 目录

- [安装问题](#安装问题)
- [配置与初始化](#配置与初始化)
- [边缘节点](#边缘节点)
- [性能与缓存](#性能与缓存)
- [证书与 HTTPS](#证书与-https)
- [运维与故障排查](#运维与故障排查)
- [上游同步与升级](#上游同步与升级)

---

## 安装问题

### Q: 安装脚本报错 "请使用 root 用户运行"

需要以 root 身份执行：

```bash
sudo bash <(curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh)
# 或者
sudo su -
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash
```

### Q: 国内服务器 GitHub 下载很慢或超时

安装脚本内置了镜像站加速，会自动探测最快的镜像（ghfast.top、gh-proxy.com、mirror.ghproxy.com 等）然后下载，无需手动干预。

如果脚本本身拉取就很慢，用镜像站的 URL 来获取脚本：

```bash
# 推荐：用镜像站拉取脚本
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash
```

如果所有镜像都失败，可以手动下载后上传到服务器：

```bash
# 从 Release 页面手动下载
wget https://github.com/hujiali30001/freecdn-admin/releases/download/v0.2.0/freecdn-v0.2.0-linux-amd64.tar.gz
# 上传到目标服务器
scp freecdn-v0.2.0-linux-amd64.tar.gz root@YOUR_SERVER:/tmp/freecdn-pkg.tar.gz
# 然后在服务器上执行 install.sh，脚本会自动检测到已存在的包，跳过下载
```

### Q: 甲骨文 ARM64 实例应该下载哪个版本？

甲骨文免费 ARM64 实例（Ampere A1）架构为 `aarch64`，对应 `arm64` 版本：

```bash
curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash
# 安装脚本会自动检测架构，无需手动指定
```

### Q: CentOS 7 安装报错

CentOS 7 默认 bash 版本较旧，建议升级或改用 CentOS 8 / Rocky Linux 8 / Ubuntu 20.04+。

如果必须用 CentOS 7，先升级 bash：
```bash
yum install -y centos-release-scl
yum install -y devtoolset-8-bash
```

---

## 配置与初始化

### Q: 访问 7788 端口显示空白或无法连接

**检查步骤：**

1. 确认服务正在运行：
   ```bash
   systemctl status freecdn-admin freecdn-api
   ```

2. 确认端口监听正常：
   ```bash
   ss -tlnp | grep -E '7788|8001'
   ```

3. 检查防火墙：
   ```bash
   # Ubuntu/Debian
   ufw status
   ufw allow 7788/tcp

   # CentOS/Rocky
   firewall-cmd --list-all
   firewall-cmd --permanent --add-port=7788/tcp && firewall-cmd --reload
   ```

4. 甲骨文云需要**同时**配置 iptables 和 OCI 控制台的安全列表（两者缺一不可）。

### Q: 初始化向导中填写数据库信息后报 "连接失败"

```bash
# 检查 MySQL 是否正在运行
systemctl status mysql

# 测试连接
mysql -u freecdn -p freecdn
```

如果 MySQL 刚安装，Ubuntu 默认使用 `auth_socket` 认证，root 账号免密登录，但 freecdn 用户需要用密码登录。安装脚本完成后会在终端打印自动生成的密码，请注意保存。

### Q: 初始化向导 API 节点填什么？

- **API 节点 Host**：`0.0.0.0`（让 EdgeAPI 监听所有网卡，边缘节点才能连接）
- **API 节点 Port**：`8001`（默认值）

如果管理台和 API 在同一台服务器，`localhost` 也可以，但这样边缘节点无法从外部连接 API。

---

## 边缘节点

### Q: 添加边缘节点后节点一直显示"离线"

**常见原因：**

1. **边缘节点无法连接 API**：确认管理节点 8001 端口对边缘节点服务器 IP 开放：
   ```bash
   # 在边缘节点服务器上测试
   curl -v http://管理节点IP:8001
   ```

2. **节点 ID / Secret 填错**：在管理台重新复制节点安装命令，注意不要有多余的空格。

3. **节点服务未启动**：
   ```bash
   systemctl status freecdn-node
   journalctl -u freecdn-node -n 50
   ```

4. **配置文件路径错误**：确认 `/usr/local/freecdn/edge-node/configs/api_node.yaml` 内容正确。

### Q: 边缘节点 ARM64 编译时报 CGO 相关错误

EdgeNode 包含 C 代码（TOA 模块），交叉编译 ARM64 时需要安装交叉编译器：

```bash
apt-get install -y gcc-aarch64-linux-gnu
export CC=aarch64-linux-gnu-gcc
export CGO_ENABLED=1
export GOARCH=arm64
go build -tags community ./cmd/edge-node/
```

### Q: 边缘节点部署在国内，加速域名要备案吗？

如果边缘节点服务器在**中国大陆境内**，源站域名和加速域名都需要在工信部完成 ICP 备案，否则服务器运营商会封禁 80/443 端口。使用香港、日本、韩国等境外节点则无需备案。

---

## 性能与缓存

### Q: 修改了源站内容但 CDN 仍返回旧内容

EdgeNode 按配置的 TTL 缓存响应。手动刷新方式：

1. 管理台 → 刷新预热 → 提交 URL 或目录刷新
2. 或者降低域名缓存配置中的 TTL（临时调低后刷新）

### Q: EdgeNode 缓存存在哪里？磁盘占用增长很快

缓存默认存在 `/usr/local/freecdn/edge-node/caches/` 目录（或 Docker 挂载路径）。可以在管理台的"节点缓存"配置中：
- 设置最大磁盘占用上限
- 配置缓存清理策略（LRU）
- 手动清空全部缓存

### Q: 并发请求高时 EdgeNode 有连接数限制吗？

安装脚本已在 systemd 配置中设置 `LimitNOFILE=1000000`（单进程最大文件描述符数），通常足够。如需进一步调优，参考系统级内核参数：

```bash
# 临时生效
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# 永久生效（写入 /etc/sysctl.conf）
echo "net.core.somaxconn=65535" >> /etc/sysctl.conf
sysctl -p
```

---

## 证书与 HTTPS

### Q: 如何为 CDN 域名配置 HTTPS？

有两种方式，推荐先用方式一（简单），遇到问题再考虑方式二（更通用）：

**方式一：管理台 UI 一键申请（HTTP-01 验证）**

1. 管理台 → 证书管理 → 申请证书（Let's Encrypt ACME 自动申请）
2. 填写域名，选择「HTTP-01 验证」，确保该域名的 A 记录已指向边缘节点 IP
3. 确认边缘节点 80 端口对公网开放，点击申请
4. 成功后在「HTTP 服务 → 对应域名 → HTTPS」中启用并选择证书

**方式二：certbot + DNS-01 验证（无需开放 80 端口）**

适合腾讯云/阿里云等安全组默认不开放 80 端口的场景。详见 [安装指南 → 配置 HTTPS 证书](./INSTALL.md#配置-https-证书)。

### Q: 我没有域名，能用 HTTPS 吗？

Let's Encrypt 不支持裸 IP，必须有域名才能申请证书。

推荐使用 **DuckDNS**（https://www.duckdns.org）申请免费子域名，格式为 `你的名字.duckdns.org`，注册即用，整个过程 2 分钟。DuckDNS 还支持 DNS-01 验证，可以完全绕过端口 80 限制。

具体步骤见 [安装指南 → 方案二：certbot + DuckDNS DNS-01 验证](./INSTALL.md#方案二certbot--duckdns-dns-01-验证无需开放-80-端口)。

### Q: 申请证书时提示「连接被重置」或「Connection reset by peer」

这是典型的**安全组/防火墙挡住了 80 端口**的症状。Let's Encrypt HTTP-01 验证时会从外部访问 `http://你的域名/.well-known/acme-challenge/...`，如果服务器的安全组或 iptables 没有放行 80 端口，连接就会被 reset。

解决方案有两个：

1. 在云控制台的**安全组**中添加入站规则放行 TCP 80（注意：服务器本机 ufw 和云安全组是两套规则，两个都要改）
2. 改用 **DNS-01 验证**，完全不依赖 80 端口（推荐，见上一条）

### Q: 申请证书时报「DNS 解析失败」或「Could not resolve host」

域名 A 记录还没生效。检查步骤：

```bash
# 从外部验证 DNS 是否已生效（不要用 localhost，要用公共 DNS）
nslookup 你的域名 8.8.8.8
# 或
dig 你的域名 @1.1.1.1
```

如果结果显示的 IP 不是你的边缘节点 IP，说明 DNS 还没传播完成。DuckDNS 更新通常 30 秒内生效；如果是自购域名，TTL 可能需要等几分钟到几小时。

### Q: certbot 安装了但提示「找不到 dns-duckdns 插件」

snap 安装的 certbot 需要显式连接插件：

```bash
sudo snap install certbot-dns-duckdns
sudo snap set certbot trust-plugin-with-root=ok
sudo snap connect certbot:plugin certbot-dns-duckdns

# 验证插件已加载
certbot plugins | grep duckdns
```

### Q: 证书申请成功了，但 curl 访问还是显示 HTTP 而不是 HTTPS

证书申请和启用是两步操作。申请完成后还需要：

1. 管理台 → 证书管理，确认证书状态为"正常"
2. 进入对应 HTTP 服务 → HTTPS 标签页 → 启用 HTTPS，选择刚申请的证书
3. 在服务配置中确认有监听 443 端口的规则（或让边缘节点自动监听）

然后再用 `curl -v https://你的域名/` 测试。

### Q: curl 测试显示 TLS 握手成功但 HTTP/2 没有升级，只有 HTTP/1.1

HTTP/2 需要服务端开启 ALPN h2 协商。FreeCDN/GoEdge 默认启用 HTTP/2，如果看到 HTTP/1.1，可能是：

- 客户端没有发送 ALPN（老版本 curl）：`curl --http2 -v https://你的域名/`
- 服务端配置中 HTTP/2 被手动关闭：管理台 → HTTP 服务 → HTTPS 配置 → 确认 HTTP/2 开关已启用

### Q: 可以上传自定义证书（如阿里云/腾讯云购买的证书）吗？

可以。管理台 → 证书管理 → 上传证书，将 PEM 格式的证书（fullchain）和私钥粘贴进去即可。

注意：上传的证书需要是完整链（包含中间 CA 证书），不要只上传服务器证书，否则部分客户端会报「证书链不完整」。

### Q: 证书快到期了但没有自动续期

检查 certbot 定时任务是否正常：

```bash
# snap 安装的 certbot
sudo systemctl status snap.certbot.renew.timer

# apt 安装的 certbot
sudo systemctl status certbot.timer
# 或
sudo crontab -l | grep certbot
```

如果使用管理台申请的证书，续期由 EdgeAdmin 内置任务处理，可以在「任务管理」页面查看续期任务状态。

---

## 运维与故障排查

### Q: 服务启动后日志在哪里看？

```bash
# 实时查看管理台日志
journalctl -u freecdn-admin -f

# 查看 API 节点日志
journalctl -u freecdn-api -f

# 查看边缘节点日志
journalctl -u freecdn-node -f

# 查看最近 100 行
journalctl -u freecdn-admin -n 100 --no-pager
```

文件日志位于 `/var/log/freecdn/`（如果配置了文件输出）或 `/usr/local/freecdn/*/logs/`。

### Q: 如何重启 / 停止 / 更新服务？

```bash
# 重启
systemctl restart freecdn-api freecdn-admin
systemctl restart freecdn-node  # 边缘节点

# 停止
systemctl stop freecdn-admin freecdn-api

# 查看状态
systemctl status freecdn-admin freecdn-api freecdn-node
```

### Q: 管理台密码忘了怎么办？

通过数据库直接重置：

```bash
# 进入 MySQL
mysql -u root freecdn

# 查询管理员账号
SELECT id, username FROM edge_admins;

# 生成新密码哈希（SHA512 + 盐，GoEdge 格式）
# 建议用管理台"重置密码"功能，或联系数据库管理员

# 如果实在无法登录，可临时禁用密码验证（开发环境）
```

更简单的方式：如果有数据库访问权限，通过管理台的"忘记密码"页面（`/dashboard/init`）重新初始化。

### Q: 数据库备份建议

```bash
# 每日自动备份（加到 crontab）
0 3 * * * mysqldump -u root freecdn | gzip > /var/backups/freecdn-$(date +%Y%m%d).sql.gz

# 保留最近 7 天
find /var/backups/ -name "freecdn-*.sql.gz" -mtime +7 -delete
```

---

## 上游同步与升级

### Q: 如何手动同步上游 GoEdge 更新？

```bash
bash scripts/upstream-sync.sh
```

或手动操作：

```bash
cd src/EdgeAdmin
git fetch upstream
git merge upstream/main
# 解决冲突后
go build -tags community ./...
```

### Q: 升级 FreeCDN 版本

1. 查看 [Release 页面](https://github.com/hujiali30001/freecdn-admin/releases) 确认新版本变更
2. 备份数据库
3. 重新运行安装脚本（`--reinstall` 参数会覆盖已有安装）：
   ```bash
   curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash -s -- --reinstall
   ```
4. 重启服务

### Q: FreeCDN 和 GoEdge 商业版有什么区别？

FreeCDN 基于 GoEdge **社区版**（开源部分）开发，不包含 GoEdge 商业版的付费功能（如多租户计费系统、商业支持）。FreeCDN 做了品牌化和简化，去掉了计费相关菜单，核心 CDN 和 WAF 功能完整保留。

如果你需要商业支持或企业级功能，可以考虑 [GoEdge 官方版本](https://goedge.cloud)。

### Q: 可以商业使用 FreeCDN 吗？

可以。FreeCDN 采用 Apache 2.0 许可证，允许商业使用、修改和分发，但需要保留原始版权声明（参见 `NOTICE` 文件）。上游 GoEdge 采用 BSD-3-Clause 许可证，版权归 TeaOSLab 所有。
