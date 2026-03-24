# Deployment

## Overview

Scripts pull the latest code from GitHub before the bot starts. No hardcoded paths — all scripts derive the bot root from their own location (`$PSScriptRoot\..`), so they work wherever the project folder is placed.

**Repo:** https://github.com/GaneshCloudrx/eivf-version5-note-entry-bot  
**Branch:** `main`  
**Task name:** `eIVFNoteBot`

---

## One-Time VM Setup

**Requirements:**
- Git installed and available in `PATH`
- Python installed on the VM
- AutoLogon configured for the bot Windows account
- *(Optional)* `config\.env` containing `GITHUB_TOKEN=<token>` for private repo access

**Step 1 — Configure VM for unattended UI automation (run once as Administrator):**

```powershell
powershell -ExecutionPolicy Bypass -File "deploy\configure_vm.ps1"
```

**Step 2 — Register the bot as a logon-triggered scheduled task:**

```powershell
powershell -ExecutionPolicy Bypass -File "deploy\register_task.ps1" -UserName "localadmin"
```

With a custom Python path:

```powershell
powershell -ExecutionPolicy Bypass -File "deploy\register_task.ps1" `
    -UserName "localadmin" `
    -PythonExe "C:\Users\localadmin\AppData\Local\Programs\Python\Python313\python.exe"
```

---

## Normal Update Flow

1. Push code changes to the `main` branch on GitHub.
2. Restart the VM or log back into the bot user session.
3. The scheduled task runs `start_bot.ps1` → pulls latest code → starts `main.py`.

---

## Manual Hotfix (No Restart)

Stop the bot, pull latest code, and restart:

```powershell
powershell -ExecutionPolicy Bypass -File "deploy\update_from_git.ps1" -RestartBotTask
```

With explicit GitHub token:

```powershell
powershell -ExecutionPolicy Bypass -File "deploy\update_from_git.ps1" `
    -GitHubToken "ghp_xxxxxxxxxxxx" `
    -RestartBotTask
```

---

## How It Works

| Script | Purpose |
|---|---|
| `configure_vm.ps1` | Disables screen saver, lock screen, sleep — required for unattended UI automation |
| `register_task.ps1` | Registers `eIVFNoteBot` as a logon-triggered Windows Scheduled Task |
| `start_bot.ps1` | Runs `update_from_git.ps1` then starts `main.py` |
| `update_from_git.ps1` | Clones latest `main` branch, syncs code to bot root, runs `pip install` |
| `cleanup_recordings.ps1` | Deletes recording files older than 24h from the `recordings\` folder |

**What `update_from_git.ps1` preserves (never overwritten):**

- `logs\` — local log files
- `reports\` — CSV patient reports
- `recordings\` — screen recordings
- `runtime\` — runtime state files
- `config\.env` — credentials and local config (never in GitHub)

**GitHub token resolution order in `update_from_git.ps1`:**
1. `-GitHubToken` parameter
2. `GITHUB_TOKEN` environment variable
3. `GITHUB_TOKEN` key in `config\.env`
