import subprocess, os, sys

# Token 从环境变量读取
TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN and len(sys.argv) > 1:
    TOKEN = sys.argv[1]
if not TOKEN:
    print("ERROR: set GITHUB_TOKEN env var or pass token as first argument")
    sys.exit(1)
CWD   = r"C:\Users\Administrator\.workbuddy\FreeCDN"
LOG   = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build_v09.log"

env = {**os.environ,
       "HTTP_PROXY":  "http://127.0.0.1:4780",
       "HTTPS_PROXY": "http://127.0.0.1:4780",
       "PATH": r"C:\Go_temp\go\bin;C:\Program Files\Git\cmd;C:\Program Files\Python310;" + os.environ.get("PATH",""),
       "PYTHONIOENCODING": "utf-8"}

cmd = [
    sys.executable,
    r"C:\Users\Administrator\.workbuddy\FreeCDN\scripts\local_build_release.py",
    "--token", TOKEN,
    "--version", "v0.9.1",
    "--arch", "all",
]

print(f"Running build, logging to {LOG} ...")
with open(LOG, "w", encoding="utf-8") as logf:
    r = subprocess.run(cmd, cwd=CWD, stdout=logf, stderr=subprocess.STDOUT,
                       text=True, env=env)
print(f"Exit code: {r.returncode}")

# 打印最后 30 行
with open(LOG, encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
for l in lines[-30:]:
    print(l, end="")
