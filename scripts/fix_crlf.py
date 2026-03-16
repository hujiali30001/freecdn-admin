import sys

# 检查 install.sh 换行符
with open(r"c:\Users\Administrator\.workbuddy\FreeCDN\install.sh", "rb") as f:
    data = f.read()

crlf_count = data.count(b'\r\n')
lf_count = data.count(b'\n') - crlf_count
print(f"CRLF lines: {crlf_count}, LF-only lines: {lf_count}")

if crlf_count > 0:
    print("需要转换为 LF...")
    data_lf = data.replace(b'\r\n', b'\n')
    with open(r"c:\Users\Administrator\.workbuddy\FreeCDN\install.sh", "wb") as f:
        f.write(data_lf)
    print("已转换为 LF!")
else:
    print("已经是 LF，无需转换")
