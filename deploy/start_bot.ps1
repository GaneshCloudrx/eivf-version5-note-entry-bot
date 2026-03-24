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

Write-Host "Waiting 60 seconds before starting the bot..."
Start-Sleep -Seconds 60

if (-not (Test-Path $mainPath)) {
    throw "Bot entrypoint not found: $mainPath"
}

Set-Location $BotRoot
& $PythonExe $mainPath
