"""
在服务器上全流程重新部署 + 验证
- 服务器项目根目录: /home/ubuntu/freecdn-deploy
- docker-compose.yml 在该目录下（context: .. 指向上一级，但该目录本身就是根）
"""
import paramiko
import sys, io, time, json, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '134.175.67.168'
USER = 'ubuntu'
PASS = 'REDACTED_SSH_PASS'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=22, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=120):
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8', errors='replace').strip()
    err = e.read().decode('utf-8', errors='replace').strip()
    rc = o.channel.recv_exit_status()
    return out, err, rc

BASE = '/home/ubuntu/freecdn-deploy'

def step(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

# ── 先确认 docker-compose.yml 的 context 路径 ────────────────
step("确认 Dockerfile context 路径")
out, _, _ = run(f"grep -n 'context:' {BASE}/docker-compose.yml")
print(out)
# context: .. 意味着从 /home/ubuntu/freecdn-deploy 上一层 /home/ubuntu
# 检查 Dockerfile 是否存在于正确位置
out, _, _ = run(f"ls -la {BASE}/Dockerfile {BASE}/docker-entrypoint-admin.sh 2>&1")
print(out)

# ── Step 1: 清除所有容器 + volume ────────────────────────────
step("STEP 1: docker compose down -v（清除所有数据，全新安装）")
out, err, rc = run(
    f"cd {BASE} && docker compose down -v 2>&1",
    timeout=60
)
print(out or err)
print(f"rc={rc}")

# ── Step 2: 构建镜像（context 修复：compose context=.. 但实际 Dockerfile 在 BASE）
# 检查实际 compose 文件中 context 是否匹配
step("STEP 2: 确认 build context")
out, _, _ = run(f"grep -A5 'build:' {BASE}/docker-compose.yml | head -20")
print(out)
# 如果 context: .. 那么 build context 是 /home/ubuntu，但 Dockerfile 在 BASE（freecdn-deploy）
# 需要确认
out, _, _ = run(f"ls /home/ubuntu/ | head -20")
print("  /home/ubuntu/ 内容:", out)

# ── Step 3: 修正 context（如果需要）+ build ──────────────────
step("STEP 3: docker compose build（重建镜像）")
print("构建中，请稍候（约 2-5 分钟）...")
out, err, rc = run(
    f"cd {BASE} && docker compose build --no-cache 2>&1 | tail -50",
    timeout=600
)
print(out or err)
print(f"rc={rc}")
if rc != 0:
    print("\n⚠️  构建失败，尝试查看完整错误...")
    out2, _, _ = run(f"cd {BASE} && docker compose build --no-cache 2>&1 | head -80", timeout=600)
    print(out2)
    c.close()
    sys.exit(1)

# ── Step 4: 启动 ─────────────────────────────────────────────
step("STEP 4: docker compose up -d")
out, err, rc = run(f"cd {BASE} && docker compose up -d 2>&1", timeout=60)
print(out or err)
print(f"rc={rc}")

# ── Step 5: 等待 healthy ──────────────────────────────────────
step("STEP 5: 等待容器 healthy（最多 3 分钟）")
for i in range(36):
    time.sleep(5)
    out, _, _ = run("docker inspect freecdn-admin --format '{{.State.Health.Status}}' 2>/dev/null")
    status = out.strip()
    print(f"  [{(i+1)*5}s] health={status}")
    if status == 'healthy':
        print("  ✅ 容器已健康！")
        break
    if status == 'unhealthy':
        print("  ❌ 容器 unhealthy，查看日志...")
        out2, _, _ = run("docker logs freecdn-admin --tail 60 2>&1")
        print(out2)
        break
else:
    print("  ⚠️  超时，继续...")

# ── Step 6: 容器日志 ──────────────────────────────────────────
step("STEP 6: 容器日志（最后 50 行）")
out, _, _ = run("docker logs freecdn-admin --tail 50 2>&1")
print(out)

# ── Step 7: 数据库验证 ────────────────────────────────────────
step("STEP 7: 数据库关键记录验证")
tables = {
    "edgeAdmins":    "SELECT id,username,isSuper,state FROM edgeAdmins LIMIT 3",
    "edgeAPINodes":  "SELECT id,uniqueId,name,state FROM edgeAPINodes LIMIT 3",
    "edgeAPITokens": "SELECT nodeId,role,state FROM edgeAPITokens LIMIT 5",
}
for tbl, sql in tables.items():
    out, _, rc = run(
        f'docker exec freecdn-mysql mysql -ufreecdn -pREDACTED_DB_PASS freecdn -e "{sql}" 2>/dev/null'
    )
    print(f"\n[{tbl}]")
    print(out if out else "(空)")

# ── Step 8: 验证 api.yaml 持久化（volume 挂载验证）────────────
step("STEP 8: 验证 edge-api/configs/api.yaml 存在")
out, _, _ = run("docker exec freecdn-admin cat /app/edge-admin/edge-api/configs/api.yaml 2>/dev/null || echo '(不存在)'")
print(out)

out, _, _ = run("docker exec freecdn-admin cat /root/.edge-admin/api_admin.yaml 2>/dev/null || echo '(不存在)'")
print("\n[~/.edge-admin/api_admin.yaml]")
print(out)

# ── Step 9: HTTP 登录验证 ─────────────────────────────────────
step("STEP 9: HTTP 登录验证")

# 9a. GET 登录页
print("→ GET /（获取 session + page_token）")
out, _, rc = run(
    "curl -sf -c /tmp/fc_cook.txt -D /tmp/fc_head.txt "
    "-A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' "
    "http://127.0.0.1:7788/ -o /tmp/fc_page.html && echo 'GET_OK'",
    timeout=20
)
print(f"  {out}")

# 解析内嵌 token
out, _, _ = run(
    "grep -oP '\"token\":\"[a-f0-9]+\"' /tmp/fc_page.html | head -1 | grep -oP '[a-f0-9]{30,}'"
)
page_token = out.strip()
print(f"  page_token={'[' + page_token[:12] + '...]' if page_token else '(未找到)'}")

# 9b. 获取 CSRF token
print("→ GET /csrf/token")
out, _, _ = run(
    "curl -sf -b /tmp/fc_cook.txt -c /tmp/fc_cook.txt "
    "-A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' "
    "-H 'X-Requested-With: XMLHttpRequest' "
    "http://127.0.0.1:7788/csrf/token"
)
print(f"  response={out[:200]}")
try:
    csrf_token = json.loads(out).get('data', {}).get('token', '')
    print(f"  csrf_token={'[' + csrf_token[:12] + '...]' if csrf_token else '(空)'}")
except Exception as e:
    csrf_token = ''
    print(f"  解析失败: {e}")

# 9c. POST 登录
if page_token and csrf_token:
    pwd_md5 = hashlib.md5(b'REDACTED_SSH_PASS').hexdigest()
    print(f"→ POST /login（admin / md5={pwd_md5[:8]}...）")
    out, _, rc = run(
        f"curl -sf -b /tmp/fc_cook.txt -c /tmp/fc_cook.txt "
        f"-A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' "
        f"-H 'X-Requested-With: XMLHttpRequest' "
        f"-H 'Origin: http://127.0.0.1:7788' "
        f"-H 'Referer: http://127.0.0.1:7788/' "
        f"-X POST http://127.0.0.1:7788/ "
        f"-F 'username=admin' "
        f"-F 'password={pwd_md5}' "
        f"-F 'token={page_token}' "
        f"-F 'csrfToken={csrf_token}'",
        timeout=20
    )
    print(f"  响应: {out[:400]}")
    try:
        resp = json.loads(out)
        if resp.get('code') == 200:
            print("  ✅ 登录成功！localSid=" + resp.get('data', {}).get('localSid', '')[:12] + "...")
        else:
            print(f"  ❌ 登录失败: code={resp.get('code')}, msg={resp.get('message')}")
    except Exception:
        print(f"  ⚠️  响应解析失败")
else:
    print("  ⚠️  缺少 token，跳过登录 POST")

# ── Step 10: 汇总 ─────────────────────────────────────────────
step("STEP 10: 最终状态")
out, _, _ = run("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
print(out)

c.close()
print("\n✅ 全流程验证完毕")
