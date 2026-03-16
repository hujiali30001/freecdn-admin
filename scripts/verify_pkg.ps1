Set-Location "c:\Users\Administrator\.workbuddy\FreeCDN\dist\build"
$file = "freecdn-v0.1.0-linux-amd64.tar.gz"
$size = (Get-Item $file).Length
Write-Host "Size: $($size / 1MB) MB"

# 验证 gzip 完整性
$result = & tar -tzf $file 2>&1 | Select-Object -Last 5
Write-Host "Tar test (last 5 lines):"
$result
Write-Host "ExitCode: $LASTEXITCODE"
