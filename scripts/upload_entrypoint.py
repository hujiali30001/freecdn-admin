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

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

sftp = client.open_sftp()

# Upload updated entrypoint.sh to the deploy directory on server
print('\n=== Uploading entrypoint to /home/ubuntu/freecdn-deploy/ ===')
with open(r'c:\Users\Administrator\.workbuddy\FreeCDN\deploy\docker-entrypoint-admin.sh', 'rb') as f:
    content = f.read()

with sftp.open('/home/ubuntu/freecdn-deploy/docker-entrypoint-admin.sh', 'wb') as f:
    f.write(content)
print(f'Uploaded ({len(content)} bytes)')

# Verify
out, err = run('tail -20 /home/ubuntu/freecdn-deploy/docker-entrypoint-admin.sh 2>&1')
print('Tail of updated file:')
print(out)

sftp.close()
client.close()
print('\nDone')
