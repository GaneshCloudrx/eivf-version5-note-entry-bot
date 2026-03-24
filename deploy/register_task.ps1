param(
    [string]$TaskName = "eIVFNoteBot",
    [string]$BotRoot = $null,
    [string]$PythonExe = "python",
    [string]$RepoUrl = "https://github.com/GaneshCloudrx/eivf-version5-note-entry-bot.git",
    [string]$Branch = "main",
    [string]$UserName
)

if (-not $UserName) {
    throw "UserName is required. Example: .\register_task.ps1 -UserName BOTUSER"
}

# Derive BotRoot from script location if not provided
if (-not $BotRoot) { $BotRoot = Split-Path $PSScriptRoot -Parent }

$startScriptPath = Join-Path $PSScriptRoot "start_bot.ps1"
$mainPath        = Join-Path $BotRoot "main.py"

$argumentParts = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$startScriptPath`"",
    "-BotRoot", "`"$BotRoot`"",
    "-PythonExe", "`"$PythonExe`"",
    "-RepoUrl", "`"$RepoUrl`"",
    "-Branch", "`"$Branch`""
)

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument ($argumentParts -join " ")

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $UserName

$principal = New-ScheduledTaskPrincipal `
    -UserId $UserName `
    -LogonType Interactive `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings

Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force
Write-Host "Scheduled task '$TaskName' registered for user '$UserName'."
Write-Host "Bot root : $BotRoot"
Write-Host "Entry    : $mainPath"
