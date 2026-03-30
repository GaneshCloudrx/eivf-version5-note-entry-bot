param(
    [string]$BotRoot = $null,
    [string]$PythonExe = "python",
    [string]$RepoUrl = "https://github.com/GaneshCloudrx/eivf-version5-note-entry-bot.git",
    [string]$Branch = "main",
    [string]$GitHubToken
)

$ErrorActionPreference = "Stop"

# Derive BotRoot from script location if not provided
if (-not $BotRoot) { $BotRoot = Split-Path $PSScriptRoot -Parent }

$updateScriptPath = Join-Path $PSScriptRoot "update_from_git.ps1"
$mainPath         = Join-Path $BotRoot "main.py"

# Pull latest code from GitHub before starting
if (Test-Path $updateScriptPath) {
    try {
        $updateArgs = @{
            BotRoot   = $BotRoot
            PythonExe = $PythonExe
            RepoUrl   = $RepoUrl
            Branch    = $Branch
        }
        if ($GitHubToken) { $updateArgs.GitHubToken = $GitHubToken }
        & $updateScriptPath @updateArgs
    }
    catch {
        Write-Host "Git update failed - starting with existing code."
        Write-Host $_.Exception.Message
    }
}

if (-not (Test-Path $mainPath)) {
    throw "Bot entrypoint not found: $mainPath"
}

Set-Location $BotRoot

# Restart loop - if the bot process dies for any reason, wait and restart
while ($true) {
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Starting bot..."
    try {
        & $PythonExe $mainPath
        $exitCode = $LASTEXITCODE
        Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Bot exited with code: $exitCode"
    }
    catch {
        Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Bot crashed: $($_.Exception.Message)"
    }
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Restarting in 10 seconds..."
    Start-Sleep -Seconds 10
}
