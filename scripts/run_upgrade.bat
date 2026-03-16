@echo off
"C:\Program Files\Python310\python.exe" C:\Users\Administrator\.workbuddy\FreeCDN\scripts\upgrade_v040.py > C:\Users\Administrator\.workbuddy\FreeCDN\scripts\upgrade_out.txt 2>&1
echo exit=%errorlevel%
type C:\Users\Administrator\.workbuddy\FreeCDN\scripts\upgrade_out.txt
