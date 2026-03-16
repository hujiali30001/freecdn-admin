Set-Location "c:\Users\Administrator\.workbuddy\FreeCDN"
$env:GIT_TERMINAL_PROMPT = "0"
$output = & git add install.sh 2>&1
$output | ForEach-Object { Write-Host $_ }
$output = & git commit -m "fix: don't fail if cached pkg can't be deleted after extraction" 2>&1
$output | ForEach-Object { Write-Host $_ }
$output = & git push "https://<GITHUB_TOKEN>@github.com/hujiali30001/freecdn-admin.git" "HEAD:main" 2>&1
$output | ForEach-Object { Write-Host $_ }
Write-Host "Push ExitCode: $LASTEXITCODE"
