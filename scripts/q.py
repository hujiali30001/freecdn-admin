import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.175.67.168', username='ubuntu', password='FreeCDN2026!', timeout=30)
_, o, _ = ssh.exec_command("mysql -h 127.0.0.1 -u freecdn -p'FreeCDN2026!' freecdn -sNe \"SELECT code,CAST(value AS CHAR) FROM edgeSysSettings;\" 2>/dev/null", timeout=15)
print(o.read().decode())
ssh.close()
