#!/usr/bin/env python3
"""批量替换所有 .go 文件中的旧 module 路径"""
import os

old = 'github.com/TeaOSLab/EdgeAdmin'
new = 'github.com/hujiali30001/freecdn-admin'
count = 0
files_changed = 0

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for root, dirs, files in os.walk(root_dir):
    dirs[:] = [d for d in dirs if d not in ('.git', 'dist', 'build')]
    for f in files:
        if not f.endswith('.go'):
            continue
        path = os.path.join(root, f)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
            if old in content:
                new_content = content.replace(old, new)
                with open(path, 'w', encoding='utf-8', newline='') as fh:
                    fh.write(new_content)
                n = content.count(old)
                count += n
                files_changed += 1
                print(f'  fixed: {os.path.relpath(path, root_dir)} ({n} replacements)')
        except Exception as e:
            print(f'  error: {path}: {e}')

print(f'\nDone: {files_changed} files changed, {count} replacements total')
