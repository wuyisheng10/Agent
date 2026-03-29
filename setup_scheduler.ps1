# ============================================================
# Windows Task Scheduler Setup Script
# File: C:\Users\user\claude AI_Agent\setup_scheduler.ps1
# Run as Administrator
# ============================================================

$BaseDir   = "C:\Users\user\claude AI_Agent"
$AgentsDir = "$BaseDir\agents"
$LogDir    = "$BaseDir\logs"
$Python    = "python"

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Amway AI Agent - Task Scheduler Setup" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

# Task 1: Daily Pipeline (08:00)
$action1  = New-ScheduledTaskAction -Execute $Python -Argument "`"$AgentsDir\04_crew_main.py`" --mode pipeline" -WorkingDirectory $AgentsDir
$trigger1 = New-ScheduledTaskTrigger -Daily -At "08:00"
Register-ScheduledTask -TaskName "Amway_AI_DailyPipeline" -Description "Daily: scraper + scoring + message" -Action $action1 -Trigger $trigger1 -RunLevel Highest -Force
Write-Host "OK Task1: Daily Pipeline 08:00" -ForegroundColor Green

# Task 2: LINE Bot Send (09:00)
$action2  = New-ScheduledTaskAction -Execute $Python -Argument "`"$AgentsDir\05_line_bot.py`"" -WorkingDirectory $AgentsDir
$trigger2 = New-ScheduledTaskTrigger -Daily -At "09:00"
Register-ScheduledTask -TaskName "Amway_AI_LineSend" -Description "Daily LINE Bot send Day1/3/7" -Action $action2 -Trigger $trigger2 -RunLevel Highest -Force
Write-Host "OK Task2: LINE Send 09:00" -ForegroundColor Green

# Task 3: LINE Webhook (AtStartup)
$action3  = New-ScheduledTaskAction -Execute $Python -Argument "`"$AgentsDir\06_line_webhook.py`"" -WorkingDirectory $AgentsDir
$trigger3 = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "Amway_AI_LineWebhook" -Description "Auto-start LINE Webhook server" -Action $action3 -Trigger $trigger3 -RunLevel Highest -Force
Write-Host "OK Task3: LINE Webhook at startup" -ForegroundColor Green

# Task 4: C# Watcher (AtStartup)
$WatcherExe = "$BaseDir\monitor\bin\Release\net8.0\AmwayWatcher.exe"
$action4    = New-ScheduledTaskAction -Execute $WatcherExe -WorkingDirectory "$BaseDir\monitor"
$trigger4   = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "Amway_AI_CSharpWatcher" -Description "Auto-start C# JSON Watcher" -Action $action4 -Trigger $trigger4 -RunLevel Highest -Force
Write-Host "OK Task4: C# Watcher at startup" -ForegroundColor Green

# Task 5: Weekly Report (Monday 07:30)
$action5  = New-ScheduledTaskAction -Execute $Python -Argument "`"$AgentsDir\04_crew_main.py`" --mode crew" -WorkingDirectory $AgentsDir
$trigger5 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "07:30"
Register-ScheduledTask -TaskName "Amway_AI_WeeklyReport" -Description "Weekly CrewAI deep analysis every Monday" -Action $action5 -Trigger $trigger5 -RunLevel Highest -Force
Write-Host "OK Task5: Weekly Report Monday 07:30" -ForegroundColor Green

# Show all tasks
Write-Host ("`n" + "=" * 60) -ForegroundColor Cyan
Write-Host "All Scheduled Tasks:" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

Get-ScheduledTask | Where-Object { $_.TaskName -like "Amway_AI_*" } |
    Select-Object TaskName, State |
    Format-Table -AutoSize

Write-Host "Done! All tasks created successfully." -ForegroundColor Green
