import subprocess, os, sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN and len(sys.argv) > 1:
    TOKEN = sys.argv[1]

PROXY = "http://127.0.0.1:4780"
CWD = r"C:\Users\Administrator\.workbuddy\FreeCDN"
env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY}

def run(cmd, allow_fail=False):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=CWD, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8", errors="replace").rstrip()
    if out: print(out, flush=True)
    print(f"rc={r.returncode}", flush=True)
    if r.returncode != 0 and not allow_fail:
        raise SystemExit(f"FAILED")
    return r

run(["git", "status", "--short"])
run(["git", "log", "--oneline", "-4"])

run(["git", "add",
     "PLAN.md",
     "dist/build_check.py",
     "dist/check_exists.py",
     "dist/find_go.py",
     "dist/launch_build_v09.py",
     "dist/push_admin_v09.py",
     "dist/push_plan_v09.py",
     "dist/push_version_v09.py",
     "dist/debug_push.py",
     "dist/fix_tokens.py",
     "dist/final_push_v09.py",
])

run(["git", "status", "--short"])
