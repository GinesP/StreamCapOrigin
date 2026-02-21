@echo off
setlocal

echo ====================================================
echo Building StreamCap Executable
echo ====================================================

:: Check if virtual environment exists
if not exist ".venv\Scripts\flet.exe" (
    echo [ERROR] Virtual environment not found or flet not installed in .venv.
    echo Please run 'pip install flet pyinstaller' first.
    pause
    exit /b 1
)

echo [1/2] Cleaning old build files...
if exist "build" rd /s /q "build"
if exist "dist\StreamCap" rd /s /q "dist\StreamCap"

echo [2/2] Running flet pack...
".venv\Scripts\flet" pack main.py ^
    --name StreamCap ^
    --icon assets/icon.ico ^
    --add-data "app;app" ^
    --add-data "assets;assets" ^
    --add-data "locales;locales" ^
    --add-data "config/default_settings.json;config" ^
    --add-data "config/language.json;config" ^
    --add-data "config/version.json;config" ^
    --debug-console True ^
    -y

if %ERRORLEVEL% equ 0 (
    echo.
    echo ====================================================
    echo Build Successful! 
    echo Executable located at: dist\StreamCap\StreamCap.exe
    echo ====================================================
) else (
    echo.
    echo [ERROR] Build failed. Check the output above for details.
)

pause
