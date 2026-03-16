import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.175.67.168', username='ubuntu', password='REDACTED_SSH_PASS', timeout=30)
_, o, _ = ssh.exec_command("mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -sNe \"SELECT code,CAST(value AS CHAR) FROM edgeSysSettings;\" 2>/dev/null", timeout=15)
print(o.read().decode())
ssh.close()
