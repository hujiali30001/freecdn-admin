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
print('Connected')

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

print('Waiting 15s for full startup...')
time.sleep(15)

print('\n=== Container status ===')
out, err = run('sudo docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1')
print(out)

print('\n=== freecdn-admin logs (last 30) ===')
out, err = run('sudo docker logs freecdn-admin --tail=30 2>&1')
print(out)
if err: print('ERR:', err)

print('\n=== Port 7788 HTTP test ===')
out, err = run('curl -v http://127.0.0.1:7788/ 2>&1 | head -30')
print(out)

print('\n=== Port 8001 gRPC test ===')
out, err = run('nc -z -w5 127.0.0.1 8001 && echo "PORT 8001 OPEN" || echo "PORT 8001 CLOSED"')
print(out)

print('\n=== Login API test ===')
out, err = run('curl -s -X POST http://127.0.0.1:7788/login/validate -H "Content-Type: application/json" -d \'{"username":"admin","password":"REDACTED_SSH_PASS"}\' 2>&1')
print(out)

print('\n=== External port test from outside ===')
out, err = run('curl -s -o /dev/null -w "External HTTP %{http_code}" http://134.175.67.168:7788/ 2>&1')
print(out)

client.close()
print('\nDone')
