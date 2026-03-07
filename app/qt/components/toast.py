"""
Qt Toast Notification System for StreamCap.
Provides floating, auto-dismissing alerts in the corner of the window.
"""

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QFrame,
    QVBoxLayout,
    QGraphicsOpacityEffect
)
from PySide6.QtGui import QColor, QFont


class ToastWidget(QFrame):
    """
    A single toast notification widget.
    """
    def __init__(self, message, toast_type="info", parent=None):
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self._setup_ui()
        
    def _setup_ui(self):
        self.setObjectName("toastWidget")
        
        # Style based on type
        colors = {
            "info": "#2D2D2D",
            "success": "#2E7D32",
            "error": "#C62828",
            "warning": "#F9A825"
        }
        accent = colors.get(self.toast_type, colors["info"])
        
        self.setStyleSheet(f"""
            QFrame#toastWidget {{
                background-color: {accent};
                border: 1px solid #444;
                border-radius: 8px;
            }}
            QLabel {{
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.label = QLabel(self.message)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        # Opacity effect for fading
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
    def fade_in(self, duration=300):
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
    def fade_out(self, duration=500, callback=None):
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        if callback:
            self.animation.finished.connect(callback)
        self.animation.start()


class QtToastManager:
    """
    Manages a queue of toasts and displays them stacked in the corner.
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.active_toasts = []
        self.spacing = 10
        self.margin = 20
        
    def show_toast(self, message, toast_type="info", duration=4000):
        toast = ToastWidget(message, toast_type, self.main_window)
        toast.show()
        toast.fade_in()
        
        self.active_toasts.append(toast)
        self._reposition_toasts()
        
        # Auto-dismiss
        timer = QTimer(toast)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._remove_toast(toast))
        timer.start(duration)
        
    def _remove_toast(self, toast):
        if toast in self.active_toasts:
            toast.fade_out(callback=lambda: self._on_fade_out_finished(toast))
            
    def _on_fade_out_finished(self, toast):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
        toast.close()
        toast.deleteLater()
        self._reposition_toasts()
        
    def _reposition_toasts(self):
        """Stacks toasts from bottom-right."""
        if not self.main_window:
            return
            
        window_rect = self.main_window.geometry()
        x = window_rect.right() - self.margin
        current_y = window_rect.bottom() - self.margin
        
        for toast in reversed(self.active_toasts):
            toast_size = toast.sizeHint()
            # If sizeHint is wrong (widget not shown yet properly), we might need a default
            w = max(200, toast_size.width())
            h = toast_size.height()
            
            toast.setFixedSize(w, h)
            toast.move(x - w, current_y - h)
            current_y -= (h + self.spacing)
