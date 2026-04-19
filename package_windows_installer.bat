@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

set "INNO_SCRIPT=installer\StreamCap.iss"
set "BUILD_EXE=dist\main_qt.dist\StreamCap.exe"
set "STREAMCAP_SKIP_BUILD_PAUSE=1"

echo ====================================================
echo Building StreamCap and packaging Windows installer
echo ====================================================

echo [1/3] Running Nuitka build...
call "%ROOT_DIR%build_qt_nuitka.bat"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Nuitka build failed. Installer will not be compiled.
    exit /b 1
)

if not exist "%BUILD_EXE%" (
    echo.
    echo [ERROR] Expected build output not found: %BUILD_EXE%
    exit /b 1
)

echo.
echo [2/3] Locating Inno Setup compiler...
if defined ISCC_EXE (
    if exist "%ISCC_EXE%" goto :compile_installer
    echo [ERROR] ISCC_EXE is set but the file does not exist: %ISCC_EXE%
    exit /b 1
)

where ISCC.exe >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "ISCC_EXE=ISCC.exe"
    goto :compile_installer
)

if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    goto :compile_installer
)

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    goto :compile_installer
)

if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
    goto :compile_installer
)

echo [ERROR] ISCC.exe was not found.
echo Install Inno Setup 6 or set ISCC_EXE to the full ISCC.exe path.
echo Example:
echo   set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
exit /b 1

:compile_installer
echo Found Inno Setup compiler: %ISCC_EXE%

if not exist "%INNO_SCRIPT%" (
    echo [ERROR] Installer script not found: %INNO_SCRIPT%
    exit /b 1
)

echo.
echo [3/3] Compiling installer...
"%ISCC_EXE%" "%INNO_SCRIPT%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Installer compilation failed.
    exit /b 1
)

echo.
echo ====================================================
echo Windows installer created successfully.
echo Output directory: dist\installer
echo ====================================================
exit /b 0
