@echo off
if "%GITHUB_TOKEN%"=="" (
    echo ERROR: GITHUB_TOKEN env var is not set. Please run: set GITHUB_TOKEN=ghp_...
    exit /b 1
)
"C:\Program Files\Python310\python.exe" C:\Users\Administrator\.workbuddy\FreeCDN\dist\tag_and_update.py %GITHUB_TOKEN%
