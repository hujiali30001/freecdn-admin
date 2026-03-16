import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "134.175.67.168"
PORT = 22
USER = "ubuntu"
PASSWORD = "FreeCDN2026!"

def run(client, cmd, timeout=20):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, PORT, USER, PASSWORD, timeout=15)
print("SSH OK")

# 服务起来了，等 20 秒让心跳充分触发
print("等 20 秒...")
time.sleep(20)

print("\n=== 20 秒后完整日志（tail -30）===")
out, _ = run(client, "sudo tail -30 /usr/local/freecdn/edge-admin/logs/run.log 2>&1", timeout=10)
print(out)

# 测试登录接口
print("\n=== 测试 7788 端口 ===")
out, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:7788/ 2>&1", timeout=10)
print(out)

client.close()
