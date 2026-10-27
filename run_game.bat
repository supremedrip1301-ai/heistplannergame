@echo off
rem Heist Planner Game - double-click to play.
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python app.py
) else (
    py app.py
)

if errorlevel 1 (
    echo.
    echo The game stopped with an error. Details: logs\heist_planner.log
    pause
)
