"""
Qt Log View for StreamCap.

Displays real-time application logs and FFmpeg output.
"""

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QCheckBox
)
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont

from app.utils.logger import logger

class LogSignalEmitter(QObject):
    log_received = Signal(str, str) # level, message

class QtLogView(QWidget):
    """
    A view that shows application logs in real-time.
    """

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.emitter = LogSignalEmitter()
        self.emitter.log_received.connect(self._append_log)
        
        self._auto_scroll = True
        self._setup_ui()
        self._setup_logging_sink()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Log Display (Create early because clear_btn needs it)
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setUndoRedoEnabled(False)
        self.log_display.setMaximumBlockCount(1000) # Keep memory low
        
        # Dark theme for logs
        self.log_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                color: #dcdcdc;
                border: 1px solid #333;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)

        # Header
        header = QHBoxLayout()
        title = QLabel("Application Logs")
        title.setProperty("class", "heading")
        header.addWidget(title)
        header.addStretch()
        
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.stateChanged.connect(self._on_autoscroll_changed)
        header.addWidget(self.auto_scroll_check)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.log_display.clear)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        layout.addWidget(self.log_display)

    def _on_autoscroll_changed(self, state):
        self._auto_scroll = state == Qt.CheckState.Checked.value

    def _setup_logging_sink(self):
        """Add a loguru sink that forwards to our Qt signal."""
        def qt_sink(message):
            record = message.record
            level = record["level"].name
            msg_text = record["message"]
            self.emitter.log_received.emit(level, msg_text)

        logger.add(qt_sink, level="INFO", enqueue=True)

    def _append_log(self, level, message):
        """Format and append a log message to the display."""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Format based on level
        fmt = QTextCharFormat()
        if level == "ERROR":
            fmt.setForeground(QColor("#ff5555")) # Red
        elif level == "WARNING":
            fmt.setForeground(QColor("#ffb86c")) # Orange
        elif level == "DEBUG":
            fmt.setForeground(QColor("#6272a4")) # Muted blue
        elif level == "SUCCESS":
            fmt.setForeground(QColor("#50fa7b")) # Green
        else:
            fmt.setForeground(QColor("#dcdcdc")) # Default
            
        cursor.setCharFormat(fmt)
        cursor.insertText(f"[{level: <7}] {message}\n")
        
        if self._auto_scroll:
            self.log_display.setTextCursor(cursor)
            self.log_display.ensureCursorVisible()
