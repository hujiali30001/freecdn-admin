"""
升级服务器到 v0.4.1 - 分步执行版（避免 SSH 读超时）
每步用短命令，下载用后台 nohup + 轮询
"""
import paramiko
import time
import sys

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"
VERSION = "v0.4.1"
ARCH = "amd64"
TARBALL = f"/tmp/freecdn-{VERSION}-linux-{ARCH}.tar.gz"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f"连接服务器 {HOST} ...")
ssh.connect(HOST, username=USER, password=PASS, timeout=30)
print("连接成功")

def run(cmd, timeout=30):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors="replace")
    e = err.read().decode(errors="replace")
    combined = (o + e).strip()
    print(combined if combined else "(no output)")
    return combined

# ── 1. 检查当前版本 ──────────────────────────────────────────────────────────
print("\n=== 当前版本 ===")
run("cat /usr/local/freecdn/edge-admin/VERSION 2>/dev/null || echo unknown")
run("sudo systemctl is-active freecdn-admin freecdn-api 2>&1")

# ── 2. 检查 tar 包是否已经存在（上次下载可能已成功）──────────────────────────
print("\n=== 检查本地缓存 ===")
check = run(f"test -f {TARBALL} && tar -tzf {TARBALL} >/dev/null 2>&1 && echo 'CACHED' || echo 'NOT_CACHED'")

if "CACHED" in check:
    print("tar 包已存在且完整，跳过下载")
    # 额外再校验一次确保完整
    verify = run(f"tar -tzf {TARBALL} >/dev/null 2>&1 && echo 'TAR_OK' || echo 'TAR_BAD'", timeout=15)
    if "TAR_BAD" in verify:
        print("WARNING: CACHED 包校验失败，强制重新下载")
        run(f"rm -f {TARBALL}", timeout=10)
        check = "NOT_CACHED"  # fall through to download

if "NOT_CACHED" in check:
    # ── 3. 后台下载（用 nohup，不等结果）──────────────────────────────────────
    print("\n=== 后台下载 v0.4.1 ===")
    # 先清理残留
    run(f"rm -f {TARBALL} /tmp/dl_exit_code /tmp/dl.log", timeout=10)
    MIRRORS = [
        f"https://gh-proxy.com/https://github.com/hujiali30001/freecdn-admin/releases/download/{VERSION}/freecdn-{VERSION}-linux-{ARCH}.tar.gz",
        f"https://ghfast.top/https://github.com/hujiali30001/freecdn-admin/releases/download/{VERSION}/freecdn-{VERSION}-linux-{ARCH}.tar.gz",
        f"https://github.com/hujiali30001/freecdn-admin/releases/download/{VERSION}/freecdn-{VERSION}-linux-{ARCH}.tar.gz",
    ]
    # 拼接 wget 命令：逐个尝试，成功即 break
    dl_cmds = " || ".join([
        f"wget -q --timeout=120 --tries=1 '{url}' -O {TARBALL}"
        for url in MIRRORS
    ])
    bg_cmd = f"nohup bash -c 'rm -f {TARBALL}; {dl_cmds}; echo $? > /tmp/dl_exit_code' > /tmp/dl.log 2>&1 &"
    run(bg_cmd)
    print("下载已在后台启动，轮询等待...")

    # 轮询最多 5 分钟
    for i in range(60):
        time.sleep(5)
        # 检查退出码文件
        status = run(f"cat /tmp/dl_exit_code 2>/dev/null || echo wait", timeout=10)
        if "wait" in status or not status:
            elapsed = (i+1)*5
            size_out = run(f"ls -lh {TARBALL} 2>/dev/null | awk '{{print $5}}' || echo 0", timeout=10)
            print(f"  等待中... {elapsed}s 已下载大小: {size_out}")
            continue
        code = status.strip().split()[-1]
        if code == "0":
            print("后台下载完成，退出码 0")
            break
        else:
            print(f"下载失败，退出码: {code}")
            run(f"cat /tmp/dl.log 2>/dev/null | tail -10")
            ssh.close()
            sys.exit(1)
    else:
        print("轮询超时（5分钟），查看日志：")
        run("cat /tmp/dl.log 2>/dev/null | tail -20")
        ssh.close()
        sys.exit(1)

# ── 4. 校验 tar 包 ────────────────────────────────────────────────────────────
print("\n=== 校验 tar 包 ===")
ok = run(f"tar -tzf {TARBALL} 2>&1 | head -5")
check2 = run(f"tar -tzf {TARBALL} >/dev/null 2>&1 && echo 'TAR_OK' || echo 'TAR_BAD'", timeout=15)
if "TAR_BAD" in check2:
    print("tar 包损坏，升级中止")
    ssh.close()
    sys.exit(1)

# ── 5. 解压 ──────────────────────────────────────────────────────────────────
print("\n=== 解压 ===")
EXTRACT_DIR = f"/tmp/freecdn-{VERSION}-linux-{ARCH}"
run(f"rm -rf {EXTRACT_DIR} && tar xzf {TARBALL} -C /tmp/ 2>&1 && echo 'UNTAR_OK'", timeout=30)
run(f"ls {EXTRACT_DIR}/ 2>&1")

# ── 6. 确定 binary 路径 ───────────────────────────────────────────────────────
check3 = run(f"test -f {EXTRACT_DIR}/edge-admin && echo HAS_ROOT || echo NOT_ROOT")
if "HAS_ROOT" in check3:
    ADMIN_BIN = f"{EXTRACT_DIR}/edge-admin"
    API_BIN   = f"{EXTRACT_DIR}/edge-api/bin/edge-api"
    print("FreeCDN Release 结构（binary 在根目录）")
else:
    ADMIN_BIN = f"{EXTRACT_DIR}/bin/edge-admin"
    API_BIN   = f"{EXTRACT_DIR}/edge-api/bin/edge-api"
    print("GoEdge zip 结构（binary 在 bin/ 子目录）")

# ── 7. 停止服务 ───────────────────────────────────────────────────────────────
print("\n=== 停止服务 ===")
run("sudo systemctl stop freecdn-admin freecdn-api 2>&1 || true")
time.sleep(2)

# ── 8. 替换二进制 ─────────────────────────────────────────────────────────────
print("\n=== 替换 edge-admin ===")
run(f"ls -lh {ADMIN_BIN} 2>&1")
run(f"sudo cp {ADMIN_BIN} /usr/local/freecdn/edge-admin/bin/edge-admin && sudo chmod +x /usr/local/freecdn/edge-admin/bin/edge-admin && echo 'edge-admin OK'")

print("\n=== 替换 edge-api ===")
api_exists = run(f"test -f {API_BIN} && echo 'api_exist' || echo 'api_miss'")
if "api_exist" in api_exists:
    run(f"sudo cp {API_BIN} /usr/local/freecdn/edge-admin/edge-api/bin/edge-api && sudo chmod +x /usr/local/freecdn/edge-admin/edge-api/bin/edge-api && echo 'edge-api OK'")
else:
    print("包中无 edge-api，保留当前版本")

# ── 9. 重启服务 ───────────────────────────────────────────────────────────────
print("\n=== 启动 freecdn-api ===")
run("sudo systemctl start freecdn-api 2>&1")
print("等待 8003 端口就绪...")
for i in range(15):
    time.sleep(2)
    r = run("nc -z -w2 127.0.0.1 8003 2>/dev/null && echo PORT_OPEN || echo PORT_CLOSED", timeout=10)
    if "PORT_OPEN" in r:
        print(f"  edge-api 就绪 (尝试 {i+1})")
        break
else:
    print("  警告：edge-api 8003 端口等待超时")

print("\n=== 启动 freecdn-admin ===")
run("sudo systemctl start freecdn-admin 2>&1")
time.sleep(4)

# ── 10. 验证 ─────────────────────────────────────────────────────────────────
print("\n=== 服务状态 ===")
run("sudo systemctl is-active freecdn-admin freecdn-api 2>&1")
run("sudo systemctl status freecdn-admin --no-pager -l 2>&1 | head -15")

print("\n=== 管理后台响应 ===")
run("curl -s -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:7788/ 2>&1")

print("\n=== 版本确认 ===")
run("cat /usr/local/freecdn/edge-admin/VERSION 2>/dev/null || echo 'no VERSION file'")

# 清理
run(f"rm -rf {EXTRACT_DIR} {TARBALL} /tmp/dl.log /tmp/dl_exit_code 2>/dev/null || true")

ssh.close()
print("\n=== 升级完成 ===")
