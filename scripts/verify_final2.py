import paramiko
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '134.175.67.168'
port = 22
username = 'ubuntu'
password = 'FreeCDN2026!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=username, password=password, timeout=15)
print('Connected')

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

# Test login page
print('\n=== GET /login ===')
out, err = run('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:7788/login 2>&1')
print(out)

# Test login API with correct format
print('\n=== POST /login/validate (admin/FreeCDN2026!) ===')
out, err = run('curl -s -X POST http://127.0.0.1:7788/login/validate -H "Content-Type: application/json" -d \'{"username":"admin","password":"FreeCDN2026!"}\' 2>&1')
print(out)
try:
    data = json.loads(out.strip())
    print(f"  -> code={data.get('code')}, isOk={data.get('data',{}).get('isOk')}")
except:
    pass

# Check what admin accounts exist
print('\n=== edgeAdmins table ===')
MYSQL_ROOT_PWD = 'freecdn_root_2026'
DB = 'freecdn'
out, err = run(f"sudo docker exec freecdn-mysql mysql -uroot -p{MYSQL_ROOT_PWD} {DB} -e 'SELECT id,username,state FROM edgeAdmins\\G' 2>&1")
print(out)
if err: print('ERR:', err)

# Check api_admin.yaml config  
print('\n=== api_admin.yaml ===')
out, err = run('sudo docker exec freecdn-admin cat /usr/local/freecdn/edge-admin/configs/api_admin.yaml 2>&1')
print(out)

# Check api.yaml to see nodeId/secret
print('\n=== edge-api api.yaml ===')
out, err = run('sudo docker exec freecdn-admin cat /usr/local/freecdn/edge-api/configs/api.yaml 2>&1')
print(out)

# Check edge-api logs
print('\n=== edge-api process and logs ===')
out, err = run('sudo docker exec freecdn-admin ps aux | grep edge 2>&1')
print(out)
out, err = run('sudo docker exec freecdn-admin cat /usr/local/freecdn/edge-api/logs/run.log 2>&1 | tail -20')
print(out)
if err: print('ERR:', err)

client.close()
print('\nDone')
