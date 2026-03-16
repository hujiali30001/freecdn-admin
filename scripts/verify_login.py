import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '134.175.67.168'
port = 22
username = 'ubuntu'
password = 'REDACTED_SSH_PASS'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=username, password=password, timeout=15)
print('Connected')

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

# 1. Check container HOME and ~/.edge-admin
print('\n=== Container HOME and ~/.edge-admin ===')
out, err = run('sudo docker exec freecdn-admin sh -c "echo HOME=$HOME; ls -la /root/.edge-admin/ 2>&1"')
print(out)

# 2. GET / - should be 200 (login page)
print('\n=== GET / ===')
out, err = run('curl -s -o /dev/null -w "HTTP %{http_code}" -H "User-Agent: Mozilla/5.0 Chrome/120" http://127.0.0.1:7788/ 2>&1')
print(out)

# 3. GET / redirects anywhere?
print('\n=== GET / with redirect follow ===')
out, err = run('curl -sv -L -H "User-Agent: Mozilla/5.0 Chrome/120" http://127.0.0.1:7788/ 2>&1 | grep -E "< HTTP|< Location|title" | head -10')
print(out)

# 4. Check if edge-api is running
print('\n=== edge-api status ===')
out, err = run('sudo docker exec freecdn-admin sh -c "cat /app/edge-admin/edge-api/logs/run.log 2>&1 | tail -10"')
print(out)

# 5. Container health
print('\n=== Container health ===')
out, err = run('sudo docker inspect freecdn-admin --format "{{.State.Status}} {{.State.Health.Status}}" 2>&1')
print(out)

# 6. edge-admin log
print('\n=== edge-admin run.log last 10 ===')
out, err = run('sudo docker exec freecdn-admin sh -c "tail -10 /app/edge-admin/logs/run.log 2>&1"')
print(out)

# 7. Test from external - can we load the login page HTML?
print('\n=== Login page body (first 200 chars) ===')
out, err = run('curl -s -H "User-Agent: Mozilla/5.0 Chrome/120" http://127.0.0.1:7788/ 2>&1 | head -c 300')
print(out[:300])

client.close()
print('\nDone')
