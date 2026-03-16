for fname in ['docs/INSTALL.md', 'docs/FAQ.md']:
    path = r'C:\Users\Administrator\.workbuddy\FreeCDN\\' + fname
    print(fname)
    for line in open(path, encoding='utf-8'):
        if 'install.sh' in line and 'bash' in line:
            print(' ', line.rstrip())
