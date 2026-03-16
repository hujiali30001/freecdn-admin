@echo off
cd /d C:\Users\Administrator\.workbuddy\FreeCDN
echo === 本地 git log ===
git log --oneline -8
echo.
echo === git status ===
git status
