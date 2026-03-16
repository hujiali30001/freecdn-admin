import re

path = r'C:\Users\Administrator\.workbuddy\FreeCDN\deploy\docker-entrypoint-admin.sh'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换首次启动时生成 api_admin.yaml 的代码块
old1 = '''  # 生成 edge-admin/configs/api_admin.yaml（admin 连接 api 的认证）
  # 注意：必须用点号写法 rpc.endpoints，不能用 YAML 嵌套的 rpc: endpoints:
  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc.endpoints: [ "http://127.0.0.1:${API_RPC_PORT}" ]
nodeId: "${ADMIN_TOKEN_NODE_ID}"
secret: "${ADMIN_TOKEN_SECRET}"
EOF'''

new1 = '''  # 生成 edge-admin/configs/api_admin.yaml（admin 连接 api 的认证）
  # 注意：必须用嵌套格式 rpc.endpoints（点号格式解析有问题），role=admin 的 token
  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc:
  endpoints:
    - "http://127.0.0.1:${API_RPC_PORT}"
nodeId: "${ADMIN_TOKEN_NODE_ID}"
secret: "${ADMIN_TOKEN_SECRET}"
EOF'''

# 替换重启时更新 api_admin.yaml 的代码块
old2 = '''  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc.endpoints: [ "http://127.0.0.1:${API_RPC_PORT}" ]
nodeId: "${EXIST_NODE_ID}"
secret: "${EXIST_SECRET}"
EOF'''

new2 = '''  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc:
  endpoints:
    - "http://127.0.0.1:${API_RPC_PORT}"
nodeId: "${EXIST_NODE_ID}"
secret: "${EXIST_SECRET}"
EOF'''

new_content = content.replace(old1, new1).replace(old2, new2)
if new_content == content:
    print('WARNING: no replacement made, check strings')
else:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('OK: entrypoint updated')
