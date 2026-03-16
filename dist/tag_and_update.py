#!/usr/bin/env python3
"""
给 EdgeCommon 仓库打 tag v1.3.10，然后更新三仓库 go.mod replace 为 v1.3.10
"""
import json, http.client, os, sys, base64, re, subprocess

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    # 从本地 git config 读，或直接从命令行参数
    TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""
if not TOKEN:
    print("Usage: python tag_and_update.py <github_token>")
    sys.exit(1)

REPO = "hujiali30001/EdgeCommon"
NEW_TAG = "v1.3.10"
COMMIT_SHA = "45be148915e8804abb9e5664463897162017c8cd"


def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-TagBot/1.0",
    }
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})


# 1. 检查 tag 是否已存在
status, data = github_api("GET", f"/repos/{REPO}/git/refs/tags/{NEW_TAG}")
if status == 200:
    print(f"Tag {NEW_TAG} already exists: {data}")
else:
    # 2. 创建 lightweight tag（直接指向 commit）
    print(f"Creating tag {NEW_TAG} -> {COMMIT_SHA}")
    body = {
        "ref": f"refs/tags/{NEW_TAG}",
        "sha": COMMIT_SHA,
    }
    status, data = github_api("POST", f"/repos/{REPO}/git/refs", body)
    if status == 201:
        print(f"Tag created: {data.get('ref')}")
    else:
        print(f"ERROR creating tag: {status} {data}")
        sys.exit(1)

print(f"\nNow update go.mod replace to: github.com/hujiali30001/EdgeCommon {NEW_TAG}")
print("Run: update go.mod in three repos")


def get_file(repo, path, branch="master"):
    st, d = github_api("GET", f"/repos/{repo}/contents/{path}?ref={branch}")
    if st == 200:
        return base64.b64decode(d["content"]).decode(), d["sha"]
    return None, None


def put_file(repo, path, content, sha, message, branch="master"):
    body = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha,
        "branch": branch,
    }
    st, d = github_api("PUT", f"/repos/{repo}/contents/{path}", body)
    if st in (200, 201):
        print(f"  [OK] {repo}/{path}")
        return True
    print(f"  [ERROR] {st}: {d}")
    return False


# 更新 freecdn-api go.mod
for repo, branch in [
    ("hujiali30001/freecdn-api",  "master"),
    ("hujiali30001/freecdn-node", "master"),
]:
    content, sha = get_file(repo, "go.mod", branch)
    if not content:
        print(f"  ERROR: cannot get {repo}/go.mod")
        continue
    # 找 replace 行并更新版本
    new_content = re.sub(
        r'(replace\s+github\.com/hujiali30001/freecdn-common\s*=>\s*github\.com/hujiali30001/EdgeCommon\s+)\S+',
        r'\g<1>' + NEW_TAG,
        content
    )
    if new_content == content:
        # 尝试查找旧格式
        print(f"  [WARN] pattern not matched in {repo}/go.mod, showing replace lines:")
        for line in content.splitlines():
            if "EdgeCommon" in line or "freecdn-common" in line:
                print(f"    {line}")
    else:
        put_file(repo, "go.mod", new_content, sha,
                 f"chore: update freecdn-common replace to {NEW_TAG}", branch)

# 更新 freecdn-admin go.mod (local)
gomod_path = r"C:\Users\Administrator\.workbuddy\FreeCDN\go.mod"
try:
    with open(gomod_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(replace\s+github\.com/hujiali30001/freecdn-common\s*=>\s*github\.com/hujiali30001/EdgeCommon\s+)\S+',
        r'\g<1>' + NEW_TAG,
        content
    )
    if new_content != content:
        with open(gomod_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("  [OK] freecdn-admin/go.mod updated locally")
    else:
        print("  [WARN] pattern not matched in admin go.mod")
        for line in content.splitlines():
            if "EdgeCommon" in line or "freecdn-common" in line:
                print(f"    {line}")
except Exception as e:
    print(f"  ERROR reading admin go.mod: {e}")

print("\nDone! Now commit admin go.mod change and re-verify build.")
