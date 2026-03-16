@echo off
"C:\Program Files\Python310\python.exe" -c "
import paramiko, socket
host = '134.175.67.168'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port=22, username='ubuntu', password='REDACTED_SSH_PASS', timeout=15, look_for_keys=False, allow_agent=False)
    print('SSH LOGIN OK')
    _, out, _ = client.exec_command('uname -a')
    print(out.read().decode())
    client.close()
except paramiko.AuthenticationException as e:
    print(f'AUTH FAILED: {e}')
except Exception as e:
    print(f'ERROR: {e}')
"
