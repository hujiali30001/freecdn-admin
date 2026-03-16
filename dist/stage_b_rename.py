#!/usr/bin/env python3
"""
阶段 B：批量执行 Go module 名重命名
策略：通过 GitHub API clone → 批量 sed → push

执行顺序：
  1. EdgeCommon:  TeaOSLab/EdgeCommon  → hujiali30001/freecdn-common
  2. freecdn-api: TeaOSLab/EdgeAPI    → hujiali30001/freecdn-api
  3. freecdn-node: TeaOSLab/EdgeNode  → hujiali30001/freecdn-node
  4. freecdn-admin: go.mod replace 指令更新（module 名已经是 hujiali30001/freecdn-admin）
"""

import subprocess, sys, os, json, base64, http.client, urllib.parse, re, time

TOKEN  = os.environ.get("GITHUB_TOKEN", "")  # set via env: GITHUB_TOKEN=ghp_...
PROXY  = "http://127.0.0.1:4780"
DISTRO = "Ubuntu-24.04"
WORKDIR = "/tmp/freecdn-b"   # WSL 内工作目录

# 替换映射（旧模块名 -> 新模块名）
RENAMES = {
    "github.com/TeaOSLab/EdgeCommon":  "github.com/hujiali30001/freecdn-common",
    "github.com/TeaOSLab/EdgeAPI":     "github.com/hujiali30001/freecdn-api",
    "github.com/TeaOSLab/EdgeNode":    "github.com/hujiali30001/freecdn-node",
    # freecdn-admin 已正确，不需改 module 名
    # 但需要把 replace 里的旧 EdgeCommon 名改成 freecdn-common
}

REPOS = {
    "EdgeCommon": {
        "url": "https://github.com/hujiali30001/EdgeCommon.git",
        "branch": "master",
        "old_module": "github.com/TeaOSLab/EdgeCommon",
        "new_module": "github.com/hujiali30001/freecdn-common",
        # 该仓库中所有 .go 里引用自身的路径
        "self_renames": [
            ("github.com/TeaOSLab/EdgeCommon", "github.com/hujiali30001/freecdn-common"),
        ],
    },
    "freecdn-api": {
        "url": "https://github.com/hujiali30001/freecdn-api.git",
        "branch": "master",
        "old_module": "github.com/TeaOSLab/EdgeAPI",
        "new_module": "github.com/hujiali30001/freecdn-api",
        "self_renames": [
            ("github.com/TeaOSLab/EdgeAPI/",       "github.com/hujiali30001/freecdn-api/"),
            ("github.com/TeaOSLab/EdgeCommon",      "github.com/hujiali30001/freecdn-common"),
        ],
    },
    "freecdn-node": {
        "url": "https://github.com/hujiali30001/freecdn-node.git",
        "branch": "master",
        "old_module": "github.com/TeaOSLab/EdgeNode",
        "new_module": "github.com/hujiali30001/freecdn-node",
        "self_renames": [
            ("github.com/TeaOSLab/EdgeNode/",       "github.com/hujiali30001/freecdn-node/"),
            ("github.com/TeaOSLab/EdgeCommon",      "github.com/hujiali30001/freecdn-common"),
        ],
    },
}


def wsl(script, check=True):
    """在 WSL 内运行 bash 脚本"""
    host_ip = get_host_ip()
    env_prefix = f"export HTTPS_PROXY=http://{host_ip}:4780 HTTP_PROXY=http://{host_ip}:4780; "
    full = env_prefix + script
    r = subprocess.run(
        ["wsl", "-d", DISTRO, "-u", "root", "--", "bash", "-c", full],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in r.stdout.splitlines():
        print(f"  {line}")
    if check and r.returncode != 0:
        print(f"ERROR: WSL command failed (exit {r.returncode})")
        sys.exit(1)
    return r


def get_host_ip():
    r = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "ip", "route", "show", "default"],
        capture_output=True, text=True
    )
    for part in r.stdout.split():
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", part):
            return part
    return "172.24.208.1"


def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-StageB/1.0",
    }
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})


def clone_or_update(repo_name, url, branch):
    """在 WSL 的 WORKDIR 里 clone 或 pull"""
    auth_url = url.replace("https://", f"https://{TOKEN}@")
    repo_path = f"{WORKDIR}/{repo_name}"
    # safe.directory
    wsl(f"git config --global --add safe.directory {repo_path} 2>/dev/null || true")
    r = wsl(f"test -d '{repo_path}/.git' && echo YES || echo NO", check=False)
    if "YES" in r.stdout:
        print(f"[B] Updating {repo_name}...")
        wsl(f"cd '{repo_path}' && git fetch origin {branch} && git reset --hard FETCH_HEAD")
    else:
        print(f"[B] Cloning {repo_name}...")
        wsl(f"mkdir -p {WORKDIR} && git clone --branch {branch} '{auth_url}' '{repo_path}'")


def do_rename(repo_name, cfg):
    """执行模块名批量替换"""
    repo_path = f"{WORKDIR}/{repo_name}"
    print(f"\n[B] === Renaming module in {repo_name} ===")

    # 1. go.mod：改 module 行
    old_m = cfg["old_module"]
    new_m = cfg["new_module"]
    wsl(f"sed -i 's|^module {old_m}$|module {new_m}|g' '{repo_path}/go.mod'")

    # 2. go.mod：改 require / replace 里的引用
    for old_ref, new_ref in cfg["self_renames"]:
        # 转义斜杠用于 sed
        old_esc = old_ref.replace("/", "\\/").replace(".", "\\.")
        new_esc = new_ref.replace("/", "\\/")
        wsl(f"sed -i 's|{old_esc}|{new_esc}|g' '{repo_path}/go.mod'")

    # 3. 所有 .go 文件：批量替换 import 路径
    for old_ref, new_ref in cfg["self_renames"]:
        old_esc = old_ref.replace("/", "\\/").replace(".", "\\.")
        new_esc = new_ref.replace("/", "\\/")
        wsl(
            f"find '{repo_path}' -name '*.go' -not -path '*/vendor/*' "
            f"-exec sed -i 's|{old_esc}|{new_esc}|g' {{}} +"
        )

    # 4. .proto 文件（EdgeCommon 专用）
    if repo_name == "EdgeCommon":
        old_esc = old_m.replace("/", "\\/").replace(".", "\\.")
        new_esc = new_m.replace("/", "\\/")
        wsl(
            f"find '{repo_path}' -name '*.proto' "
            f"-exec sed -i 's|{old_esc}|{new_esc}|g' {{}} +"
        )

    # 5. 验证：grep 确认旧名不再出现（go.sum 除外）
    print(f"[B] Verifying no old references in {repo_name}...")
    r = wsl(
        f"grep -r --include='*.go' '{old_m}' '{repo_path}' | grep -v '.git' | wc -l",
        check=False
    )
    count_line = [l.strip() for l in r.stdout.splitlines() if l.strip().isdigit()]
    count = int(count_line[0]) if count_line else -1
    if count > 0:
        print(f"  [WARN] {count} remaining references to old module name in .go files")
        # 显示前5行
        wsl(f"grep -r --include='*.go' '{old_m}' '{repo_path}' | head -5", check=False)
    else:
        print(f"  [OK] No remaining old module references")

    print(f"[B] go.mod after rename:")
    wsl(f"grep -E '^module|replace|{old_m}|{new_m}' '{repo_path}/go.mod' || true")


def commit_and_push(repo_name, cfg, version="0.7.0"):
    """提交并推送变更"""
    repo_path = f"{WORKDIR}/{repo_name}"
    print(f"\n[B] Committing {repo_name}...")
    commit_msg = f"refactor: rename Go module from {cfg['old_module']} to {cfg['new_module']} (FreeCDN v{version} stage B)"
    wsl(
        f"cd '{repo_path}' && "
        f"git config user.email 'freecdn-bot@example.com' && "
        f"git config user.name 'FreeCDN Bot' && "
        f"git add -A && "
        f"git diff --cached --stat && "
        f"git commit -m '{commit_msg}' || echo 'Nothing to commit'"
    )
    print(f"[B] Pushing {repo_name}...")
    branch = cfg["branch"]
    auth_url = cfg["url"].replace("https://", f"https://{TOKEN}@")
    wsl(f"cd '{repo_path}' && git push '{auth_url}' {branch}")
    print(f"[B] {repo_name} pushed OK")


def update_admin_gomod():
    """
    freecdn-admin 的 module 名已经正确（hujiali30001/freecdn-admin），
    只需更新 go.mod 里的 replace/require 引用 EdgeCommon → freecdn-common，
    以及 .go import 路径。
    直接在 Windows 工作目录操作。
    """
    print(f"\n[B] === Updating freecdn-admin go.mod + imports ===")
    admin_path = "/mnt/c/Users/Administrator/.workbuddy/FreeCDN"
    old = "github.com/TeaOSLab/EdgeCommon"
    new = "github.com/hujiali30001/freecdn-common"
    old_esc = old.replace("/", "\\/").replace(".", "\\.")
    new_esc = new.replace("/", "\\/")

    # go.mod
    wsl(f"sed -i 's|{old_esc}|{new_esc}|g' '{admin_path}/go.mod'")
    print("[B] go.mod updated")

    # .go files
    wsl(
        f"find '{admin_path}/internal' '{admin_path}/cmd' -name '*.go' "
        f"-exec sed -i 's|{old_esc}|{new_esc}|g' {{}} +"
    )
    print("[B] .go imports updated")

    # Verify
    r = wsl(
        f"grep -r --include='*.go' '{old}' '{admin_path}/internal' | wc -l",
        check=False
    )
    count_line = [l.strip() for l in r.stdout.splitlines() if l.strip().isdigit()]
    count = int(count_line[0]) if count_line else -1
    if count > 0:
        print(f"  [WARN] {count} remaining old refs in admin .go files")
    else:
        print(f"  [OK] No remaining old module refs in admin")


def main():
    order = ["EdgeCommon", "freecdn-api", "freecdn-node"]

    for repo_name in order:
        cfg = REPOS[repo_name]
        clone_or_update(repo_name, cfg["url"], cfg["branch"])
        do_rename(repo_name, cfg)
        commit_and_push(repo_name, cfg)
        print(f"\n[B] {repo_name} DONE\n")
        time.sleep(2)  # 给 GitHub API 冷却

    # 最后更新 freecdn-admin（本地仓库）
    update_admin_gomod()
    print("\n[B] All module renames done!")
    print("[B] Next: update version to 0.7.0 and rebuild")


if __name__ == "__main__":
    main()
