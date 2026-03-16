"""启动 v0.8.0 构建，继承当前环境并设置代理"""
import subprocess, sys, os

token = sys.argv[1]
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["HTTP_PROXY"]  = "http://127.0.0.1:4780"
env["HTTPS_PROXY"] = "http://127.0.0.1:4780"

log_path = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build_v08.log"
with open(log_path, "w", encoding="utf-8") as log_f:
    result = subprocess.run(
        [
            sys.executable,
            r"C:\Users\Administrator\.workbuddy\FreeCDN\scripts\local_build_release.py",
            "--token", token,
            "--version", "v0.8.0",
            "--arch", "all",
        ],
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )

print("exit:", result.returncode)
# tail 最后 50 行
with open(log_path, encoding="utf-8") as f:
    lines = f.readlines()
print("".join(lines[-50:]))
