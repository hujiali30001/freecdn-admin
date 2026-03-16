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

# Test network connectivity
print('=== Test GitHub access from server ===')
out, _ = run('curl -sf --connect-timeout 10 https://github.com -o /dev/null -w "%{http_code}" 2>&1 || echo FAIL')
print('GitHub:', out.strip())

# Test ghfast.top mirror
out, _ = run('curl -sf --connect-timeout 10 https://ghfast.top -o /dev/null -w "%{http_code}" 2>&1 || echo FAIL')
print('ghfast.top:', out.strip())

# Check if we can install curl in the container directly
print('\n=== Install curl in running container ===')
out, err = run('docker exec freecdn-admin apt-get update -qq 2>&1 | tail -3', timeout=60)
print('apt update:', out.strip()[-200:])

out, err = run('docker exec freecdn-admin apt-get install -y -qq curl 2>&1 | tail -5', timeout=120)
print('apt install curl:', out.strip()[-200:])

# Verify
out, _ = run('docker exec freecdn-admin curl --version 2>&1 | head -1')
print('curl version:', out.strip())

# Test healthcheck after installing curl
print('\n=== Test healthcheck with curl ===')
out, _ = run("docker exec freecdn-admin curl -sf -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' http://localhost:7788/ -o /dev/null && echo HEALTHY || echo UNHEALTHY")
print(out.strip())

client.close()
print('\nDone')
