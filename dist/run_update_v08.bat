@echo off
set PYTHONIOENCODING=utf-8
set HTTPS_PROXY=http://127.0.0.1:4780
if "%GITHUB_TOKEN%"=="" echo ERROR: GITHUB_TOKEN env var not set && exit /b 1
C:\Progra~1\Python310\python.exe C:\Users\Administrator\.workbuddy\FreeCDN\dist\update_v08_version.py %GITHUB_TOKEN%

