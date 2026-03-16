import os, re

# 扫 views + public 下所有文件，找品牌字符串
roots = [
    r'C:\Users\Administrator\.workbuddy\FreeCDN\web\views',
    r'C:\Users\Administrator\.workbuddy\FreeCDN\web\public',
]
brand_re = re.compile(r'GoEdge|goedge\.cloud|goedge\.rip|goedge\.cn|GoEdgeCDN|版权.*GoEdge|copyright.*goedge', re.IGNORECASE)
title_re = re.compile(r'<title>|系统名称|产品名称|品牌|brand|logo')

results = []
for root in roots:
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ['.git']]
        for f in files:
            fpath = os.path.join(dirpath, f)
            try:
                lines = open(fpath, encoding='utf-8', errors='ignore').readlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                if brand_re.search(line):
                    rel = os.path.relpath(fpath, r'C:\Users\Administrator\.workbuddy\FreeCDN')
                    results.append((rel, i, line.strip()[:120]))

results.sort(key=lambda x: x[0])
print(f'Total: {len(results)}')
for rel, lineno, line in results[:60]:
    print(f'  {rel}:{lineno}  {line}')
