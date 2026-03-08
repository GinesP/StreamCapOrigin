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
import signal
from qasync import QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QLoggingCategory
from PySide6.QtGui import QFont

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.qt_app_manager import QtApp
from app.qt.main_window import MainWindow

_qt_app = None

async def start_app():
    """Asynchronously initialize core and launch the main window."""
    global _qt_app
    # Initialize Core Application Logic
    _qt_app = QtApp()
    await _qt_app.initialize()
    
    # Create and show window
    window = MainWindow(_qt_app)
    _qt_app.main_window = window   # Needed for lazy video player creation
    # Ensure it's stored to prevent GC
    global _main_window 
    _main_window = window
    window.show()

    # Start periodic tasks
    await _qt_app.start_periodic_tasks()

def main():
    """Main entry point."""
    # Silence specific Qt warnings
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false;qt.qpa.fonts=false"
    QLoggingCategory.setFilterRules("qt.qpa.fonts.warning=false")

    # Create the Qt Application
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("StreamCap")

    # Set a robust default font
    default_font = QFont("Segoe UI", 10)
    if not default_font.exactMatch():
        default_font = QFont("Arial", 10)
    app.setFont(default_font)
    
    # Create and set the qasync event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Run the application
    with loop:
        # Handle Ctrl+C gracefully
        def sigint_handler(*args):
            print("\nInterrupt received, exiting...")
            app.quit()
        
        signal.signal(signal.SIGINT, sigint_handler)
        
        # Periodic timer dummy to allow Python signal handling on Windows
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(500)

        asyncio.ensure_future(start_app())
        
        try:
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanly stop everything
            if _qt_app:
                # We need to run cleanup in the loop before it closes
                loop.run_until_complete(_qt_app.cleanup())
            
            loop.stop()
            app.quit()
    
    print("Application closed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
