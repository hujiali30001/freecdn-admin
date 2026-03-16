import glob
candidates = (
    glob.glob("C:/*/go/bin/go.exe") +
    glob.glob("C:/Go*/bin/go.exe") +
    glob.glob("C:/Users/*/go/bin/go.exe") +
    glob.glob("C:/Users/*/AppData/Local/go/bin/go.exe")
)
print(candidates)
