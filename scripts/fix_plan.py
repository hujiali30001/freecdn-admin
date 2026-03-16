path = r'C:\Users\Administrator\.workbuddy\FreeCDN\PLAN.md'
with open(path, encoding='utf-8') as f:
    content = f.read()

old = '- `edgeAPITokens.role=admin` 的 nodeId 必须与 `api_admin.yaml` 中一致'
new = ('- `api_admin.yaml` 必须用嵌套 YAML 格式（`rpc:` / `  endpoints:` / `    - "..."``），'
       '点号格式 `rpc.endpoints: [...]` 会导致 edge-admin 解析失败，报 "wrong token role"\n'
       '- `edgeAPITokens.role=admin` 的 nodeId 必须与 `api_admin.yaml` 中一致')

new_content = content.replace(old, new)
if new_content == content:
    print('WARNING: no change')
else:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('OK: PLAN.md updated')
