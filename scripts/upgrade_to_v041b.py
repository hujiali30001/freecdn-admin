"""
升级服务器到 v0.4.1（分步执行，超时宽松）
"""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("134.175.67.168", username="ubuntu", password="FreeCDN2026!", timeout=30)

def run(cmd, timeout=180):
    print(f"$ {cmd[:80]}...")
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode()
    stderr = err.read().decode()
    if stdout.strip():
        print("  OUT:", stdout[:500])
    if stderr.strip():
        print("  ERR:", stderr[:300])
    print(f"  RC: {rc}")
    return rc, stdout

# 1. 检查当前 edge-api 版本文件
run("cat /usr/local/freecdn/edge-admin/VERSION 2>/dev/null || echo 'no VERSION'")

# 2. 下载 v0.4.1（用 curl，更快）
print("\n=== 下载 v0.4.1 ===")
rc, _ = run(
    "curl -L --retry 3 -o /tmp/freecdn-v041.tar.gz "
    "https://github.com/hujiali30001/freecdn-admin/releases/download/v0.4.1/freecdn-v0.4.1-linux-amd64.tar.gz "
    "&& echo 'Download OK'",
    timeout=180
)

# 3. 解压
print("\n=== 解压 ===")
rc, out = run("cd /tmp && tar xzf freecdn-v041.tar.gz && ls freecdn-v0.4.1-linux-amd64/bin/ 2>&1")

# 4. 停止服务、替换二进制、重启
print("\n=== 热更新 ===")
run("sudo systemctl stop freecdn-admin freecdn-api 2>&1 || true")
run("cp /usr/local/freecdn/edge-admin/bin/edge-admin /usr/local/freecdn/edge-admin/bin/edge-admin.bak")
run("cp /tmp/freecdn-v0.4.1-linux-amd64/bin/edge-admin /usr/local/freecdn/edge-admin/bin/edge-admin")
run("cp /tmp/freecdn-v0.4.1-linux-amd64/bin/edge-api   /usr/local/freecdn/edge-admin/edge-api/bin/edge-api")
run("sudo systemctl start freecdn-api")
time.sleep(5)
run("sudo systemctl start freecdn-admin")
time.sleep(3)

# 5. 检查状态
print("\n=== 状态 ===")
run("sudo systemctl is-active freecdn-admin freecdn-api")
run("sudo systemctl status freecdn-api --no-pager -n 5 2>&1 | tail -10")

ssh.close()
print("\n=== 完成 ===")
