import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from qasync import asyncSlot

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.setup_ui()
        # Start a background task
        asyncio.create_task(self.update_counter())

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

        # Stats Cards
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(15)

        self.total_rooms_card, self.total_rooms_val = self.create_card("Total Rooms", "0")
        self.active_recordings_card, self.active_recordings_val = self.create_card("Active Recordings", "0")
        
        self.stats_layout.addWidget(self.total_rooms_card, 0, 0)
        self.stats_layout.addWidget(self.active_recordings_card, 0, 1)
        
        self.layout.addLayout(self.stats_layout)

        # Async Counter Display
        self.counter_label = QLabel("Background Task Counter: 0")
        self.counter_label.setStyleSheet("font-style: italic; color: blue;")
        self.layout.addWidget(self.counter_label)

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
        
        return card, val_label

    @asyncSlot()
    async def on_start_clicked(self):
        print("Start Recording clicked (Simulating Async Call)")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("Starting...")
        await asyncio.sleep(2) # Simulate async work
        self.start_btn.setText("Start Recording")
        self.start_btn.setEnabled(True)
        print("Recording Started (Simulated)")

    async def update_counter(self):
        while True:
            self.counter += 1
            self.counter_label.setText(f"Background Task Counter: {self.counter}")
            await asyncio.sleep(1)
