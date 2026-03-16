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

def run(cmd, timeout=300):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

# 1. Update entrypoint.sh in the RUNNING container (from server copy)
print('=== Step 1: Update entrypoint.sh in container ===')
out, err = run('docker cp /home/ubuntu/freecdn-deploy/docker-entrypoint-admin.sh freecdn-admin:/entrypoint.sh 2>&1')
print('docker cp:', out.strip() or 'OK', err.strip() if err else '')

# Verify
out, _ = run('docker exec freecdn-admin wc -l /entrypoint.sh')
print('entrypoint.sh lines:', out.strip())

out, _ = run('docker exec freecdn-admin grep -c "edge-admin" /entrypoint.sh')
print('edge-admin mentions:', out.strip())

# Check if it has the new sync code
out, _ = run('docker exec freecdn-admin grep -n "ADMIN_HOME_DIR\|已同步.*api_admin" /entrypoint.sh')
print('Sync code present:', out.strip() if out.strip() else 'NOT FOUND')

# 2. Commit this updated entrypoint to the image
print('\n=== Step 2: Commit new entrypoint to image ===')
out, err = run('docker commit '
    '--change \'ENTRYPOINT ["/entrypoint.sh"]\' '
    '--change \'EXPOSE 7788 8003\' '
    '--change \'WORKDIR /app/edge-admin\' '
    '--message "Updated entrypoint with api.yaml rebuild + ~/.edge-admin sync" '
    'freecdn-admin freecdn/admin:latest 2>&1')
print('docker commit:', out.strip())

out, _ = run('docker images freecdn/admin:latest')
print('New image:', out.strip())

# 3. Now recreate container with updated image
# This time entrypoint should properly handle ~/.edge-admin/ and api.yaml
print('\n=== Step 3: Recreate container with updated image ===')
out, err = run('cd /home/ubuntu/freecdn-deploy && docker compose up -d --force-recreate freecdn-admin 2>&1', timeout=120)
print(out)

print('Waiting 35s for startup...')
time.sleep(35)

# 4. Check results
print('\n=== Step 4: Check results ===')
out, _ = run('docker inspect freecdn-admin --format "Health={{.State.Health.Status}} Running={{.State.Running}}"')
print('Status:', out.strip())

out, _ = run('docker logs freecdn-admin --tail 25 2>&1')
print('\nLogs:', out)

# Check ~/.edge-admin/ was synced by entrypoint
out, _ = run('docker exec freecdn-admin ls -la /root/.edge-admin/ 2>&1')
print('\n~/.edge-admin/:', out)

# Check api.yaml
out, _ = run('docker exec freecdn-admin cat /app/edge-admin/edge-api/configs/api.yaml 2>&1')
print('api.yaml:', out.strip())

# HTTP check
out, _ = run("curl -s -A 'Mozilla/5.0' -o /dev/null -w 'HTTP:%{http_code}' http://localhost:7788/")
print('\nHTTP status:', out)

client.close()
print('\nDone')
