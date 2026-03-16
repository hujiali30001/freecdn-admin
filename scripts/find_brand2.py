import os, re

# 扫描 views 目录
root = r'C:\Users\Administrator\.workbuddy\FreeCDN\web\views'
results = []
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '.git']]
    for f in files:
        if not f.endswith(('.html',)):
            continue
        fpath = os.path.join(dirpath, f)
        try:
            content = open(fpath, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        matches = re.findall(r'GoEdge|goedge\.cn|goedge\.rip|GoEdge CDN', content)
        if matches:
            rel = os.path.relpath(fpath, root)
            results.append((rel, len(matches), set(matches)))

results.sort(key=lambda x: -x[1])
print(f'Total HTML files with GoEdge: {len(results)}')
for rel, cnt, sample in results[:50]:
    print(f'{cnt:4d}  {rel}  {sample}')
