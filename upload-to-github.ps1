# FreeCDN v0.10.0 GitHub Release Upload
# This script uploads the release package to GitHub Releases

param(
    [string]$Version = "0.10.0",
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$Owner = "hujiali30001",
    [string]$Repo = "freecdn-admin"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host "FreeCDN v$Version GitHub Release Upload"
Write-Host "========================================"
Write-Host ""

if (-not $Token) {
    Write-Host "ERROR: GITHUB_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set the token using:"
    Write-Host '  $env:GITHUB_TOKEN = "your_token_here"'
    Write-Host ""
    exit 1
}

$apiUrl = "https://api.github.com/repos/$Owner/$Repo/releases"
$uploadUrl = "https://uploads.github.com/repos/$Owner/$Repo/releases"

$headers = @{
    "Authorization" = "token $Token"
    "Accept" = "application/vnd.github.v3+json"
}

try {
    # Check if release exists
    Write-Host "Checking if release v$Version exists..."
    $releaseUrl = "$apiUrl/tags/v$Version"
    
    $releaseCheck = Invoke-RestMethod -Uri $releaseUrl -Headers $headers -ErrorAction SilentlyContinue
    
    if ($releaseCheck) {
        Write-Host "Release v$Version already exists (ID: $($releaseCheck.id))"
        $releaseId = $releaseCheck.id
    } else {
        Write-Host "Creating new release v$Version..."
        
        # Read release notes
        $releaseNotes = Get-Content -Path "RELEASE_NOTES_v0.10.0.md" -Raw -ErrorAction SilentlyContinue
        if (-not $releaseNotes) {
            $releaseNotes = "FreeCDN v$Version - UI Modern Design System Complete`n`nSee BUILD_GUIDE_v0.10.0.md for details."
        }
        
        $releaseData = @{
            tag_name = "v$Version"
            name = "FreeCDN v$Version - UI Modern Design System"
            body = $releaseNotes
            draft = $false
            prerelease = $false
        } | ConvertTo-Json
        
        $release = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $releaseData
        $releaseId = $release.id
        Write-Host "Release created (ID: $releaseId)"
    }
    
    # Upload assets
    Write-Host ""
    Write-Host "Uploading assets..."
    
    $zipFile = "dist\freecdn-admin-ui-upgrade-v0.10.0.zip"
    $checksumFile = "$zipFile.sha256"
    
    if (-not (Test-Path $zipFile)) {
        throw "ZIP file not found: $zipFile"
    }
    
    if (-not (Test-Path $checksumFile)) {
        throw "Checksum file not found: $checksumFile"
    }
    
    # Upload ZIP
    Write-Host "Uploading: $(Split-Path $zipFile -Leaf)"
    $zipContent = [System.IO.File]::ReadAllBytes($zipFile)
    
    $uploadHeaders = @{
        "Authorization" = "token $Token"
        "Accept" = "application/vnd.github.v3+json"
        "Content-Type" = "application/zip"
    }
    
    $uploadApiUrl = "$uploadUrl/$releaseId/assets?name=$(Split-Path $zipFile -Leaf)"
    Invoke-RestMethod -Uri $uploadApiUrl -Method Post -Headers $uploadHeaders -Body $zipContent | Out-Null
    Write-Host "✅ Uploaded: $(Split-Path $zipFile -Leaf)"
    
    # Upload checksum
    Write-Host "Uploading: $(Split-Path $checksumFile -Leaf)"
    $checksumContent = Get-Content -Path $checksumFile -Raw
    
    $checksumHeaders = @{
        "Authorization" = "token $Token"
        "Accept" = "application/vnd.github.v3+json"
        "Content-Type" = "text/plain"
    }
    
    $uploadApiUrl = "$uploadUrl/$releaseId/assets?name=$(Split-Path $checksumFile -Leaf)"
    Invoke-RestMethod -Uri $uploadApiUrl -Method Post -Headers $checksumHeaders -Body $checksumContent | Out-Null
    Write-Host "✅ Uploaded: $(Split-Path $checksumFile -Leaf)"
    
    # Summary
    Write-Host ""
    Write-Host "========================================"
    Write-Host "Upload Summary"
    Write-Host "========================================"
    Write-Host "Release:        v$Version"
    Write-Host "Release URL:    https://github.com/$Owner/$Repo/releases/tag/v$Version"
    Write-Host "Assets:         2 files uploaded"
    Write-Host "Status:         ✅ COMPLETE"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Visit: https://github.com/$Owner/$Repo/releases/tag/v$Version"
    Write-Host "2. Verify assets are uploaded"
    Write-Host "3. Publish the release (if in draft mode)"
    Write-Host ""
    Write-Host "========================================"
    
} catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $error = $reader.ReadToEnd() | ConvertFrom-Json
        Write-Host "API Error: $($error.message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "✅ Release upload complete!" -ForegroundColor Green
