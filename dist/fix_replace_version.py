#!/usr/bin/env python3
"""更新三主仓库 go.mod 使用 v1.3.9-freecdn.2 tag"""
import json, http.client, base64, re, sys, os

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN", "")
NEW_VERSION = "v1.3.9-freecdn.2"


def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fix/1.0",
    }
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})


def get_file(repo, path, branch="master"):
    st, d = github_api("GET", f"/repos/{repo}/contents/{path}?ref={branch}")
    if st == 200:
        return base64.b64decode(d["content"]).decode(), d["sha"]
    return None, None


def fix_gomod(content):
    """把 replace 行里的 EdgeCommon 版本替换成 v1.3.9-freecdn.1"""
    # 处理各种格式
    # 1. github.com/hujiali30001/EdgeCommon v<any>
    new = re.sub(
        r'(github\.com/hujiali30001/EdgeCommon\s+)v[\w\.\-]+',
        r'\g<1>' + NEW_VERSION,
        content
    )
    return new


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


for repo, branch in [
    ("hujiali30001/freecdn-api",  "master"),
    ("hujiali30001/freecdn-node", "master"),
]:
    content, sha = get_file(repo, "go.mod", branch)
    if not content:
        print(f"  ERROR: cannot get {repo}/go.mod")
        continue
    new_content = fix_gomod(content)
    if new_content == content:
        print(f"  [WARN] no change in {repo}/go.mod, current replace lines:")
        for line in content.splitlines():
            if "EdgeCommon" in line or "freecdn-common" in line:
                print(f"    {repr(line)}")
    else:
        print(f"Updating {repo}/go.mod...")
        put_file(repo, "go.mod", new_content, sha,
                 f"chore: use EdgeCommon {NEW_VERSION} (freecdn-v1.3.9 branch, module renamed)",
                 branch)

# freecdn-admin local
gomod_path = r"C:\Users\Administrator\.workbuddy\FreeCDN\go.mod"
with open(gomod_path, "r", encoding="utf-8") as f:
    content = f.read()
new_content = fix_gomod(content)
if new_content != content:
    with open(gomod_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("  [OK] freecdn-admin/go.mod updated locally")
else:
    print("  [WARN] no change in admin go.mod")
    for line in content.splitlines():
        if "EdgeCommon" in line or "freecdn-common" in line:
            print(f"    {repr(line)}")

print("\nDone!")
