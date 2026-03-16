import subprocess, os, sys
env = dict(os.environ)
env['HTTP_PROXY'] = 'http://127.0.0.1:4780'
env['HTTPS_PROXY'] = 'http://127.0.0.1:4780'
env['GIT_TERMINAL_PROMPT'] = '0'
cwd = r'C:\Users\Administrator\.workbuddy\FreeCDN'

token = 'REDACTED_TOKEN'
remote_url = f'https://{token}@github.com/hujiali30001/freecdn-admin.git'

r = subprocess.run(
    ['git', '-c', f'http.proxy=http://127.0.0.1:4780',
     'push', remote_url, 'main'],
    capture_output=True, cwd=cwd, env=env,
    encoding='utf-8', errors='replace', timeout=120
)
print("RC:", r.returncode)
print("OUT:", r.stdout[:500])
print("ERR:", r.stderr[:500])
