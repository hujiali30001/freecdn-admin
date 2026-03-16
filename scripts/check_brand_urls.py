import re
lines = open(r'C:\Users\Administrator\.workbuddy\FreeCDN\web\public\js\components.src.js', encoding='utf-8').readlines()
for idx in [22895, 22905]:
    line = lines[idx]
    matches = re.findall(r'goedge[^\s\"\',<>]{0,40}', line, re.IGNORECASE)
    print(f'Line {idx+1}:', matches[:5])
