@echo off
cd /d C:\Users\Administrator\.workbuddy\FreeCDN\scripts
C:\Progra~1\Python310\python.exe upgrade_v041_and_verify.py > upgrade_v041_out.txt 2>&1
echo Exit code: %errorlevel%
type upgrade_v041_out.txt
