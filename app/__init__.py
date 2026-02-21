import os
import sys

from .initialization.installation_manager import InstallationManager

# When frozen by PyInstaller, sys.executable is the .exe path
# When running from source, use sys.argv[0]
if getattr(sys, 'frozen', False):
    execute_dir = os.path.dirname(sys.executable)
    bundle_dir = sys._MEIPASS
else:
    execute_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
    bundle_dir = execute_dir

__all__ = ["InstallationManager", "execute_dir", "bundle_dir"]
