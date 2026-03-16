import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '134.175.67.168'
port = 22
username = 'ubuntu'
password = 'REDACTED_SSH_PASS'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=username, password=password, timeout=15)
print('Connected')

def run(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

sftp = client.open_sftp()

# 1. Upload the updated entrypoint.sh
print('\n=== Uploading updated entrypoint.sh to server ===')
with open(r'c:\Users\Administrator\.workbuddy\FreeCDN\deploy\docker-entrypoint-admin.sh', 'rb') as f:
    content = f.read()
    
# Write to /tmp on server
with sftp.open('/tmp/new_entrypoint.sh', 'wb') as f:
    f.write(content)
print('Uploaded to /tmp/new_entrypoint.sh')

# 2. Copy into container
print('\n=== Copy entrypoint.sh into container ===')
out, err = run('sudo docker cp /tmp/new_entrypoint.sh freecdn-admin:/entrypoint.sh && sudo docker exec freecdn-admin chmod +x /entrypoint.sh && echo OK')
print(out)
if err: print('ERR:', err)

# 3. Verify 
print('\n=== Verify in container ===')
out, err = run('sudo docker exec freecdn-admin tail -15 /entrypoint.sh')
print(out)

# 4. Now restart the container to test the fix
print('\n=== Restarting freecdn-admin ===')
out, err = run('cd /home/ubuntu/freecdn-deploy && sudo docker compose restart freecdn-admin 2>&1', timeout=60)
print(out)
if err and 'warn' not in err.lower(): print('ERR:', err)

# 5. Wait and check
import time
time.sleep(15)

print('\n=== Container status after restart ===')
out, err = run('sudo docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1')
print(out)

# 6. Check if ~/.edge-admin/ was created
print('\n=== ~/.edge-admin/ after restart ===')
out, err = run('sudo docker exec freecdn-admin ls -la ~/.edge-admin/ 2>&1')
print(out)

# 7. Check GET /
print('\n=== GET / after restart ===')
out, err = run('curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}" -H "User-Agent: Mozilla/5.0 Chrome/120" http://127.0.0.1:7788/ -L 2>&1')
print(out)

sftp.close()
client.close()
print('\nDone')
