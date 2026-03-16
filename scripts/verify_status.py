import paramiko
import sys
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '134.175.67.168'
port = 22
username = 'ubuntu'
password = 'REDACTED_SSH_PASS'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=username, password=password, timeout=15)

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

print('=== Test HTTP response ===')
out, _ = run("curl -sf -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' -o /dev/null -w 'HTTP:%{http_code} Final:%{url_effective}' http://localhost:7788/ 2>&1")
print(out)

print('\n=== Test login page content ===')
out, _ = run("curl -s -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' http://localhost:7788/ 2>&1 | head -30")
print(out)

print('\n=== Check /root/.edge-admin/ ===')
out, _ = run('docker exec freecdn-admin ls -la /root/.edge-admin/ 2>&1')
print(out)

print('\n=== edge-api port ===')
out, _ = run('docker exec freecdn-admin sh -c "cat /proc/net/tcp6 2>/dev/null | awk \'NR>1{print $2,$4}\' | grep -i \'1F43\\|1F4B\' || echo checking..." ')
# 8003 in hex = 0x1F43, 8001 = 0x1F41
out2, _ = run('docker exec freecdn-admin sh -c "grep -i 1f43 /proc/net/tcp6 2>/dev/null | head -5 || grep -i 1f43 /proc/net/tcp 2>/dev/null | head -5"')
print('Port 8003 (hex 1f43):', out2)

print('\n=== Container health ===')
out, _ = run('docker inspect freecdn-admin --format "Health={{.State.Health.Status}} Running={{.State.Running}}"')
print(out.strip())

print('\n=== Check external access ===')
out, _ = run("curl -sf -A 'Mozilla/5.0' -o /dev/null -w 'HTTP:%{http_code}' http://134.175.67.168:7788/ 2>&1")
print('External HTTP:', out)

client.close()
print('\nDone')
