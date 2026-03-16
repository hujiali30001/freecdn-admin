import paramiko
import sys

host = '134.175.67.168'
port = 22
username = 'ubuntu'
password = 'FreeCDN2026!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=username, password=password, timeout=15)

stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/freecdn-deploy/docker-compose.yml')
content = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

print(repr(content[:100]))
with open('c:/tmp/docker-compose-remote.yml', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written to c:/tmp/docker-compose-remote.yml, length:', len(content))

client.close()
