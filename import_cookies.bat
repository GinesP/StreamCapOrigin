@echo off
REM Cookie Import Batch Script for StreamCapOrigin
REM This script provides easy access to the cookie import functionality

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   StreamCapOrigin Cookie Import Tool
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Check for different import scripts
set SIMPLE_IMPORTER=%SCRIPT_DIR%import_cookies.py
set ADVANCED_IMPORTER=%SCRIPT_DIR%scripts\cookie_importer.py

if exist "%ADVANCED_IMPORTER%" (
    echo Using advanced cookie importer...
    echo.
    python "%ADVANCED_IMPORTER%" %*
) else if exist "%SIMPLE_IMPORTER%" (
    echo Using simple cookie importer...
    echo.
    python "%SIMPLE_IMPORTER%" %*
) else (
    echo ERROR: Cookie import script not found!
    echo Please ensure the import script exists in:
    echo   - %SIMPLE_IMPORTER%
    echo   - %ADVANCED_IMPORTER%
    pause
    exit /b 1
)

echo.
echo Import process completed.
pause
