"""
FreeCDN P5 品牌替换脚本
将 JS/HTML 文件中残留的 GoEdge/goedge 品牌字样替换为 FreeCDN 对应内容
"""
import re, os

FREECDN_ROOT = r'C:\Users\Administrator\.workbuddy\FreeCDN'

# 要处理的文件列表（相对路径）
FILES = [
    r'web\public\js\components\server\http-access-log-search-box.js',
    r'web\public\js\components.src.js',
    r'web\public\js\components.js',
]

# 替换规则：(pattern, replacement, description)
RULES = [
    # 1. 访问日志搜索框 tip 里的示例 URL
    (
        r'查询URL：https://goedge\.cloud/docs',
        '查询URL：https://github.com/hujiali30001/freecdn-admin',
        '访问日志 tip 示例 URL'
    ),
    # 2. WAF 规则正则文档链接（URL 编码形式在 components.src.js 中）
    (
        r'goedge\.cloud/docs/Appendix/Regexp/Index\.md',
        'github.com/google/re2/wiki/Syntax',
        'WAF 正则文档链接'
    ),
    # 3. CNAME 示例域名
    (
        r'比如38b48e4f\.goedge\.cloud',
        '比如abc123.freecdn.io',
        'CNAME 示例域名'
    ),
]

total_changes = 0
for rel_path in FILES:
    fpath = os.path.join(FREECDN_ROOT, rel_path)
    if not os.path.exists(fpath):
        print(f'  SKIP (not found): {rel_path}')
        continue

    content = open(fpath, encoding='utf-8').read()
    original = content
    file_changes = 0

    for pattern, replacement, desc in RULES:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            print(f'  [{rel_path}] {desc}: {count} occurrence(s)')
            file_changes += count

    if file_changes > 0:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  -> Saved {rel_path} ({file_changes} changes)')
        total_changes += file_changes
    else:
        print(f'  [no changes] {rel_path}')

print(f'\nDone. Total changes: {total_changes}')
