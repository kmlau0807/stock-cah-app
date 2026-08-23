# ---------------------------------------------------------------------------
# Windows Task Scheduler setup (PowerShell, run as Administrator).
# Creates a daily 08:30 task that runs the detector and emails the report.
# Edit the three paths below to match this machine, then run:
#     powershell -ExecutionPolicy Bypass -File setup_windows.ps1
# ---------------------------------------------------------------------------

$python = "C:\Users\lauki\.workbuddy\binaries\python\versions\3.13.12\python.exe"
$workdir = "C:\Users\lauki\WorkBuddy\2026-08-22-15-59-45\stock_cah_app"
$script  = Join-Path $workdir "main.py"

# Email creds must be present in the environment for --email to succeed.
# Set them once (user scope) with:
#   [System.Environment]::SetEnvironmentVariable("CAH_SMTP_HOST","smtp.xxx.com","User")
#   [System.Environment]::SetEnvironmentVariable("CAH_SMTP_USER","you@x.com","User")
#   [System.Environment]::SetEnvironmentVariable("CAH_SMTP_PASS","app-password","User")
#   [System.Environment]::SetEnvironmentVariable("CAH_EMAIL_FROM","you@x.com","User")
#   [System.Environment]::SetEnvironmentVariable("CAH_EMAIL_TO","you@x.com","User")

$action = New-ScheduledTaskAction -Execute $python -Argument "main.py run --market both --email" -WorkingDirectory $workdir
$trigger = New-ScheduledTaskTrigger -Daily -At "08:30"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun
Register-ScheduledTask -TaskName "StockCAHDaily" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Created scheduled task 'StockCAHDaily' (daily 08:30)."
