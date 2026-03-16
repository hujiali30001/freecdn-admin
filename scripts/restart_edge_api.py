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
print('Connected')

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

# Check api.yaml is there
print('\n=== api.yaml ===')
out, err = run('sudo docker exec freecdn-admin cat /app/edge-admin/edge-api/configs/api.yaml 2>&1')
print(out)

# Find edge-api binary and run it directly in background
print('\n=== Starting edge-api manually ===')
out, err = run('sudo docker exec freecdn-admin sh -c "cd /app/edge-admin/edge-api && ./bin/edge-api > /tmp/edge-api-new.log 2>&1 & sleep 3 && echo PID:$! && tail -5 /tmp/edge-api-new.log" 2>&1')
print(out)

time.sleep(3)

# Check if edge-api is now listening
print('\n=== edge-api log after manual start ===')
out, err = run('sudo docker exec freecdn-admin sh -c "tail -15 /tmp/edge-api-new.log 2>&1"')
print(out)

# Check run.log
print('\n=== edge-api run.log last 5 ===')
out, err = run('sudo docker exec freecdn-admin sh -c "tail -5 /app/edge-admin/edge-api/logs/run.log 2>&1"')
print(out)

# Test port 8003
print('\n=== Port 8003 check ===')
out, err = run('sudo ss -tlnp | grep 8003 2>&1')
print(out or '(not listening)')

# Test GET /
print('\n=== GET / ===')
out, err = run('curl -s -o /dev/null -w "HTTP %{http_code}" -H "User-Agent: Mozilla/5.0 Chrome/120" http://127.0.0.1:7788/ 2>&1')
print(out)

client.close()
print('\nDone')
