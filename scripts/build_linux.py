#!/usr/bin/env python3
"""
编译 edge-admin Linux amd64 binary 并通过 SSH 部署到服务器
"""
import subprocess, os, sys, paramiko, stat

GO_EXE   = r'C:\Go_temp\go\bin\go.exe'
REPO     = r'C:\Users\Administrator\.workbuddy\FreeCDN'
OUT_BIN  = os.path.join(REPO, 'dist', 'edge-admin-linux-amd64')
SRV_HOST = os.environ.get('SSH_HOST', '134.175.67.168')
SRV_USER = os.environ.get('SSH_USER', 'ubuntu')
SRV_PASS = os.environ.get('SSH_PASS', '')
REMOTE   = '/home/edgeadmin/edge-admin'   # 服务器上安装路径

if not SRV_PASS:
    print("ERROR: SSH_PASS environment variable is not set.")
    print("  Windows: set SSH_PASS=yourpassword")
    sys.exit(1)

os.makedirs(os.path.join(REPO, 'dist'), exist_ok=True)

# ── 1. 编译 ────────────────────────────────────────────────────────────────────
print("[build] Compiling edge-admin linux/amd64 ...")
env = dict(os.environ)
env.update({
    'HTTP_PROXY':  'http://127.0.0.1:4780',
    'HTTPS_PROXY': 'http://127.0.0.1:4780',
    'GOPATH': r'C:\Users\Administrator\go',
    'GOOS':   'linux',
    'GOARCH': 'amd64',
    'CGO_ENABLED': '0',
    'GOFLAGS': '-mod=mod',
    'GOPROXY': 'https://proxy.golang.org,direct',
})

r = subprocess.run(
    [GO_EXE, 'build', '-trimpath', '-ldflags=-s -w',
     '-o', OUT_BIN, './cmd/edge-admin'],
    cwd=REPO, env=env,
    capture_output=True, text=True, timeout=300
)
if r.stdout: print(r.stdout[:800])
if r.stderr: print(r.stderr[:800])
if r.returncode != 0:
    print(f"[build] FAILED (rc={r.returncode})")
    sys.exit(1)
size_mb = os.path.getsize(OUT_BIN) / 1024 / 1024
print(f"[build] OK  -> {OUT_BIN}  ({size_mb:.1f} MB)")

# ── 2. 上传并重启 ────────────────────────────────────────────────────────────────
print(f"\n[deploy] Uploading to {SRV_HOST}:{REMOTE} ...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.WarningPolicy())  # 固定服务器，WarningPolicy 代替 AutoAddPolicy
ssh.connect(SRV_HOST, username=SRV_USER, password=SRV_PASS, timeout=30)

def run(cmd, t=30):
    _, o, e = ssh.exec_command(cmd, timeout=t)
    out = (o.read().decode(errors='replace') + e.read().decode(errors='replace')).strip()
    return out

# 找实际安装位置
install_path = run("which edge-admin 2>/dev/null || find /home /usr/local -name 'edge-admin' -type f 2>/dev/null | head -1")
if install_path:
    REMOTE = install_path.strip().split('\n')[0]
    print(f"[deploy] Found edge-admin at: {REMOTE}")
else:
    print(f"[deploy] edge-admin not in PATH, using {REMOTE}")

# 停服务
print("[deploy] Stopping edge-admin service ...")
out = run("sudo systemctl stop edge-admin 2>&1 || sudo supervisorctl stop edge-admin 2>&1 || true")
print(f"  {out[:200]}")

# 备份
bak = REMOTE + '.bak'
run(f"sudo cp -f {REMOTE} {bak} 2>/dev/null || true")

# 上传
sftp = ssh.open_sftp()
tmp_path = '/tmp/edge-admin-new'
sftp.put(OUT_BIN, tmp_path)
sftp.chmod(tmp_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
sftp.close()
print(f"[deploy] Uploaded to {tmp_path}")

# 替换
out = run(f"sudo cp -f {tmp_path} {REMOTE} && sudo chmod +x {REMOTE} && echo OK")
print(f"[deploy] Copy: {out}")

# 重启
print("[deploy] Starting edge-admin service ...")
out = run("sudo systemctl start edge-admin 2>&1 || sudo supervisorctl start edge-admin 2>&1 || true")
print(f"  {out[:200]}")

import time
time.sleep(3)

# 验证是否启动
out = run("curl -sk -o /dev/null -w '%{http_code}' http://127.0.0.1:7788/csrf/token 2>&1")
print(f"[deploy] Health check (CSRF token): HTTP {out}")

out2 = run("sudo systemctl status edge-admin --no-pager -l 2>&1 | head -20 || "
           "sudo supervisorctl status edge-admin 2>&1 | head -5")
print(f"[deploy] Service status:\n{out2}")

ssh.close()
print("\n[deploy] Done!")
