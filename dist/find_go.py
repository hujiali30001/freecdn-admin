import subprocess
r = subprocess.run(['where', '/r', 'C:\\', 'go.exe'], capture_output=True, text=True, timeout=30)
for line in r.stdout.split('\n')[:5]:
    if line.strip(): print(line.strip())
if r.stderr: print('ERR:', r.stderr[:200])
