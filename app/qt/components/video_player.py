"""
Qt Video Player for StreamCap.

Plays recorded videos and live stream previews using QtMultimedia.
"""

import os
from PySide6.QtCore import Qt, QUrl, QTime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.utils.logger import logger


class QtVideoPlayer(QDialog):
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app = app_context
        self.setWindowTitle("Video Player")
        self.resize(900, 600)
        self.setMinimumSize(640, 480)
        
        self._setup_ui()
        self._setup_player()
        
        self._is_playing = False
        self._duration = 0

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Video Render Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.video_widget)
        
        # 2. Controls Area
        controls_layout = QVBoxLayout()
        
        # Seek bar
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self._on_seek_moved)
        controls_layout.addWidget(self.seek_slider)
        
        # Buttons row
        btns_row = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setFixedWidth(100)
        self.play_btn.clicked.connect(self._toggle_playback)
        btns_row.addWidget(self.play_btn)
        
        self.time_label = QLabel("00:00 / 00:00")
        btns_row.addWidget(self.time_label)
        
        self.fullscreen_btn = QPushButton("📺 Fullscreen")
        self.fullscreen_btn.setFixedWidth(110)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        btns_row.addWidget(self.fullscreen_btn)
        
        btns_row.addStretch()
        
        # Action buttons (Copy, Open Room)
        self.actions_layout = QHBoxLayout()
        btns_row.addLayout(self.actions_layout)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btns_row.addWidget(self.close_btn)
        
        controls_layout.addLayout(btns_row)
        self.layout.addLayout(controls_layout)
        
        # Double click on video to toggle fullscreen
        self.video_widget.mouseDoubleClickEvent = self._on_video_double_click

    def _setup_player(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        # Signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.errorOccurred.connect(self._on_error)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("📺 Fullscreen")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("🗗 Windowed")

    def _on_video_double_click(self, event):
        self._toggle_fullscreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self._toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    async def preview_video(self, source, is_file_path=True, room_url=None):
        """Prepare and show the video."""
        self.stop()
        
        # Update title
        filename = os.path.basename(source) if is_file_path else "Live Stream"
        self.setWindowTitle(f"Playing: {filename}")
        
        # Update action buttons
        self._update_actions(source, room_url)
        
        if is_file_path:
            file_url = QUrl.fromLocalFile(source)
            self.player.setSource(file_url)
        else:
            self.player.setSource(QUrl(source))
            
        self.show()
        self.player.play()

    def _update_actions(self, source, room_url):
        # Clear previous actions
        for i in reversed(range(self.actions_layout.count())): 
            self.actions_layout.itemAt(i).widget().setParent(None)
            
        if room_url:
            btn = QPushButton("🌐 Open Room")
            btn.clicked.connect(lambda: self.app.page.launch_url(room_url)) # Flet compat? 
            # In QtMainWindow we might need another way to launch URL
            def open_room():
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl(room_url))
            btn.clicked.disconnect()
            btn.clicked.connect(open_room)
            self.actions_layout.addWidget(btn)
            
        copy_btn = QPushButton("📋 Copy Source")
        def copy_to_clip():
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(source)
        copy_btn.clicked.connect(copy_to_clip)
        self.actions_layout.addWidget(copy_btn)

    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸ Pause")
        else:
            self.play_btn.setText("▶ Play")

    def _on_position_changed(self, position):
        self.seek_slider.setValue(position)
        self._update_time_label(position, self._duration)

    def _on_duration_changed(self, duration):
        self._duration = duration
        self.seek_slider.setRange(0, duration)
        self._update_time_label(self.player.position(), duration)

    def _on_seek_moved(self, position):
        self.player.setPosition(position)

    def _update_time_label(self, current, total):
        curr_time = QTime(0, 0).addMSecs(current).toString("mm:ss")
        total_time = QTime(0, 0).addMSecs(total).toString("mm:ss")
        self.time_label.setText(f"{curr_time} / {total_time}")

    def _on_error(self, error, error_string):
        logger.error(f"Video Player Error: {error_string}")

    def stop(self):
        self.player.stop()

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)
