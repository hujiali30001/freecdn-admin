path = r'C:\Users\Administrator\.workbuddy\FreeCDN\deploy\README.md'
with open(path, encoding='utf-8') as f:
    content = f.read()

old = '**重置初始化（已有数据但想重新初始化）**'

new = '''**edge-api 报 "wrong token role, expect: api, but give admin"**

`api_admin.yaml` 格式不正确，或者 token 对不上。正确的格式是嵌套写法：
```yaml
rpc:
  endpoints:
    - "http://127.0.0.1:8003"
nodeId: "你的nodeId"
secret: "你的secret"
```

删除 `admin_configs` 卷重新初始化即可（entrypoint 会自动生成正确格式）：
```bash
docker compose -f deploy/docker-compose.yml down
docker volume rm freecdn_admin_configs
docker compose -f deploy/docker-compose.yml up -d
```

---

**重置初始化（已有数据但想重新初始化）**'''

new_content = content.replace(old, new)
if new_content == content:
    print('WARNING: no change')
else:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('OK: README.md updated')
