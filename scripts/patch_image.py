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

# The issue: entrypoint.sh doesn't have +x because docker cp doesn't preserve perms
# and commit doesn't include uncommitted changes
# Solution: use a tiny Dockerfile to patch the existing image

print('=== Create patch Dockerfile ===')
patch_dockerfile = '''FROM freecdn/admin:latest
COPY docker-entrypoint-admin.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
'''

out, err = run('cat > /home/ubuntu/freecdn-deploy/Dockerfile.patch << \'HEREDOC\'\n' + patch_dockerfile + '\nHEREDOC')
# Write via SFTP instead
sftp = client.open_sftp()
with sftp.open('/home/ubuntu/freecdn-deploy/Dockerfile.patch', 'w') as f:
    f.write(patch_dockerfile)
print('Dockerfile.patch written')

# Build the patched image
print('\n=== Build patched image ===')
out, err = run(
    'cd /home/ubuntu/freecdn-deploy && '
    'docker build -f Dockerfile.patch -t freecdn/admin:latest . 2>&1',
    timeout=120
)
print(out)
if err:
    print('STDERR:', err[:500])

# Verify
out, _ = run('docker images freecdn/admin:latest')
print('New image:', out.strip())

# Test the entrypoint in new image
out, _ = run('docker run --rm --entrypoint ls freecdn/admin:latest -la /entrypoint.sh 2>&1')
print('entrypoint.sh permissions:', out.strip())

# Recreate container
print('\n=== Recreate container ===')
out, err = run('cd /home/ubuntu/freecdn-deploy && docker compose up -d --force-recreate freecdn-admin 2>&1', timeout=120)
print(out)

print('Waiting 40s...')
time.sleep(40)

print('\n=== Final status ===')
out, _ = run('docker inspect freecdn-admin --format "Health={{.State.Health.Status}} Running={{.State.Running}}"')
print('Status:', out.strip())

out, _ = run('docker logs freecdn-admin --tail 20 2>&1')
print('\nLogs:', out)

out, _ = run('docker exec freecdn-admin ls -la /root/.edge-admin/ 2>&1')
print('\n~/.edge-admin/:', out)

out, _ = run("curl -s -A 'Mozilla/5.0' -o /dev/null -w 'HTTP:%{http_code}' http://134.175.67.168:7788/")
print('\nExternal HTTP:', out)

sftp.close()
client.close()
print('\nAll done!')
