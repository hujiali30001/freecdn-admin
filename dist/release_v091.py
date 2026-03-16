"""
v0.9.1 发布脚本：
  1. push freecdn-api  版本号 v0.9.1
  2. push freecdn-node 版本号 v0.9.1
  3. push freecdn-admin（install.sh + const.go 修复 + PLAN.md）
  4. 调用 launch_build_v09.py 构建并上传 Release
"""
import subprocess, os, sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN and len(sys.argv) > 1:
    TOKEN = sys.argv[1]
if not TOKEN:
    print("ERROR: pass token as first argument or set GITHUB_TOKEN"); sys.exit(1)

env = {**os.environ, "HTTP_PROXY": "http://127.0.0.1:4780", "HTTPS_PROXY": "http://127.0.0.1:4780"}
GIT = r"C:\Program Files\Git\bin\git.exe"

def run(cmd, cwd):
    out = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    text = out.stdout.decode("utf-8", errors="replace").strip()
    print(f"$ {' '.join(str(c) for c in cmd)}")
    if text:
        print(text)
    print(f"rc={out.returncode}")
    if out.returncode != 0:
        raise SystemExit(f"FAILED rc={out.returncode}")
    return text

# ─── 1. freecdn-api ───────────────────────────────────────────────────────────
API_DIR = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\src\api"
print("\n=== Push freecdn-api v0.9.1 ===")
run([GIT, "add", r"internal\const\const.go"], API_DIR)
run([GIT, "commit", "-m", "chore: bump version to v0.9.1"], API_DIR)
REMOTE_API = f"https://x-token:{TOKEN}@github.com/hujiali30001/freecdn-api.git"
run([GIT, "push", REMOTE_API, "HEAD:master"], API_DIR)

# ─── 2. freecdn-node ──────────────────────────────────────────────────────────
NODE_DIR = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\src\node"
print("\n=== Push freecdn-node v0.9.1 ===")
run([GIT, "add", r"internal\const\const.go"], NODE_DIR)
run([GIT, "commit", "-m", "chore: bump version to v0.9.1"], NODE_DIR)
REMOTE_NODE = f"https://x-token:{TOKEN}@github.com/hujiali30001/freecdn-node.git"
run([GIT, "push", REMOTE_NODE, "HEAD:master"], NODE_DIR)

# ─── 3. freecdn-admin ─────────────────────────────────────────────────────────
ADMIN_DIR = r"C:\Users\Administrator\.workbuddy\FreeCDN"
print("\n=== Push freecdn-admin v0.9.1 ===")
run([GIT, "add",
     "install.sh",
     r"internal\const\const.go",
     "PLAN.md",
     # dist 工具脚本
     r"dist\release_v091.py",
     ], ADMIN_DIR)

# 检查有没有东西要 commit
status_out = subprocess.run(
    [GIT, "status", "--porcelain"],
    cwd=ADMIN_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
).stdout.decode("utf-8", errors="replace").strip()
print("git status:", status_out or "(clean)")

# 先看看 staged 有什么
staged = subprocess.run(
    [GIT, "diff", "--cached", "--name-only"],
    cwd=ADMIN_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
).stdout.decode("utf-8", errors="replace").strip()
print("staged:", staged)

if staged:
    run([GIT, "commit", "-m", "fix: install.sh bash function order + freecdn-init output; bump to v0.9.1"], ADMIN_DIR)
else:
    print("nothing to commit, skip")

REMOTE_ADMIN = f"https://x-token:{TOKEN}@github.com/hujiali30001/freecdn-admin.git"
run([GIT, "push", REMOTE_ADMIN, "HEAD:main"], ADMIN_DIR)

# ─── 4. 构建 ─────────────────────────────────────────────────────────────────
print("\n=== Building v0.9.1 ===")

# 先更新 launch_build_v09.py 里的版本号常量
build_script = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\launch_build_v09.py"
content = open(build_script, encoding="utf-8").read()
content = content.replace('VERSION = "0.9.0"', 'VERSION = "0.9.1"')
open(build_script, "w", encoding="utf-8").write(content)

proc = subprocess.run(
    [sys.executable, build_script, TOKEN],
    env=env
)
print(f"build rc={proc.returncode}")
if proc.returncode != 0:
    raise SystemExit("build FAILED")

print("\n=== v0.9.1 released successfully ===")
