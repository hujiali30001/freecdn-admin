import os, re

root = r'C:\Users\Administrator\.workbuddy\FreeCDN\internal'
results = []
# 简单扫描：含 GoEdge 的字符串字面量（排除 import/注释/包路径行）
pattern = re.compile(r'"([^"]*(?:GoEdge|goedge\.cn|goedge\.rip)[^"]*)"')

for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['.git']]
    for f in files:
        if not f.endswith('.go'):
            continue
        fpath = os.path.join(dirpath, f)
        try:
            lines = open(fpath, encoding='utf-8', errors='ignore').readlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 跳过纯注释行、import 行、包路径
            if stripped.startswith('//') or stripped.startswith('import') or 'TeaOSLab' in line:
                continue
            for m in pattern.finditer(line):
                val = m.group(1)
                # 跳过包路径
                if 'TeaOSLab' in val or val.startswith('github.com'):
                    continue
                rel = os.path.relpath(fpath, root)
                results.append((rel, i, val))

results.sort(key=lambda x: x[0])
print(f'Total: {len(results)}')
for rel, lineno, val in results:
    print(f'  {rel}:{lineno}  → "{val}"')
