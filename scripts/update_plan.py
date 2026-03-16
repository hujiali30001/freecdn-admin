import re

path = r'C:\Users\Administrator\.workbuddy\FreeCDN\PLAN.md'
content = open(path, encoding='utf-8').read()

# 在"已完成"区域补充 P2/P4/P5 条目
old = "- [x] README.md FreeCDN 化"
new = """- [x] README.md FreeCDN 化
- [x] GitHub Actions release.yml（push tag v* 自动打包 FreeCDN Release）
- [x] GitHub Actions upstream-check.yml（每周检查 GoEdge 上游新 tag，自动创建审计 Issue）
- [x] P5 品牌替换：JS 文件中 goedge.cloud 链接/示例域名全部替换为 FreeCDN"""

content = content.replace(old, new, 1)

open(path, 'w', encoding='utf-8').write(content)
print('done')
