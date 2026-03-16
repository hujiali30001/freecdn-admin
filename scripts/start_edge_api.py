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

def run(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

# Check edge-api binary options more carefully
print('=== edge-api start options ===')
out, _ = run('docker exec freecdn-admin /app/edge-admin/edge-api/bin/edge-api start 2>&1')
print(out[:1000])

time.sleep(3)

# Check if it started
print('\n=== Processes ===')
out, _ = run('docker exec freecdn-admin ps aux 2>&1')
print(out)

# Check port 8003
print('\n=== Port 8003 ===')
out, _ = run('docker exec freecdn-admin sh -c "ss -tlnp 2>/dev/null | grep 8003 || netstat -tlnp 2>/dev/null | grep 8003 || (lsof -i:8003 2>/dev/null | head)"')
print(out)

# Check edge-api logs
print('\n=== edge-api logs ===')
out, _ = run('docker exec freecdn-admin cat /app/edge-admin/edge-api/logs/run.log 2>/dev/null | tail -20 || echo "no log file"')
print(out)

# Try the daemon flag
print('\n=== Try daemon mode ===')
out, err = run('docker exec freecdn-admin sh -c "cd /app/edge-admin/edge-api && ./bin/edge-api daemon 2>&1 | head -5"', timeout=10)
print(out, err[:200] if err else '')

time.sleep(3)

out, _ = run('docker exec freecdn-admin ps aux 2>&1 | grep edge-api')
print('Processes after daemon attempt:', out)

out, _ = run('docker exec freecdn-admin sh -c "ss -tlnp 2>/dev/null | grep 8003 || netstat -tlnp 2>/dev/null | grep 8003"')
print('Port 8003:', out)

client.close()
print('\nDone')
