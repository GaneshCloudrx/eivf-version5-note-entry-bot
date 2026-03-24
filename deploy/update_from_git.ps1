param(
    [string]$RepoUrl = "https://github.com/GaneshCloudrx/eivf-version5-note-entry-bot.git",
    [string]$Branch = "main",
    [string]$BotRoot = $null,
    [string]$PythonExe = "python",
    [string]$TaskName = "eIVFNoteBot",
    [string]$GitHubToken,
    [switch]$RestartBotTask
)

$ErrorActionPreference = "Stop"

# Derive BotRoot from script location if not provided (deploy folder's parent)
if (-not $BotRoot) { $BotRoot = Split-Path $PSScriptRoot -Parent }

$deployPath    = Join-Path $BotRoot "deploy"
$repoCachePath = Join-Path $deployPath "repo-cache"
$backupPath    = Join-Path $BotRoot "backup\app_previous"
$configEnvPath = Join-Path $BotRoot "config\.env"
$runtimePath   = Join-Path $BotRoot "runtime"
$versionPath   = Join-Path $runtimePath "version.txt"
$logPath       = Join-Path $BotRoot "logs\git-update.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$timestamp $Message"
    Write-Host $line
    Add-Content -Path $logPath -Value $line
}

function Invoke-External {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$FailureMessage,
        [switch]$AllowRobocopyExitCodes
    )
    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if ($AllowRobocopyExitCodes) {
        if ($exitCode -gt 7) { throw "$FailureMessage Exit code: $exitCode" }
        return
    }
    if ($exitCode -ne 0) { throw "$FailureMessage Exit code: $exitCode" }
}

function Get-ConfigValue {
    param([string]$Path, [string]$Key)
    if (-not (Test-Path $Path)) { return $null }
    foreach ($rawLine in Get-Content -Path $Path) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) { continue }
        $parts = $line.Split("=", 2)
        if ($parts[0].Trim() -eq $Key) { return $parts[1].Trim() }
    }
    return $null
}

# Create required directories
New-Item -ItemType Directory -Force -Path $BotRoot        | Out-Null
New-Item -ItemType Directory -Force -Path $deployPath     | Out-Null
New-Item -ItemType Directory -Force -Path $runtimePath    | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BotRoot "logs")   | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BotRoot "backup") | Out-Null

$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $gitCommand) { throw "Git is not installed or not available in PATH." }

$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE     = "Never"

if (-not $GitHubToken) { $GitHubToken = $env:GITHUB_TOKEN }
if (-not $GitHubToken) { $GitHubToken = Get-ConfigValue -Path $configEnvPath -Key "GITHUB_TOKEN" }

$gitRepoUrl = $RepoUrl
if ($GitHubToken -and $RepoUrl -like "https://github.com/*") {
    $escapedToken = [Uri]::EscapeDataString($GitHubToken)
    $gitRepoUrl   = $RepoUrl -replace '^https://github\.com/', "https://x-access-token:$escapedToken@github.com/"
    Write-Log "Using GitHub token for authentication."
} elseif ($RepoUrl -like "https://github.com/*") {
    Write-Log "No GitHub token found. Clone may fail for private repos."
}

Write-Log "Starting update from $RepoUrl ($Branch) into $BotRoot."

$shouldRestartTask = $false
if ($RestartBotTask) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        $shouldRestartTask = $true
        Write-Log "Stopping scheduled task '$TaskName' before update."
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    }
}

try {
    # Fresh clone
    if (Test-Path $repoCachePath) {
        Write-Log "Removing previous repo cache."
        Remove-Item -Path $repoCachePath -Recurse -Force
    }

    Write-Log "Cloning $Branch into repo cache..."
    Invoke-External -FilePath $gitCommand.Source `
        -Arguments @("-c","credential.helper=","-c","core.askPass=",
                     "clone","--depth","1","--branch",$Branch,"--single-branch",
                     $gitRepoUrl, $repoCachePath) `
        -FailureMessage "Git clone failed."

    # Backup current bot files
    if (Test-Path $BotRoot) {
        Write-Log "Backing up current files..."
        New-Item -ItemType Directory -Force -Path $backupPath | Out-Null
        Invoke-External -FilePath "robocopy.exe" `
            -Arguments @($BotRoot, $backupPath, "/MIR","/R:2","/W:2","/NP",
                         "/XD","logs","reports","recordings","__pycache__","runtime","backup","deploy",
                         "/XF","*.pyc","*.log","config.py",".env") `
            -FailureMessage "Backup failed." -AllowRobocopyExitCodes
    }

    # Sync repo root -> BotRoot (preserving local data folders and local-only config)
    Write-Log "Syncing latest code into $BotRoot..."
    Invoke-External -FilePath "robocopy.exe" `
        -Arguments @($repoCachePath, $BotRoot, "/MIR","/R:2","/W:2","/NP",
                     "/XD","logs","reports","recordings","__pycache__","runtime","backup","repo-cache",".git",
                     "/XF","*.pyc","*.log","config.py",".env") `
        -FailureMessage "Code sync failed." -AllowRobocopyExitCodes

    # Install dependencies
    $requirementsPath = Join-Path $BotRoot "requirements.txt"
    if (Test-Path $requirementsPath) {
        Write-Log "Installing Python requirements..."
        Invoke-External -FilePath $PythonExe `
            -Arguments @("-m","pip","install","-r",$requirementsPath) `
            -FailureMessage "pip install failed."
    }

    $updatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitSha = (& $gitCommand.Source -C $repoCachePath rev-parse HEAD).Trim()
    Set-Content -Path $versionPath -Value @(
        "updated_at=$updatedAt"
        "branch=$Branch"
        "commit=$commitSha"
        "repo=$RepoUrl"
    )
    Write-Log "Update complete. Commit: $commitSha"
}
finally {
    if ($shouldRestartTask) {
        Write-Log "Restarting scheduled task '$TaskName'."
        Start-ScheduledTask -TaskName $TaskName
    }
}
