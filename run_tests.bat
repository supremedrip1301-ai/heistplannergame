@echo off
rem Runs all unit tests of the Heist Planner Game.
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python -m unittest discover -s tests -v
) else (
    py -m unittest discover -s tests -v
)

pause
