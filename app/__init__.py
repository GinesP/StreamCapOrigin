import os
import sys

# When frozen by PyInstaller, sys.executable is the .exe path
# When running from source, use sys.argv[0]
if getattr(sys, 'frozen', False):
    execute_dir = os.path.dirname(sys.executable)
    bundle_dir = sys._MEIPASS
else:
    execute_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
    bundle_dir = execute_dir

# NOTE: InstallationManager is NOT imported here intentionally.
# Importing it at package level would trigger a chain of imports (including Flet)
# before the application has a chance to initialize, causing unwanted windows.
# It is imported lazily by app_manager.py and qt_app_manager.py when needed.
__all__ = ["execute_dir", "bundle_dir"]
