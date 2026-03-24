$dir = Join-Path (Split-Path $PSScriptRoot -Parent) "recordings"

if (-not (Test-Path $dir)) {
    Write-Host "Recordings folder not found: $dir"
    exit 0
}

$files  = Get-ChildItem $dir
$sum    = ($files | Measure-Object -Property Length -Sum).Sum
$mb     = [math]::Round($sum / 1MB, 1)
Write-Host "Total: $mb MB across $($files.Count) files"

$cutoff = (Get-Date).AddHours(-24)
$old    = $files | Where-Object { $_.LastWriteTime -lt $cutoff }
$oldSum = ($old | Measure-Object -Property Length -Sum).Sum
$oldMB  = [math]::Round($oldSum / 1MB, 1)
Write-Host "Older than 24h: $oldMB MB across $($old.Count) files"

$old | Remove-Item -Force
Write-Host "Deleted $($old.Count) old files - freed $oldMB MB"
