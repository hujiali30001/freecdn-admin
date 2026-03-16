path = r'C:\Users\Administrator\.workbuddy\FreeCDN\deploy\docker-entrypoint-admin.sh'
lines = open(path, encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'rpc' in l or 'endpoints' in l:
        print(i, l.rstrip())
