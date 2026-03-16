import subprocess, os, sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN and len(sys.argv) > 1:
    TOKEN = sys.argv[1]
if not TOKEN:
    print("ERROR: set GITHUB_TOKEN env var or pass as arg")
    sys.exit(1)

PROXY = "http://127.0.0.1:4780"
CWD = r"C:\Users\Administrator\.workbuddy\FreeCDN"
env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY}

def run(cmd, allow_fail=False):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=CWD, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", errors="replace").rstrip(), flush=True)
    print(f"rc={r.returncode}", flush=True)
    if r.returncode != 0 and not allow_fail:
        raise SystemExit("FAILED")
    return r

# 查看当前 log，确认 reset 基点
run(["git", "log", "--oneline", "-8"])

# 找到 "docs: update PLAN.md" 之前的那个 clean commit
# 那两个含 token 的 commit 是：b1e2bd73 (push_plan_v09 等) 和 f43e6336
# 以及 "docs: update PLAN.md" commit 也在那两个之后
# 我们需要把从 7e002042 (feat C-2) 之后的所有 commit squash 成一个
# 7e002042 is the last "good" commit that doesn't contain tokens

# Reset soft to 7e002042 (feat C-2 commit - last clean one)
run(["git", "reset", "--soft", "7e002042"])
run(["git", "status", "--short"])
