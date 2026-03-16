@echo off
set PYTHONIOENCODING=utf-8
set HTTP_PROXY=http://127.0.0.1:4780
set HTTPS_PROXY=http://127.0.0.1:4780
if "%GITHUB_TOKEN%"=="" echo ERROR: GITHUB_TOKEN env var not set && exit /b 1
"C:\Program Files\Python310\python.exe" C:\Users\Administrator\.workbuddy\FreeCDN\scripts\local_build_release.py --token %GITHUB_TOKEN% --version v0.7.0 --arch all > C:\Users\Administrator\.workbuddy\FreeCDN\dist\build_v07.log 2>&1
echo Exit: %ERRORLEVEL%
type C:\Users\Administrator\.workbuddy\FreeCDN\dist\build_v07.log

