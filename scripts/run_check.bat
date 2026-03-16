@echo off
"C:\Program Files\Python310\python.exe" C:\Users\Administrator\.workbuddy\FreeCDN\scripts\check_release.py > C:\Users\Administrator\.workbuddy\FreeCDN\scripts\release_out.txt 2>&1
echo exit=%errorlevel%
