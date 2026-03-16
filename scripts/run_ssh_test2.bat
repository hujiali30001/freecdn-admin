@echo off
cd /d c:\Users\Administrator\.workbuddy\FreeCDN
git push https://<GITHUB_TOKEN>@github.com/hujiali30001/freecdn-admin.git HEAD:main
echo exit code: %errorlevel%
