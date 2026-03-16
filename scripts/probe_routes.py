"""
探测服务器上的实际路由路径
"""
import paramiko

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"
BASE = "http://127.0.0.1:7788"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def get_code(path):
    cmd = f"curl -s -o /dev/null -w '%{{http_code}}' '{BASE}{path}' 2>&1"
    _, out, err = ssh.exec_command(cmd, timeout=15)
    return out.read().decode().strip()

# 探测各种可能的路径
test_paths = [
    # 集群相关
    "/clusters/cluster?clusterId=1",
    "/clusters/cluster/nodes?clusterId=1",
    "/clusters/cluster/detail?clusterId=1",
    "/clusters/cluster/settings?clusterId=1",
    # 节点
    "/clusters/cluster/node?nodeId=1",
    "/clusters/cluster/node/detail?nodeId=1",
    "/clusters/cluster/node/detail?clusterId=1&nodeId=1",
    "/clusters/cluster/node/settings?nodeId=1",
    "/clusters/cluster/node/settings/cache?nodeId=1",
    "/clusters/cluster/node/cache?nodeId=1",
    "/clusters/cluster/node/logs?nodeId=1",
    "/clusters/cluster/node/log?nodeId=1",
    # HTTP服务
    "/servers/server?serverId=1",
    "/servers/server/detail?serverId=1",
    "/servers/server/settings?serverId=1",
    "/servers/server/settings/reverseProxy?serverId=1",
    "/servers/server/origins?serverId=1",
    "/servers/server/settings/https?serverId=1",
    "/servers/server/https?serverId=1",
    "/servers/server/settings/cache?serverId=1",
    "/servers/server/cache?serverId=1",
    "/servers/server/settings/rewrite?serverId=1",
    "/servers/server/rewrites?serverId=1",
    "/servers/server/settings/headers?serverId=1",
    "/servers/server/headers?serverId=1",
    "/servers/server/settings/access?serverId=1",
    "/servers/server/access?serverId=1",
    "/servers/server/settings/waf?serverId=1",
    "/servers/server/waf?serverId=1",
    "/servers/server/stat?serverId=1",
    # 证书
    "/servers/certs/cert?certId=1",
    "/servers/certs/certPopup?certId=1",
    "/servers/certs/certDetail?certId=1",
    # 用户
    "/users/user?userId=1",
    "/users/user/detail?userId=1",
    # DNS
    "/dns/domain/records?domainId=1",
    "/dns/domain?domainId=1",
]

print("路由探测结果（无 cookie）:")
print(f"{'状态码':<8} {'路径'}")
print("-" * 60)
for path in test_paths:
    code = get_code(path)
    marker = ""
    if code == "200":
        marker = " <== 直接OK"
    elif code == "403":
        marker = " <== 需登录(路由存在)"
    elif code == "302":
        marker = " <== 重定向"
    elif code == "404":
        marker = "  (路由不存在)"
    print(f"[{code}]    {path}{marker}")

ssh.close()
print("\n探测完毕。")
