@echo off
powershell -ExecutionPolicy Bypass -File "c:\Users\Administrator\.workbuddy\FreeCDN\scripts\fix_crlf.ps1"
echo EXIT: %errorlevel%
