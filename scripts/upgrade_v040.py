#!/usr/bin/env python3
"""
升级服务器到 v0.4.0
策略：nohup 后台下载 + 短命令轮询，避免 SSH 长连接超时断开
"""
import paramiko, time, sys

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"
VERSION = "v0.4.0"
INSTALL_DIR = "/usr/local/freecdn/edge-admin"
TMP_TAR  = f"/tmp/freecdn-{VERSION}-linux-amd64.tar.gz"
TMP_DIR  = f"/tmp/freecdn-upgrade-{VERSION}"
DL_LOG   = "/tmp/freecdn_dl.log"
DL_DONE  = "/tmp/freecdn_dl.done"
DL_FAIL  = "/tmp/freecdn_dl.fail"

MIRRORS = [
    "https://ghfast.top/https://github.com/hujiali30001/freecdn-admin",
    "https://mirror.ghproxy.com/https://github.com/hujiali30001/freecdn-admin",
    "https://gh-proxy.com/https://github.com/hujiali30001/freecdn-admin",
]


def new_client():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=15, banner_timeout=15)
    c.get_transport().set_keepalive(20)
    return c


def run(c, cmd, timeout=30, ok_nonzero=False):
    print(f"$ {cmd}")
    _, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    rc  = stdout.channel.recv_exit_status()
    if out.strip(): print(out.rstrip())
    if err.strip(): print(f"[STDERR] {err[:300].rstrip()}")
    if rc != 0 and not ok_nonzero:
        print(f"[WARN] exit={rc}")
    return rc, out, err


# ── Step 1: 查当前版本 ─────────────────────────────────────────────
print("=== 1. 当前版本 ===")
c = new_client()
run(c, f"cat {INSTALL_DIR}/VERSION 2>/dev/null || echo unknown", ok_nonzero=True)
run(c, f"ls -lh {INSTALL_DIR}/bin/edge-admin {INSTALL_DIR}/edge-api/bin/edge-api 2>/dev/null", ok_nonzero=True)
c.close()

# ── Step 2: 后台异步下载 ───────────────────────────────────────────
print("\n=== 2. 后台下载 v0.4.0 ===")
c = new_client()
run(c, f"rm -f {DL_LOG} {DL_DONE} {DL_FAIL} {TMP_TAR}", ok_nonzero=True)

# 构造多镜像 fallback 的 shell 片段
cmds = []
for m in MIRRORS:
    url = f"{m}/releases/download/{VERSION}/freecdn-{VERSION}-linux-amd64.tar.gz"
    cmds.append(f"curl -fsSL -m 400 --retry 2 -o {TMP_TAR} '{url}' 2>>{DL_LOG} && echo OK:{url} >> {DL_LOG} && touch {DL_DONE} && exit 0")
body = " || ".join(cmds) + f" || (echo ALLFAIL >> {DL_LOG} && touch {DL_FAIL})"
nohup_cmd = f"nohup bash -c '{body}' >> {DL_LOG} 2>&1 &"
run(c, nohup_cmd, ok_nonzero=True)
c.close()
print("[INFO] 下载已在服务器后台启动，开始轮询...")

# ── Step 3: 轮询等待下载完成 ───────────────────────────────────────
max_wait = 600
interval = 20
elapsed  = 0
download_ok = False

while elapsed < max_wait:
    time.sleep(interval)
    elapsed += interval
    try:
        c = new_client()
        _, done_out, _ = run(c, f"test -f {DL_DONE} && echo DONE || echo WAIT", ok_nonzero=True)
        _, fail_out, _ = run(c, f"test -f {DL_FAIL} && echo FAIL || echo OK",  ok_nonzero=True)
        _, sz_out,   _ = run(c, f"stat -c '%s' {TMP_TAR} 2>/dev/null || echo 0", ok_nonzero=True)
        sz = int(sz_out.strip()) if sz_out.strip().isdigit() else 0
        print(f"[{elapsed}s] 进度: {sz/1024/1024:.1f} MB  状态: {done_out.strip()}/{fail_out.strip()}")
        c.close()
        if "DONE" in done_out:
            download_ok = True
            break
        if "FAIL" in fail_out:
            c2 = new_client()
            run(c2, f"cat {DL_LOG}", ok_nonzero=True)
            c2.close()
            print("ERROR: 所有镜像下载均失败")
            sys.exit(1)
    except Exception as e:
        print(f"[连接错误 {elapsed}s] {e}，稍后重试...")
        time.sleep(5)

if not download_ok:
    print("ERROR: 下载超时（>10min），请检查服务器网络")
    sys.exit(1)
print("[OK] 下载完成")

# ── Step 4-8: 安装 ────────────────────────────────────────────────
c = new_client()

_, sz_out, _ = run(c, f"stat -c '%s' {TMP_TAR}", ok_nonzero=True)
sz = int(sz_out.strip()) if sz_out.strip().isdigit() else 0
print(f"\n[INFO] 包大小: {sz/1024/1024:.1f} MB")
if sz < 10_000_000:
    print("ERROR: 包太小，可能损坏，退出")
    c.close(); sys.exit(1)

print("\n=== 4. 停止服务 ===")
run(c, "sudo systemctl stop freecdn-admin freecdn-api 2>&1 || true", ok_nonzero=True)
time.sleep(2)

print("\n=== 5. 解压 ===")
run(c, f"sudo rm -rf {TMP_DIR} && sudo mkdir -p {TMP_DIR}", ok_nonzero=True)
rc, _, _ = run(c, f"sudo tar -xzf {TMP_TAR} -C {TMP_DIR}", timeout=60)
if rc != 0:
    print("ERROR: 解压失败"); c.close(); sys.exit(1)
run(c, f"find {TMP_DIR} -maxdepth 4 -type f | head -20", ok_nonzero=True)

_, out_a, _ = run(c, f"find {TMP_DIR} -name 'edge-admin' -type f", ok_nonzero=True)
_, out_p, _ = run(c, f"find {TMP_DIR} -name 'edge-api'   -type f", ok_nonzero=True)
admin_bins = [x.strip() for x in out_a.strip().splitlines() if x.strip()]
api_bins   = [x.strip() for x in out_p.strip().splitlines() if x.strip()]
print(f"[INFO] edge-admin: {admin_bins}")
print(f"[INFO] edge-api:   {api_bins}")

print("\n=== 6. 替换二进制 ===")
if admin_bins:
    run(c, f"sudo cp {INSTALL_DIR}/bin/edge-admin {INSTALL_DIR}/bin/edge-admin.bak 2>/dev/null || true", ok_nonzero=True)
    run(c, f"sudo cp {admin_bins[0]} {INSTALL_DIR}/bin/edge-admin && sudo chmod +x {INSTALL_DIR}/bin/edge-admin")
    print("[OK] edge-admin 已替换")
else:
    print("[WARN] 未找到 edge-admin")

if api_bins:
    run(c, f"sudo cp {INSTALL_DIR}/edge-api/bin/edge-api {INSTALL_DIR}/edge-api/bin/edge-api.bak 2>/dev/null || true", ok_nonzero=True)
    run(c, f"sudo cp {api_bins[0]} {INSTALL_DIR}/edge-api/bin/edge-api && sudo chmod +x {INSTALL_DIR}/edge-api/bin/edge-api")
    print("[OK] edge-api 已替换")
else:
    print("[WARN] 未找到 edge-api")

run(c, f"echo '{VERSION}' | sudo tee {INSTALL_DIR}/VERSION", ok_nonzero=True)

print("\n=== 7. 启动服务 ===")
run(c, "sudo systemctl start freecdn-api",   ok_nonzero=True)
time.sleep(3)
run(c, "sudo systemctl start freecdn-admin", ok_nonzero=True)
time.sleep(5)

print("\n=== 8. 验证 ===")
run(c, "systemctl is-active freecdn-admin freecdn-api", ok_nonzero=True)
run(c, "sudo systemctl status freecdn-admin --no-pager 2>&1 | head -12", ok_nonzero=True)
_, http_out, _ = run(c, "curl -sk -o /dev/null -w '%{http_code}' http://127.0.0.1:7788/", ok_nonzero=True)
run(c, f"cat {INSTALL_DIR}/VERSION", ok_nonzero=True)
print(f"\n[HTTP] 7788 响应码: {http_out.strip()}")

run(c, f"sudo rm -rf {TMP_TAR} {TMP_DIR} {DL_LOG} {DL_DONE} {DL_FAIL}", ok_nonzero=True)
c.close()

code = http_out.strip()
if code in ("200", "302", "301", "403"):
    print(f"\n[SUCCESS] v0.4.0 upgrade done! HTTP {code}")
else:
    print(f"\n[INFO] HTTP {code}, service may still be starting")
print("完成。")
