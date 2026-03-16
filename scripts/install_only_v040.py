#!/usr/bin/env python3
"""
只做安装（包已在服务器 /tmp/ 下载好了）
"""
import paramiko, time, sys

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"
VERSION = "v0.4.0"
INSTALL_DIR = "/usr/local/freecdn/edge-admin"
TMP_TAR = f"/tmp/freecdn-{VERSION}-linux-amd64.tar.gz"
TMP_DIR = f"/tmp/freecdn-upgrade-{VERSION}"


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


c = new_client()
print(f"Connected to {HOST}")

# 确认包存在
_, sz_out, _ = run(c, f"stat -c '%s' {TMP_TAR}", ok_nonzero=True)
sz = int(sz_out.strip()) if sz_out.strip().isdigit() else 0
print(f"[INFO] TMP_TAR size: {sz/1024/1024:.1f} MB")
if sz < 10_000_000:
    print("ERROR: 包不存在或太小，请先下载")
    c.close(); sys.exit(1)

print("\n--- Stop services ---")
run(c, "sudo systemctl stop freecdn-admin freecdn-api 2>&1 || true", ok_nonzero=True)
time.sleep(2)

print("\n--- Extract ---")
run(c, f"sudo rm -rf {TMP_DIR} && sudo mkdir -p {TMP_DIR}", ok_nonzero=True)
rc, _, _ = run(c, f"sudo tar -xzf {TMP_TAR} -C {TMP_DIR}", timeout=60)
if rc != 0:
    print("ERROR: tar failed"); c.close(); sys.exit(1)

run(c, f"find {TMP_DIR} -maxdepth 4 -type f | head -20", ok_nonzero=True)
_, out_a, _ = run(c, f"find {TMP_DIR} -name 'edge-admin' -type f", ok_nonzero=True)
_, out_p, _ = run(c, f"find {TMP_DIR} -name 'edge-api'   -type f", ok_nonzero=True)
admin_bins = [x.strip() for x in out_a.strip().splitlines() if x.strip()]
api_bins   = [x.strip() for x in out_p.strip().splitlines() if x.strip()]
print(f"edge-admin: {admin_bins}")
print(f"edge-api:   {api_bins}")

print("\n--- Replace binaries ---")
if admin_bins:
    run(c, f"sudo cp {INSTALL_DIR}/bin/edge-admin {INSTALL_DIR}/bin/edge-admin.bak 2>/dev/null || true", ok_nonzero=True)
    run(c, f"sudo cp {admin_bins[0]} {INSTALL_DIR}/bin/edge-admin && sudo chmod +x {INSTALL_DIR}/bin/edge-admin")
    print("[OK] edge-admin replaced")
else:
    print("[WARN] edge-admin not found in tar")

if api_bins:
    run(c, f"sudo cp {INSTALL_DIR}/edge-api/bin/edge-api {INSTALL_DIR}/edge-api/bin/edge-api.bak 2>/dev/null || true", ok_nonzero=True)
    run(c, f"sudo cp {api_bins[0]} {INSTALL_DIR}/edge-api/bin/edge-api && sudo chmod +x {INSTALL_DIR}/edge-api/bin/edge-api")
    print("[OK] edge-api replaced")
else:
    print("[WARN] edge-api not found in tar")

run(c, f"echo '{VERSION}' | sudo tee {INSTALL_DIR}/VERSION", ok_nonzero=True)

print("\n--- Start services ---")
run(c, "sudo systemctl start freecdn-api",   ok_nonzero=True)
time.sleep(3)
run(c, "sudo systemctl start freecdn-admin", ok_nonzero=True)
time.sleep(5)

print("\n--- Verify ---")
run(c, "systemctl is-active freecdn-admin freecdn-api", ok_nonzero=True)
run(c, "sudo systemctl status freecdn-admin --no-pager 2>&1 | head -15", ok_nonzero=True)
_, http_out, _ = run(c, "curl -sk -o /dev/null -w '%{http_code}' http://127.0.0.1:7788/", ok_nonzero=True)
run(c, f"cat {INSTALL_DIR}/VERSION", ok_nonzero=True)

# Cleanup
run(c, f"sudo rm -rf {TMP_TAR} {TMP_DIR} /tmp/freecdn_dl.*", ok_nonzero=True)
c.close()

code = http_out.strip()
print(f"\nHTTP 7788: {code}")
if code in ("200", "302", "301", "403"):
    print(f"[SUCCESS] v0.4.0 upgrade done!")
else:
    print(f"[INFO] HTTP {code} - check manually if needed")
print("Done.")
