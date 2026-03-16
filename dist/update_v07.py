#!/usr/bin/env python3
"""更新三仓库版本号至 0.7.0，并清理 freecdn-admin go.mod"""
import json, http.client, base64, re, sys, os

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN", "")
NEW_VER = "0.7.0"


def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "stageb/1.0",
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
    print(f"  [ERROR] {repo}/{path}: {st}: {d.get('message','')}")
    return False


# ── update freecdn-api const.go ──
for repo in ["hujiali30001/freecdn-api", "hujiali30001/freecdn-node"]:
    content, sha = get_file(repo, "internal/const/const.go")
    if not content:
        print(f"ERROR: cannot fetch {repo}/internal/const/const.go")
        continue
    new_content = re.sub(
        r'(Version\s*=\s*")[^"]+(")',
        f'\\g<1>{NEW_VER}\\2',
        content
    )
    if new_content == content:
        print(f"  [WARN] {repo} const.go unchanged (already {NEW_VER}?)")
        for l in content.splitlines():
            if "Version" in l:
                print(f"    {l}")
    else:
        print(f"Updating {repo} version to {NEW_VER}...")
        put_file(repo, "internal/const/const.go", new_content, sha,
                 f"chore: bump version to {NEW_VER} (stage B)", "master")

# ── fix freecdn-admin go.mod require version ──
gomod_path = r"C:\Users\Administrator\.workbuddy\FreeCDN\go.mod"
with open(gomod_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update require: freecdn-common => v1.3.9-freecdn.2
new_content = re.sub(
    r'(github\.com/hujiali30001/freecdn-common\s+)v[\w\.\-]+',
    r'\g<1>v1.3.9-freecdn.2',
    content
)
if new_content != content:
    with open(gomod_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("  [OK] freecdn-admin go.mod require version aligned to v1.3.9-freecdn.2")
else:
    print("  [INFO] freecdn-admin go.mod require already up to date")

print("\nDone!")
