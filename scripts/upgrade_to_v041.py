"""
升级服务器到 v0.4.1，并重新运行功能验收
"""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("134.175.67.168", username="ubuntu", password="REDACTED_SSH_PASS", timeout=30)

def run(cmd, timeout=120):
    _, out, err = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    stdout = out.read().decode()
    stderr = err.read().decode()
    return stdout + stderr

# 1. 停止服务
print("=== 停止服务 ===")
print(run("sudo systemctl stop freecdn-admin freecdn-api 2>&1 || true"))

# 2. 下载 v0.4.1 tar.gz
print("=== 下载 v0.4.1 ===")
out = run(
    "cd /tmp && rm -f freecdn-v0.4.1-linux-amd64.tar.gz && "
    "wget -q https://github.com/hujiali30001/freecdn-admin/releases/download/v0.4.1/freecdn-v0.4.1-linux-amd64.tar.gz -O freecdn-v0.4.1-linux-amd64.tar.gz && "
    "echo 'Download OK' || echo 'Download FAILED'",
    timeout=120
)
print(out)

# 3. 解压并替换二进制
print("=== 替换二进制 ===")
out = run(
    "cd /tmp && tar xzf freecdn-v0.4.1-linux-amd64.tar.gz && "
    "ls freecdn-v0.4.1-linux-amd64/ 2>&1"
)
print("tar contents:", out)

out = run(
    "cd /tmp/freecdn-v0.4.1-linux-amd64 && "
    "cp bin/edge-admin /usr/local/freecdn/edge-admin/bin/edge-admin && "
    "cp bin/edge-api   /usr/local/freecdn/edge-admin/edge-api/bin/edge-api && "
    "echo 'Copy OK' || echo 'Copy FAILED'"
)
print(out)

# 4. 重启服务
print("=== 重启服务 ===")
print(run("sudo systemctl start freecdn-api && sleep 5 && sudo systemctl start freecdn-admin && sleep 3"))

# 5. 检查服务状态
print("=== 服务状态 ===")
print(run("sudo systemctl is-active freecdn-admin freecdn-api 2>&1"))

ssh.close()
print("=== 升级完成 ===")
