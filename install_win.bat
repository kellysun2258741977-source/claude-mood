@echo off
setlocal EnableDelayedExpansion

:: ClaudeMood — Windows installer
:: Run this from the cloned claude-mood directory.
:: Requires Python 3.8+ on PATH (https://python.org).

set "SRC=%~dp0"
if "!SRC:~-1!"=="\" set "SRC=!SRC:~0,-1!"
set "VENV=!SRC!\.venv"
set "PY=!VENV!\Scripts\python.exe"

echo.
echo  ==========================================
echo   ClaudeMood — Windows Installer
echo  ==========================================
echo.

:: ── 1. Find Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python 3.8+ not found.
    echo  Install from https://python.org — check "Add Python to PATH".
    pause & exit /b 1
)
echo  [1/4] Python found.

:: ── 2. Virtual environment ──────────────────────────────────────────────────
echo  [2/4] Creating virtual environment...
python -m venv "!VENV!"
if errorlevel 1 (
    echo  ERROR: venv creation failed.
    pause & exit /b 1
)

:: ── 3. Install dependencies ─────────────────────────────────────────────────
echo  [3/4] Installing Pillow, pystray, playsound...
"!PY!" -m pip install -q --upgrade pip
"!PY!" -m pip install -q Pillow pystray playsound
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause & exit /b 1
)

:: ── 4. Register Claude Code hooks ───────────────────────────────────────────
echo  [4/4] Registering hooks in ~/.claude/settings.json...
"!PY!" "!SRC!\hook_win.py" --install "!SRC!"
if errorlevel 1 (
    echo  ERROR: hook registration failed.
    pause & exit /b 1
)

:: ── 5. Register autostart via Task Scheduler ────────────────────────────────
echo  Registering startup task...
schtasks /delete /tn "ClaudeMood" /f >nul 2>&1
schtasks /create /tn "ClaudeMood" ^
    /tr "\"!PY!\" \"!SRC!\systray.py\"" ^
    /sc ONLOGON /rl LIMITED /f >nul 2>&1
if errorlevel 1 (
    echo  Note: Task Scheduler registration failed.
    echo        Start manually: "!PY!" "!SRC!\systray.py"
) else (
    echo  Startup task registered — ClaudeMood will start on every login.
)

:: ── 6. Launch now ───────────────────────────────────────────────────────────
echo.
echo  Starting ClaudeMood...
start /b "" "!PY!" "!SRC!\systray.py"

echo.
echo  ==========================================
echo   Done! Look for ClaudeMood in the system
echo   tray (bottom-right, near the clock).
echo.
echo   To uninstall: run uninstall_win.bat
echo  ==========================================
echo.
pause
