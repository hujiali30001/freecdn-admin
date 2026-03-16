import paramiko
import sys
import time

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

print('=== Step 1: Check current container state ===')
out, err = run('docker inspect freecdn-admin --format "Status={{.State.Status}} Health={{.State.Health.Status}}" 2>&1')
print(out.strip())

print('\n=== Step 2: Backup current api.yaml from container ===')
out, err = run('docker exec freecdn-admin cat /app/edge-admin/edge-api/configs/api.yaml 2>&1')
if 'no such' in out.lower() or 'error' in out.lower():
    print('WARNING: api.yaml not found in container:', out.strip())
    api_yaml_content = None
else:
    print('api.yaml found, content length:', len(out))
    api_yaml_content = out

print('\n=== Step 3: Also backup api_admin.yaml ===')
out, err = run('docker exec freecdn-admin cat /app/edge-admin/configs/api_admin.yaml 2>&1')
if 'no such' not in out.lower():
    print('api_admin.yaml content length:', len(out))
    api_admin_content = out
else:
    print('WARNING: api_admin.yaml not found:', out.strip())
    api_admin_content = None

print('\n=== Step 4: Recreate container with new volume ===')
print('Running docker compose up --force-recreate...')
out, err = run('cd /home/ubuntu/freecdn-deploy && docker compose up -d --force-recreate freecdn-admin 2>&1', timeout=180)
print(out[-2000:] if len(out) > 2000 else out)
if err:
    print('STDERR:', err[-500:])

print('\n=== Step 5: Wait 10s for container to start ===')
time.sleep(10)

print('\n=== Step 6: Check container status ===')
out, err = run('docker inspect freecdn-admin --format "Status={{.State.Status}} Health={{.State.Health.Status}}" 2>&1')
print(out.strip())

print('\n=== Step 7: Check if edge-api configs dir exists ===')
out, err = run('docker exec freecdn-admin ls -la /app/edge-admin/edge-api/configs/ 2>&1')
print(out)

print('\n=== Step 8: Check if api_admin.yaml exists ===')
out, err = run('docker exec freecdn-admin ls -la /app/edge-admin/configs/ 2>&1')
print(out)

print('\n=== Step 9: Check container logs (last 30 lines) ===')
out, err = run('docker logs freecdn-admin --tail 30 2>&1')
print(out)

client.close()
print('Done')
