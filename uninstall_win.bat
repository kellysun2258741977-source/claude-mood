@echo off
setlocal EnableDelayedExpansion

set "SRC=%~dp0"
if "!SRC:~-1!"=="\" set "SRC=!SRC:~0,-1!"
set "PY=!SRC!\.venv\Scripts\python.exe"

echo  Removing ClaudeMood...

:: Stop running instance (best-effort)
taskkill /f /fi "IMAGENAME eq python.exe" /fi "WINDOWTITLE eq ClaudeMood*" >nul 2>&1

:: Remove Task Scheduler entry
schtasks /delete /tn "ClaudeMood" /f >nul 2>&1

:: Remove hooks from settings.json
if exist "!PY!" (
    "!PY!" "!SRC!\hook_win.py" --uninstall
) else (
    echo  Note: venv not found — remove hooks manually from ~/.claude/settings.json
)

:: Delete state file
del /f "%USERPROFILE%\.claude\cc-status.json" >nul 2>&1

echo.
echo  Done. You can now delete the claude-mood folder.
pause
