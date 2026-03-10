@echo off
setlocal

echo ====================================================
echo Building StreamCap (Qt) with Nuitka
echo ====================================================

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in "venv".
    pause
    exit /b 1
)

echo [1/3] Checking optional build tools...
:: Asegúrate de que Nuitka está instalado.
"venv\Scripts\python" -m pip install Nuitka zstandard

echo [2/3] Cleaning old build files...
if exist "dist\main_qt.build" rd /s /q "dist\main_qt.build"
if exist "dist\main_qt.dist" rd /s /q "dist\main_qt.dist"

echo [3/3] Compiling to native machine code with Nuitka...
:: Nota: Si es la primera vez, Nuitka preguntará si quieres descargar el compilador en C (MinGW). Escribe 'Yes'.
"venv\Scripts\python" -m nuitka ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --windows-console-mode=disable ^
    --nofollow-import-to=flet ^
    --windows-icon-from-ico="assets/icon.ico" ^
    --include-data-dir="app=app" ^
    --include-data-dir="assets=assets" ^
    --include-data-dir="locales=locales" ^
    --include-data-file="config/default_settings.json=config/" ^
    --include-data-file="config/language.json=config/" ^
    --include-data-file="config/version.json=config/" ^
    --output-dir="dist" ^
    --output-filename="StreamCap.exe" ^
    --product-name="StreamCap" ^
    --file-version="1.0.0" ^
    --product-version="1.0.0" ^
    --company-name="GinesP" ^
    main_qt.py

if %ERRORLEVEL% equ 0 (
    echo ====================================================
    echo Build Successful! 
    echo Native executable located at: dist\main_qt.dist\StreamCap.exe
    echo ====================================================
) else (
    echo.
    echo [ERROR] Build failed. Check the Nuitka logs above.
)

pause
