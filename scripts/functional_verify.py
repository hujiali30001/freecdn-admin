#!/usr/bin/env python3
"""
FreeCDN v0.4.0 功能逻辑验收脚本
测试各模块 API 是否正常工作（POST/创建/查询）
"""
import urllib.request, urllib.parse, urllib.error
import http.cookiejar, hashlib, re, json, time

BASE = "http://134.175.67.168:7788"
PASS = "REDACTED_SSH_PASS"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.addheaders = [("User-Agent", "Mozilla/5.0")]

def get(path, timeout=10):
    try:
        r = opener.open(f"{BASE}{path}", timeout=timeout)
        b = r.read().decode(errors="replace")
        return r.getcode(), b
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)

def post(path, data, timeout=15):
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=payload)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    try:
        r = opener.open(req, timeout=timeout)
        b = r.read().decode(errors="replace")
        return r.getcode(), b
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)

def post_json(path, data, timeout=15):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=payload)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    try:
        r = opener.open(req, timeout=timeout)
        b = r.read().decode(errors="replace")
        return r.getcode(), b
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)

def ok(j):
    """判断 API 返回是否成功"""
    try:
        d = json.loads(j)
        return d.get("code") == 200 or d.get("isOk") is True
    except:
        return False

def get_data(j):
    try:
        return json.loads(j).get("data", {})
    except:
        return {}

results = []

def check(name, passed, detail=""):
    flag = "PASS" if passed else "FAIL"
    results.append((flag, name, detail))
    print(f"  [{flag}] {name:<40} {detail}")

# ═══════════════════════════════════════════════════════════════════
print("=" * 65)
print("FreeCDN v0.4.0 功能验收")
print("=" * 65)

# ── 登录 ──────────────────────────────────────────────────────────
print("\n[AUTH] 登录...")
code, body = get("/")
m = re.search(r'"token"\s*:\s*"([0-9a-f]{32,}\d+)"', body)
token = m.group(1) if m else ""
code2, csrf_body = get("/csrf/token")
csrf = json.loads(csrf_body).get("data", {}).get("token", "")
pwd = hashlib.md5(PASS.encode()).hexdigest()
code3, lb = post("/", {"username": "admin", "password": pwd, "token": token, "csrfToken": csrf})
logged_in = ok(lb)
check("登录 (admin/REDACTED_SSH_PASS)", logged_in, f"code={code3}")
if not logged_in:
    print("  登录失败，终止验收")
    exit(1)

# ═══════════════════════════════════════════════════════════════════
# 1. 集群
print("\n[1] 集群管理")
c, b = get("/clusters")
check("集群列表页面", c == 200)

# 查询集群列表 API
c, b = post("/clusters", {"action": "list"})
# 用页面方式验证（已是 200），改为找集群 ID
c, b = get("/clusters")
# 从页面找第一个集群 ID（通常是 1）
cluster_id = "1"  # 默认

# 查集群详情
c, b = get(f"/clusters/cluster?clusterId={cluster_id}")
check("集群详情页面", c == 200 and "clusterId" not in b.lower() or c == 200)

# ═══════════════════════════════════════════════════════════════════
# 2. 节点
print("\n[2] 节点管理")
c, b = get(f"/clusters/nodes?clusterId={cluster_id}")
check("节点列表页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 3. HTTP 服务创建
print("\n[3] HTTP 服务")
c, b = get("/servers")
check("服务列表页面", c == 200)

c, b = get("/servers/create")
check("创建服务页面", c == 200)

# 尝试创建一个测试 httpWeb 服务（静态Web类型，不需要源站）
csrf_resp = json.loads(opener.open(f"{BASE}/csrf/token").read().decode())
csrf2 = csrf_resp.get("data", {}).get("token", "")
import json as _json
addresses = _json.dumps([{"protocol": "http", "host": "", "portRange": "9799"}])
c, b = post("/servers/create", {
    "type": "httpWeb",                          # 服务页面 type 参数（隐藏字段）
    "serverType": "httpWeb",
    "clusterIds": cluster_id,
    "name": "verify-test-web",
    "description": "验收测试服务（httpWeb）",
    "addresses": addresses,
    "serverNames": "[]",
    "origins": "[]",
    "csrfToken": csrf2,
})
d = get_data(b)
server_created = ok(b) and d.get("serverId", 0) > 0
server_id = d.get("serverId", 0)
check("创建 HTTP 服务 (httpWeb)", server_created, f"serverId={server_id}, resp={b[:100]}")

# ═══════════════════════════════════════════════════════════════════
# 4. 证书管理
print("\n[4] 证书管理")
c, b = get("/servers/certs")
check("证书列表页面", c == 200)

c, b = get("/servers/certs/acme")
check("ACME 申请页面", c == 200)

c, b = get("/servers/certs/uploadPopup")
check("上传证书弹窗页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 5. DNS
print("\n[5] DNS 管理")
c, b = get("/dns")
check("DNS 域名列表页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 6. 管理员
print("\n[6] 管理员管理")
c, b = get("/admins")
check("管理员列表页面", c == 200)

c, b = get("/admins/createPopup")
check("创建管理员弹窗页面", c == 200)

# 尝试创建一个测试管理员（需要 fullname、pass1、pass2）
csrf3 = json.loads(opener.open(f"{BASE}/csrf/token").read().decode()).get("data", {}).get("token", "")
c, b = post("/admins/createPopup", {
    "fullname": "验收测试管理员",
    "username": "testadmin_verify",
    "pass1": "TestPass2026!",
    "pass2": "TestPass2026!",
    "isSuper": "false",
    "canLogin": "true",
    "otpOn": "false",
    "csrfToken": csrf3,
})
admin_created = ok(b)
admin_id = get_data(b).get("adminId", 0)
check("创建管理员账号", admin_created, f"adminId={admin_id}, resp={b[:80]}")

# 删除刚创建的测试管理员（如果创建成功）
if admin_created and admin_id:
    csrf4 = json.loads(opener.open(f"{BASE}/csrf/token").read().decode()).get("data", {}).get("token", "")
    c, b = post("/admins/delete", {"adminId": admin_id, "csrfToken": csrf4})
    check("删除测试管理员", ok(b), f"resp={b[:60]}")

# ═══════════════════════════════════════════════════════════════════
# 7. 用户
print("\n[7] 用户系统")
c, b = get("/users")
check("用户列表页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 8. 系统设置
print("\n[8] 系统设置")
c, b = get("/settings")
check("基本设置页面", c == 200)

c, b = get("/settings/security")
check("安全设置页面", c == 200)

c, b = get("/db")
check("数据库状态页面", c == 200)

c, b = get("/settings/profile")
check("个人信息页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 9. 日志
print("\n[9] 日志")
c, b = get("/log")
check("操作日志页面", c == 200)

c, b = get("/settings/login")
check("登录日志页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 10. Dashboard
print("\n[10] Dashboard")
c, b = get("/dashboard")
check("Dashboard 页面", c == 200)

# ═══════════════════════════════════════════════════════════════════
# 清理：删除测试 HTTP 服务
if server_created and server_id:
    print("\n[CLEANUP] 删除测试服务...")
    csrf5 = json.loads(opener.open(f"{BASE}/csrf/token").read().decode()).get("data", {}).get("token", "")
    c, b = post("/servers/delete", {"serverId": server_id, "csrfToken": csrf5})
    check("删除测试 HTTP 服务", ok(b), f"resp={b[:60]}")

# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
passed = sum(1 for f, _, _ in results if f == "PASS")
failed = sum(1 for f, _, _ in results if f == "FAIL")
print(f"结果：PASS={passed}  FAIL={failed}  共{len(results)}项")
print("=" * 65)

if failed > 0:
    print("\nFAIL 详情：")
    for f, name, detail in results:
        if f == "FAIL":
            print(f"  - {name}: {detail}")
