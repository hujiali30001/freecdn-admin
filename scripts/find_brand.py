import os, re

root = r'C:\Users\Administrator\.workbuddy\FreeCDN\web'
results = []
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '.git']]
    for f in files:
        if not f.endswith(('.html', '.js', '.less', '.css')):
            continue
        fpath = os.path.join(dirpath, f)
        try:
            content = open(fpath, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        matches = re.findall(r'GoEdge|goedge|GOEDGE', content)
        if matches:
            rel = os.path.relpath(fpath, root)
            results.append((rel, len(matches), matches[:3]))

results.sort(key=lambda x: -x[1])
for rel, cnt, sample in results[:40]:
    print(f'{cnt:4d}  {rel}')
print('---')
print(f'Total files with GoEdge: {len(results)}')
