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

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out, err

print('=' * 70)
print('FULL SYSTEM VERIFICATION - FreeCDN Admin @ 134.175.67.168')
print('=' * 70)

# 1. Container health
print('\n[1] Container health check:')
out, _ = run('docker inspect freecdn-admin --format "Running={{.State.Running}} Health={{.State.Health.Status}}"')
print('   ', out.strip())

# 2. All volumes
print('\n[2] Volume mounts:')
out, _ = run('docker inspect freecdn-admin --format "{{range .Mounts}}  {{.Name}} -> {{.Destination}}\n{{end}}"')
print(out)

# 3. Key files in volumes
print('[3] Key config files:')
out, _ = run('docker exec freecdn-admin ls -la /app/edge-admin/configs/ /app/edge-admin/edge-api/configs/ 2>&1')
print(out)

# 4. ~/.edge-admin/ sync
print('[4] ~/.edge-admin/ (IsNewInstalled check):')
out, _ = run('docker exec freecdn-admin cat /root/.edge-admin/api_admin.yaml 2>/dev/null | head -3')
print(out or '  NOT FOUND!')

# 5. edge-api running
print('[5] edge-api port 8003:')
out, _ = run('docker exec freecdn-admin sh -c "grep 1F43 /proc/net/tcp6 2>/dev/null | head -1 | awk \'{print $4}\'"')
state = out.strip()
print('   Port 8003 state:', '0A (LISTEN)' if state == '0A' else state)

# 6. Admin account
print('\n[6] Admin account:')
out, _ = run('docker exec freecdn-mysql mysql -ufreecdn -pREDACTED_DB_PASS freecdn -sNe "SELECT username, (password=\'0bab18d55a860df6d4ab91d32acf0542\') as pwd_ok, state, canLogin FROM edgeAdmins WHERE username=\'admin\';" 2>/dev/null')
print('   username | pwd_ok | state | canLogin')
print('  ', out.strip())

# 7. HTTP test from outside
print('\n[7] HTTP accessibility:')
out, _ = run("curl -s -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' http://134.175.67.168:7788/ | grep '<title>'")
print('   Title:', out.strip())

# 8. No redirect to /setup/confirm
out, _ = run("curl -sL -A 'Mozilla/5.0' -o /dev/null -w '%{http_code} %{url_effective}' http://localhost:7788/")
print('   Final URL:', out)

# 9. healthcheck log (last 3)
print('\n[8] Healthcheck history (last 3):')
out, _ = run('docker inspect freecdn-admin 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f\'  {h[chr(69)+chr(120)+chr(105)+chr(116)+chr(67)+chr(111)+chr(100)+chr(101)]}: {h[chr(83)+chr(116)+chr(97)+chr(114)+chr(116)][11:19]}\') for h in d[0][chr(83)+chr(116)+chr(97)+chr(116)+chr(101)][chr(72)+chr(101)+chr(97)+chr(108)+chr(116)+chr(104)][chr(76)+chr(111)+chr(103)][-3:]]" 2>/dev/null')
# Simpler
out, _ = run('docker inspect freecdn-admin 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); logs=d[0][\'State\'][\'Health\'][\'Log\']; [print(f\'  ExitCode={l[\"ExitCode\"]} at {l[\"Start\"][11:19]}\') for l in logs[-3:]]"')
print(out)

print('=' * 70)
print('LOGIN: http://134.175.67.168:7788/')
print('User:  admin')
print('Pass:  REDACTED_SSH_PASS')
print('=' * 70)

client.close()
