import re, os

base = r'C:\Users\Administrator\.workbuddy\FreeCDN'
files = ['docs/INSTALL.md', 'docs/FAQ.md']

for fname in files:
    path = os.path.join(base, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # | bash -s -- 先处理（避免被下面的规则误匹配）
    new = re.sub(r'\| bash -s --', '| sudo bash -s --', content)
    # | bash（后面不是 -s）改为 | sudo bash
    new = re.sub(r'\| bash(?! -s)(?! \()', '| sudo bash', new)

    if new != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        print(f'[OK] {fname} updated')
    else:
        print(f'[--] {fname} no change')
