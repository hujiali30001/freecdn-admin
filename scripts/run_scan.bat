@echo off
"C:\Program Files\Python310\python.exe" C:\Users\Administrator\.workbuddy\FreeCDN\scripts\scan_pages.py > C:\Users\Administrator\.workbuddy\FreeCDN\scripts\scan_out.txt 2>&1
echo exit=%errorlevel%
type C:\Users\Administrator\.workbuddy\FreeCDN\scripts\scan_out.txt
