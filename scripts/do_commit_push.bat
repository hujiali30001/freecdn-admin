@echo off
cd /d C:\Users\Administrator\.workbuddy\FreeCDN
git commit -m "fix(docker): api_admin.yaml nested rpc format + prod compose rewrite"
git push https://<GITHUB_TOKEN>@github.com/hujiali30001/freecdn-admin.git main
