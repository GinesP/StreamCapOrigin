# Windows distribution

StreamCap uses a one-command Windows distribution flow:

```powershell
.\package_windows_installer.bat
```

This script runs the Nuitka build first and compiles the Inno Setup installer only if the build succeeds.

You can still run the two steps manually:

1. Build the Qt application with Nuitka:

   ```powershell
   .\build_qt_nuitka.bat
   ```

   This creates the application folder at `dist\main_qt.dist`.

2. Compile the Inno Setup installer:

   ```powershell
   ISCC.exe .\installer\StreamCap.iss
   ```

   The installer output is written to `dist\installer`.

If `ISCC.exe` is not on `PATH`, `package_windows_installer.bat` also checks common Inno Setup 6 install paths, including:

```text
%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
```

You can override detection with:

```powershell
$env:ISCC_EXE = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
.\package_windows_installer.bat
```

## Update behavior

The installer updates only the program files under the selected install directory. User data is stored outside the install directory at:

```text
%LOCALAPPDATA%\StreamCap\config
```

These files are preserved when installing a newer version over an existing installation:

- `user_settings.json`
- `cookies.json`
- `accounts.json`
- `web_auth.json`
- `recordings.db`
- SQLite sidecar files and existing backups

On first launch after this change, StreamCap copies legacy mutable configuration from `<install_dir>\config` to `%LOCALAPPDATA%\StreamCap\config` only when the destination file does not already exist.

## Uninstall behavior

The uninstaller preserves user data by default. During uninstall it asks whether `%LOCALAPPDATA%\StreamCap` should also be deleted.
