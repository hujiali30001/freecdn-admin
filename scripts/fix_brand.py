#!/usr/bin/env python3
"""替换 web/views 下所有 HTML 中的 your-org 占位符"""
import os

ROOT = os.path.join(os.path.dirname(__file__), '..', 'web', 'views')
OLD = 'github.com/your-org/freecdn'
NEW = 'github.com/hujiali30001/freecdn-admin'

count = 0
for dirpath, _, filenames in os.walk(ROOT):
    for fn in filenames:
        if not fn.endswith('.html'):
            continue
        fp = os.path.join(dirpath, fn)
        with open(fp, encoding='utf-8') as f:
            content = f.read()
        if OLD in content:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content.replace(OLD, NEW))
            print(f'Fixed: {fp}')
            count += 1

print(f'\nTotal fixed: {count} files')
