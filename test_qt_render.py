"""
Qt UI Mock Test for StreamCap.
Renders the Recordings View and saves it to a file.
"""

import sys
import asyncio
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt

# Mock app context
class MockApp:
    def __init__(self):
        self.settings = self
        self.user_config = {"theme_mode": "dark"}
        self.record_manager = self
        self.recordings = []
        self.event_bus = self
        
    def get(self, key, default=None):
        return self.user_config.get(key, default)
        
    def get_duration(self, rec):
        return "00:10:00"
        
    def subscribe(self, *args):
        pass
        
    def publish(self, *args):
        pass
        
    def run_task(self, *args):
        pass

async def run_test():
    from app.qt.views.recordings_view import QtRecordingsView
    from app.models.recording.recording_model import Recording
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    mock_app = MockApp()
    # Add a few mock recordings
    for i in range(5):
        rec = Recording(
            streamer_name=f"Streamer {i}",
            url=f"https://twitch.tv/streamer{i}",
            quality="1080p60",
            status_info="Recording" if i == 0 else "Live"
        )
        rec.rec_id = f"id_{i}"
        rec.is_recording = (i == 0)
        rec.is_live = True
        rec.loop_time_seconds = 60 * (i + 1)
        mock_app.recordings.append(rec)
        
    view = QtRecordingsView(mock_app)
    view.resize(1000, 700)
    view.show()
    
    # Wait for layout and rendering
    await asyncio.sleep(2)
    
    # Grab the widget
    pixmap = view.grab()
    save_path = os.path.abspath("qt_ui_test_render.png")
    pixmap.save(save_path)
    print(f"RENDER_SUCCESS: {save_path}")
    
    view.close()
    app.quit()

if __name__ == "__main__":
    from qasync import QEventLoop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(run_test())
