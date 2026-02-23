from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # Welcome Header
        self.title_label = QLabel("Welcome to StreamCap")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        self.tagline_label = QLabel("Record every exciting moment of the live broadcast")
        self.tagline_label.setStyleSheet("color: #666;")
        self.layout.addWidget(self.tagline_label)

        # Stats Cards (using Grid)
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(15)

        self.total_rooms_card = self.create_card("Total Rooms", "0")
        self.active_recordings_card = self.create_card("Active Recordings", "0")
        
        self.stats_layout.addWidget(self.total_rooms_card, 0, 0)
        self.stats_layout.addWidget(self.active_recordings_card, 0, 1)
        
        self.layout.addLayout(self.stats_layout)

        # Action Button
        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setFixedHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.layout.addWidget(self.start_btn)

        self.layout.addStretch()

    def create_card(self, title, value):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px; border: 1px solid #ddd;")
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 14px;")
        card_layout.addWidget(title_label)
        
        val_label = QLabel(value)
        val_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        card_layout.addWidget(val_label)
        
        return card

    def on_start_clicked(self):
        print("Start Recording clicked (Dummy Action)")
