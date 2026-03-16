@echo off
set HTTP_PROXY=http://127.0.0.1:4780
set HTTPS_PROXY=http://127.0.0.1:4780
cd /d C:\Users\Administrator\.workbuddy\FreeCDN
"C:\Program Files\Python310\python.exe" scripts\local_build_release.py --token REDACTED_TOKEN --version v0.4.0 --arch all > C:\build_out.txt 2> C:\build_err.txt
echo EXIT_CODE=%ERRORLEVEL%
