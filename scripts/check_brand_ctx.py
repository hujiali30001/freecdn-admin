import re
lines = open(r'C:\Users\Administrator\.workbuddy\FreeCDN\web\public\js\components.src.js', encoding='utf-8').readlines()
line = lines[22895]  # 0-based, line 22896
# 找 goedge.cloud 前后 80 字符
idx = line.find('goedge.cloud')
print(repr(line[max(0,idx-100):idx+120]))
