#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import sys

os.chdir(r"c:\Users\Administrator\.workbuddy\FreeCDN\web\views\@default")

files_to_compile = [
    ("@design_tokens.less", "@design_tokens.css"),
    ("@components_base.less", "@components_base.css"),
    ("@components_data.less", "@components_data.css"),
    ("@components_feedback.less", "@components_feedback.css"),
    ("@globals_utilities.less", "@globals_utilities.css"),
    ("dashboard/index.less", "dashboard/index.css"),
    ("clusters/index.less", "clusters/index.css"),
    ("servers/index.less", "servers/index.css"),
    ("users/features.less", "users/features.css"),
]

print("=" * 60)
print("LESS 编译脚本")
print("=" * 60)

for less_file, css_file in files_to_compile:
    try:
        print(f"\n编译 {less_file}...")
        result = subprocess.run(
            ["lessc", less_file, css_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✓ 编译成功: {css_file}")
        else:
            print(f"✗ 编译失败: {less_file}")
            if result.stderr:
                print(f"  错误: {result.stderr[:200]}")
            if result.stdout:
                print(f"  输出: {result.stdout[:200]}")
    except Exception as e:
        print(f"✗ 错误: {str(e)}")

print("\n" + "=" * 60)
print("编译完成")
print("=" * 60)
