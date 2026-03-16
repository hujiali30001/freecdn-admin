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

sftp = client.open_sftp()

# 1. Update docker-compose.yml: change healthcheck back to curl (correct UA)
with sftp.open('/home/ubuntu/freecdn-deploy/docker-compose.yml', 'rb') as f:
    raw = f.read()
content = raw.decode('utf-8', errors='replace')
content_lf = content.replace('\r\n', '\n')

# Current healthcheck (nc version we set)
old_hc = '''    healthcheck:
      test: ["CMD-SHELL", "nc -z -w 3 127.0.0.1 7788 || exit 1"]
      interval: 30s
      timeout: 10s
      start_period: 60s
      retries: 3'''

# Restore to curl version (what Dockerfile HEALTHCHECK uses)
new_hc = '''    healthcheck:
      test: ["CMD-SHELL", "curl -sf -A 'Mozilla/5.0 (compatible; HealthCheck)' http://localhost:7788/ > /dev/null 2>&1 || exit 1"]
      interval: 30s
      timeout: 10s
      start_period: 90s
      retries: 3'''

old_hc_lf = old_hc.replace('\r\n', '\n')
new_hc_lf = new_hc.replace('\r\n', '\n')

if old_hc_lf in content_lf:
    new_content_lf = content_lf.replace(old_hc_lf, new_hc_lf, 1)
    new_content = new_content_lf.replace('\n', '\r\n')
    with sftp.open('/home/ubuntu/freecdn-deploy/docker-compose.yml', 'wb') as f:
        f.write(new_content.encode('utf-8'))
    print('Healthcheck restored to curl version in docker-compose.yml')
else:
    print('WARNING: nc healthcheck not found, checking current state...')
    idx = content_lf.find('healthcheck:')
    if idx >= 0:
        print(repr(content_lf[idx:idx+200]))

sftp.close()

# 2. Build new image
print('\n=== Building new Docker image ===')
print('This may take a few minutes...')
out, err = run(
    'cd /home/ubuntu/freecdn-deploy && '
    'docker compose build --no-cache freecdn-admin 2>&1',
    timeout=600
)
print(out[-3000:] if len(out) > 3000 else out)
if err:
    print('STDERR:', err[-500:])

client.close()
print('\nBuild done')
