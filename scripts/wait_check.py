import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '134.175.67.168'
port = 22
username = 'ubuntu'
password = 'FreeCDN2026!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=username, password=password, timeout=15)
print('Connected - waiting 30s for container to start...')

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

time.sleep(30)

# Check status
print('\n=== Status after 30s ===')
out, err = run('sudo docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1')
print(out)

# Check login page
out, err = run('curl -s -o /dev/null -w "HTTP %{http_code}" -H "User-Agent: Mozilla/5.0 Chrome/120" http://127.0.0.1:7788/ 2>&1')
print('GET /:', out)

# Check ~/.edge-admin
out, err = run('sudo docker exec freecdn-admin ls /root/.edge-admin/ 2>&1')
print('~/.edge-admin:', out.strip())

# Check edge-api
out, err = run('sudo docker exec freecdn-admin sh -c "tail -3 /app/edge-admin/edge-api/logs/run.log 2>&1"')
print('edge-api log:', out.strip())

# Check edge-admin
out, err = run('sudo docker exec freecdn-admin sh -c "tail -5 /app/edge-admin/logs/run.log 2>&1"')
print('edge-admin log:', out.strip())

client.close()
print('\nDone')
