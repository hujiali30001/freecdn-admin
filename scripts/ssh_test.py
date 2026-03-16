import subprocess, sys

result = subprocess.run(
    [
        "git", "push",
        "https://<GITHUB_TOKEN>@github.com/hujiali30001/freecdn-admin.git",
        "HEAD:main"
    ],
    cwd=r"c:\Users\Administrator\.workbuddy\FreeCDN",
    capture_output=True,
    text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RETURNCODE:", result.returncode)
