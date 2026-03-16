#!/usr/bin/env python3
"""
EdgeCommon 正确的重命名策略：
- 在 v1.3.9 commit 上创建新分支 freecdn-v1.3.9
- 只在这个分支上做 module 重命名（不带任何 v1.4.x 新增代码）
- 打 tag v1.3.9-freecdn.1
- 三主仓库 replace 指向这个新 tag/commit
"""
import subprocess, sys, os, json, base64, http.client, re

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("Usage: python fix_edgecommon.py <token>")
    sys.exit(1)

DISTRO = "Ubuntu-24.04"
REPO_DIR = "/tmp/freecdn-b/EdgeCommon"
# v1.3.9 commit
V139_SHA = "ae7ca4b083d2773ef3db2ab88d94d1fc1d4b1285"
NEW_BRANCH = "freecdn-v1.3.9"
NEW_TAG = "v1.3.9-freecdn.1"


def wsl(script, check=True):
    host_ip = "172.24.208.1"
    r2 = subprocess.run(["wsl", "-d", DISTRO, "--", "ip", "route", "show", "default"],
                        capture_output=True, text=True)
    for part in r2.stdout.split():
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", part):
            host_ip = part
            break
    full = f"export HTTPS_PROXY=http://{host_ip}:4780 HTTP_PROXY=http://{host_ip}:4780 PATH=/usr/local/go/bin:/usr/bin:/bin; " + script
    r = subprocess.run(
        ["wsl", "-d", DISTRO, "-u", "root", "--", "bash", "-c", full],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in r.stdout.splitlines():
        print(f"  {line}")
    if check and r.returncode != 0:
        print(f"ERROR: exit {r.returncode}")
        sys.exit(1)
    return r


def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-Fix/1.0",
    }
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})


REPO = "hujiali30001/EdgeCommon"

# 1. 在 WSL 里创建新分支 freecdn-v1.3.9，基于 v1.3.9 commit
print(f"=== Creating branch {NEW_BRANCH} from {V139_SHA} ===")
wsl(
    f"cd {REPO_DIR} && "
    f"git config user.email 'freecdn-bot@example.com' && "
    f"git config user.name 'FreeCDN Bot' && "
    f"git checkout -B {NEW_BRANCH} {V139_SHA}"
)

# 2. 在这个分支上执行 module 重命名
print(f"\n=== Renaming modules on {NEW_BRANCH} ===")
old_m = "github.com/TeaOSLab/EdgeCommon"
new_m = "github.com/hujiali30001/freecdn-common"
old_esc = old_m.replace("/", "\\/").replace(".", "\\.")
new_esc = new_m.replace("/", "\\/")

# go.mod
wsl(f"sed -i 's|^module {old_esc}$|module {new_m}|g' {REPO_DIR}/go.mod")
# 所有 .go 文件
wsl(
    f"find {REPO_DIR} -name '*.go' -not -path '*/.git/*' "
    f"-exec sed -i 's|{old_esc}|{new_esc}|g' {{}} +"
)
# .proto 文件
wsl(
    f"find {REPO_DIR} -name '*.proto' "
    f"-exec sed -i 's|{old_esc}|{new_esc}|g' {{}} +"
)

# 验证
r = wsl(f"grep -r '{old_m}' {REPO_DIR} --include='*.go' | wc -l", check=False)
count = int(r.stdout.strip()) if r.stdout.strip().isdigit() else -1
if count > 0:
    print(f"  [WARN] {count} remaining old refs")
else:
    print(f"  [OK] No old refs remaining")

# 3. 提交
print(f"\n=== Committing ===")
wsl(
    f"cd {REPO_DIR} && "
    f"git add -A && "
    f"git commit -m 'refactor: rename Go module from {old_m} to {new_m} (FreeCDN v0.7.0 stage B)'"
)

# 4. 获取新 commit SHA
r = wsl(f"cd {REPO_DIR} && git rev-parse HEAD", check=False)
new_sha = r.stdout.strip()
print(f"New commit SHA: {new_sha}")

# 5. Push 这个分支
print(f"\n=== Pushing branch {NEW_BRANCH} ===")
auth_url = f"https://{TOKEN}@github.com/{REPO}.git"
wsl(f"cd {REPO_DIR} && git push '{auth_url}' {NEW_BRANCH}")

# 6. 创建 tag v1.3.9-freecdn.1
print(f"\n=== Creating tag {NEW_TAG} ===")
status, data = github_api("POST", f"/repos/{REPO}/git/refs", {
    "ref": f"refs/tags/{NEW_TAG}",
    "sha": new_sha.strip(),
})
if status == 201:
    print(f"  [OK] Tag {NEW_TAG} created")
elif status == 422 and "already exists" in str(data):
    print(f"  [SKIP] Tag already exists")
else:
    print(f"  [ERROR] {status}: {data}")

print(f"\n=== Result ===")
print(f"Branch: {NEW_BRANCH}")
print(f"Tag: {NEW_TAG}")
print(f"Commit: {new_sha.strip()}")
print(f"go.mod replace line:")
print(f"  replace github.com/hujiali30001/freecdn-common => github.com/hujiali30001/EdgeCommon {NEW_TAG}")
