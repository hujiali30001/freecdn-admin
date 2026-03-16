#!/usr/bin/env python3
"""调试两个 FAIL 项"""
import urllib.request, urllib.parse, urllib.error
import http.cookiejar, hashlib, re, json

BASE = "http://134.175.67.168:7788"
PASS = "REDACTED_SSH_PASS"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.addheaders = [("User-Agent", "Mozilla/5.0")]

def get(path, timeout=10):
    try:
        r = opener.open(f"{BASE}{path}", timeout=timeout)
        return r.getcode(), r.read().decode(errors="replace")
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
        return r.getcode(), r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)

def csrf():
    return json.loads(opener.open(f"{BASE}/csrf/token").read().decode()).get("data",{}).get("token","")

# 登录
code, body = get("/")
m = re.search(r'"token"\s*:\s*"([0-9a-f]{32,}\d+)"', body)
token = m.group(1) if m else ""
csrf0 = csrf()
pwd = hashlib.md5(PASS.encode()).hexdigest()
post("/", {"username":"admin","password":pwd,"token":token,"csrfToken":csrf0})
print("Logged in. Cookies:", [(c.name, c.value[:20]) for c in jar])

# ── 调试1：创建服务 ──────────────────────────────────────────────────
print("\n=== 调试：创建 httpWeb 服务 ===")
addresses = json.dumps([{"protocol":"http","host":"","portRange":"9799"}])
c, b = post("/servers/create", {
    "serverType": "httpWeb",
    "clusterIds": "1",
    "name": "verify-test-web",
    "description": "验收测试服务",
    "addresses": addresses,
    "serverNames": "[]",
    "origins": "[]",
    "csrfToken": csrf(),
})
print(f"status={c}")
print(f"body={b}")  # 完整输出

# ── 调试2：创建管理员 ────────────────────────────────────────────────
print("\n=== 调试：创建管理员 ===")
c, b = post("/admins/createPopup", {
    "fullname": "验收测试管理员",
    "username": "testadmin_verify2",
    "pass1": "TestPass2026!",
    "pass2": "TestPass2026!",
    "isSuper": "false",
    "canLogin": "true",
    "otpOn": "false",
    "moduleCodes": "",
    "csrfToken": csrf(),
})
print(f"status={c}")
print(f"body={b}")
