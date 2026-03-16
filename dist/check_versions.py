#!/usr/bin/env python3
"""统计各仓库需要替换的引用数量"""
import urllib.request, json, base64, os

TOKEN = os.environ.get("GITHUB_TOKEN", "")  # set via env: GITHUB_TOKEN=ghp_...
PROXY = "http://127.0.0.1:4780"

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
)

# 检查 freecdn-api 和 freecdn-node 的 const.go 确认版本号
CONSTS = [
    ("hujiali30001/freecdn-api",  "internal/const/const.go"),
    ("hujiali30001/freecdn-node", "internal/const/const.go"),
    ("hujiali30001/EdgeCommon",   "go.mod"),
]

for repo, path in CONSTS:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "check/1.0",
    })
    try:
        r = opener.open(req)
        d = json.loads(r.read())
        content = base64.b64decode(d["content"]).decode()
        print(f"\n=== {repo}/{path} ===")
        for line in content.splitlines():
            if any(x in line for x in ["Version", "module ", "GoEdge"]):
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"ERROR {repo}/{path}: {e}")
