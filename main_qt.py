"""
StreamCap – Qt entry point.

Run this script to launch the Qt-based UI prototype.
The Flet version remains available via main.py.

Usage:
    python main_qt.py
"""

import sys
import os
import asyncio
from qasync import QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QLoggingCategory
from PySide6.QtGui import QFont

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.qt_app_manager import QtApp
from app.qt.main_window import MainWindow

async def start_app():
    """Asynchronously initialize core and launch the main window."""
    # Initialize Core Application Logic
    qt_app = QtApp()
    await qt_app.initialize()
    
    # Create and show window
    window = MainWindow(qt_app)
    qt_app.main_window = window   # Needed for lazy video player creation
    # Ensure it's stored to prevent GC
    global _main_window 
    _main_window = window
    window.show()

    
    # Start periodic tasks
    await qt_app.start_periodic_tasks()
    
    # The asyncio world is now managed by the qasync loop running in main()

def main():
    """Main entry point."""
    # Silence specific Qt warnings that spam the console on some Windows systems
    # especially related to legacy bitmap fonts that fail with DirectWrite.
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false;qt.qpa.fonts=false"
    QLoggingCategory.setFilterRules("qt.qpa.fonts.warning=false")

    # Create the Qt Application
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("StreamCap")

    # Set a robust default font to avoid legacy bitmap font fallbacks (DirectWrite errors)
    default_font = QFont("Segoe UI", 10)
    if not default_font.exactMatch():
        default_font = QFont("Arial", 10)
    app.setFont(default_font)
    
    # Create and set the qasync event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Run the application
    with loop:
        asyncio.ensure_future(start_app())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
