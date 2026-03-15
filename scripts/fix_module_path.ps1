$old = 'github.com/TeaOSLab/EdgeAdmin'
$new = 'github.com/hujiali30001/freecdn-admin'
$root = 'C:\Users\Administrator\.workbuddy\FreeCDN'
$files = Get-ChildItem -Path $root -Recurse -Filter '*.go' | Where-Object { $_.FullName -notmatch '\.git' }
$changed = 0
$total = 0
foreach ($file in $files) {
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
    if ($content.Contains($old)) {
        $newContent = $content.Replace($old, $new)
        [System.IO.File]::WriteAllText($file.FullName, $newContent, [System.Text.Encoding]::UTF8)
        $count = ($content.Split($old).Count - 1)
        $total += $count
        $changed++
        Write-Output "fixed: $($file.FullName.Replace($root+'\', '')) ($count replacements)"
    }
}
Write-Output ""
Write-Output "Done: $changed files changed, $total replacements total"
