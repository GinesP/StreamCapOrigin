import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from app.qt_app_manager import QtApp
from app.qt.views.settings_view import QtSettingsView
from app.qt.themes.theme import apply_theme

async def main():
    app_qt = QApplication(sys.argv)
    loop = QEventLoop(app_qt)
    asyncio.set_event_loop(loop)
    
    # Initialize Core
    manager = QtApp()
    await manager.initialize()
    
    apply_theme(app_qt, dark=True)
    
    view = QtSettingsView(manager)
    view.resize(800, 600)
    view.show()
    
    # Wait a bit for layout and styling to apply
    await asyncio.sleep(3)
    
    # Take screenshot of the widget itself
    pixmap = view.grab()
    pixmap.save("settings_view_test.png")
    print("Screenshot saved to settings_view_test.png")
    
    # Force process events
    QApplication.processEvents()
    
    QTimer.singleShot(500, app_qt.quit)
    loop.run_forever()

if __name__ == "__main__":
    from PySide6.QtCore import QTimer
    asyncio.run(main())
