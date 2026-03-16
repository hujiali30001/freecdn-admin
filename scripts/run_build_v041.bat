@echo off
echo Starting v0.4.1 build...
"C:\Program Files\Python310\python.exe" C:\Users\Administrator\.workbuddy\FreeCDN\scripts\local_build_release.py --token REDACTED_TOKEN --version v0.4.1 --arch all > C:\Users\Administrator\.workbuddy\FreeCDN\scripts\build_v041_out.txt 2>&1
echo Build exit code: %ERRORLEVEL%
type C:\Users\Administrator\.workbuddy\FreeCDN\scripts\build_v041_out.txt
