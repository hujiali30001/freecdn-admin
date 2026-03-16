@echo off
set PYTHONIOENCODING=utf-8
set HTTPS_PROXY=http://127.0.0.1:4780
set HTTP_PROXY=http://127.0.0.1:4780
if "%GITHUB_TOKEN%"=="" (
    echo ERROR: GITHUB_TOKEN env var is not set. Please run: set GITHUB_TOKEN=ghp_...
    exit /b 1
)
"C:\Program Files\Python310\python.exe" "C:\Users\Administrator\.workbuddy\FreeCDN\dist\update_v07.py" %GITHUB_TOKEN%
