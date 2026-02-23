import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt

try:
    from .home_view import HomeView
except ImportError:
    from home_view import HomeView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamCap Origin - Native Prototype")
        self.resize(1000, 700)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Sidebar
        self.sidebar_container = QFrame()
        self.sidebar_container.setFixedWidth(200)
        self.sidebar_container.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ccc;")
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        
        self.sidebar_title = QLabel("StreamCap")
        self.sidebar_title.setAlignment(Qt.AlignCenter)
        self.sidebar_title.setStyleSheet("font-weight: bold; font-size: 18px; margin: 10px;")
        self.sidebar_layout.addWidget(self.sidebar_title)

        self.nav_list = QListWidget()
        self.nav_list.addItem("Home")
        self.nav_list.addItem("Recordings")
        self.nav_list.addItem("Settings")
        self.nav_list.addItem("About")
        self.sidebar_layout.addWidget(self.nav_list)
        
        self.sidebar_layout.addStretch()
        
        self.main_layout.addWidget(self.sidebar_container)

        # Content Area (Stacked Widget)
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # Connect sidebar selection to stack
        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)

        # Initial pages
        self.add_pages()

    def add_pages(self):
        # Home
        self.home_view = HomeView()
        self.content_stack.addWidget(self.home_view)

        # Recordings
        self.recordings_page = QWidget()
        recordings_layout = QVBoxLayout(self.recordings_page)
        recordings_layout.addWidget(QLabel("Recordings View Placeholder"))
        self.content_stack.addWidget(self.recordings_page)

        # Settings
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.addWidget(QLabel("Settings View Placeholder"))
        self.content_stack.addWidget(settings_page)

        # About
        about_page = QWidget()
        about_layout = QVBoxLayout(about_page)
        about_layout.addWidget(QLabel("About View Placeholder"))
        self.content_stack.addWidget(about_page)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
