$file = "c:\Users\Administrator\.workbuddy\FreeCDN\install.sh"
$bytes = [System.IO.File]::ReadAllBytes($file)
$crlf = [System.Text.Encoding]::UTF8.GetBytes("`r`n")

# 统计 CRLF
$count = 0
for ($i = 0; $i -lt $bytes.Length - 1; $i++) {
    if ($bytes[$i] -eq 13 -and $bytes[$i+1] -eq 10) { $count++ }
}
Write-Host "CRLF count: $count"

if ($count -gt 0) {
    # 读文本，替换换行，以 UTF8 无 BOM 写回
    $content = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
    $content = $content -replace "`r`n", "`n"
    $utf8nobom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($file, $content, $utf8nobom)
    Write-Host "Converted to LF only!"
} else {
    Write-Host "Already LF, no change needed."
}
