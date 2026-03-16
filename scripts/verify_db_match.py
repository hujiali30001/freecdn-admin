import paramiko
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '134.175.67.168'
USER = 'ubuntu'
PASS = 'FreeCDN2026!'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=22, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=60):
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8', errors='replace')
    err = e.read().decode('utf-8', errors='replace')
    return out, err

# DB credentials
DB_USER = 'freecdn'
DB_PASS = 'freecdn_pass_2026'
DB_NAME = 'freecdn'

def mysql(sql):
    cmd = f"docker exec freecdn-mysql mysql -u{DB_USER} -p{DB_PASS} {DB_NAME} -e \"{sql}\" 2>/dev/null"
    out, err = run(cmd)
    return out

print("=== edgeAPINodes ===")
print(mysql("SELECT id, uniqueId, LEFT(secret,30) as secret_prefix, state FROM edgeAPINodes;"))

print("=== edgeAPITokens ===")
print(mysql("SELECT id, nodeId, role, LEFT(token,20) as token_prefix, state FROM edgeAPITokens;"))

print("=== edgeAdmins ===")
print(mysql("SELECT id, username, LEFT(password,32) as pwd_hash, state FROM edgeAdmins;"))

print("=== api_admin.yaml in container ===")
out, _ = run("docker exec freecdn-admin cat /app/edge-admin/configs/api_admin.yaml 2>/dev/null")
print(out)

print("=== api.yaml in container ===")
out, _ = run("docker exec freecdn-admin cat /app/edge-admin/edge-api/configs/api.yaml 2>/dev/null")
print(out)

print("=== ~/.edge-admin/api_admin.yaml ===")
out, _ = run("docker exec freecdn-admin cat /root/.edge-admin/api_admin.yaml 2>/dev/null")
print(out)

# 关键：验证 api_admin.yaml 里的 nodeId 是否在 edgeAPITokens 里
print("=== Verify: api_admin.yaml nodeId in edgeAPITokens ===")
out, _ = run("docker exec freecdn-admin cat /app/edge-admin/configs/api_admin.yaml 2>/dev/null")
node_id = None
for line in out.splitlines():
    if 'nodeId' in line:
        node_id = line.split(':')[1].strip().strip('"')
        break
if node_id:
    print(f"  api_admin.yaml nodeId: {node_id}")
    result = mysql(f"SELECT id, nodeId, role, state FROM edgeAPITokens WHERE nodeId='{node_id}';")
    print(f"  In DB: {result}")
else:
    print("  Could not extract nodeId")

# 验证 api.yaml nodeId 是否在 edgeAPINodes 里
print("\n=== Verify: api.yaml nodeId in edgeAPINodes ===")
out, _ = run("docker exec freecdn-admin cat /app/edge-admin/edge-api/configs/api.yaml 2>/dev/null")
api_node_id = None
for line in out.splitlines():
    if 'nodeId' in line:
        api_node_id = line.split(':')[1].strip().strip('"')
        break
if api_node_id:
    print(f"  api.yaml nodeId: {api_node_id}")
    result = mysql(f"SELECT id, uniqueId, LEFT(secret,20) as s, state FROM edgeAPINodes WHERE uniqueId='{api_node_id}';")
    print(f"  In DB: {result}")
else:
    print("  Could not extract nodeId")

# 测试登录 HTTP
print("\n=== Test HTTP login page ===")
out, _ = run("docker exec freecdn-admin curl -sf -A 'Mozilla/5.0' http://localhost:7788/ 2>/dev/null | grep -o '<title>[^<]*</title>'")
print(out or "(empty)")

# 测试 CSRF token 端点
print("\n=== Test CSRF token endpoint ===")
out, _ = run("docker exec freecdn-admin curl -sf -A 'Mozilla/5.0' http://localhost:7788/csrf/token 2>/dev/null | head -200")
print(out or "(empty)")

c.close()
print("\nDone.")
