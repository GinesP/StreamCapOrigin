from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt

class RecordingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_mock_data()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.title_label = QLabel("Recording List")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        # Table for recordings
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Streamer", "Platform", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        self.layout.addWidget(self.table)

    def load_mock_data(self):
        mock_data = [
            {"streamer": "Streamer A", "platform": "Twitch", "status": "Recording"},
            {"streamer": "Streamer B", "platform": "YouTube", "status": "Offline"},
            {"streamer": "Streamer C", "platform": "Twitch", "status": "Waiting"},
        ]

        self.table.setRowCount(len(mock_data))
        for i, item in enumerate(mock_data):
            self.table.setItem(i, 0, QTableWidgetItem(item["streamer"]))
            self.table.setItem(i, 1, QTableWidgetItem(item["platform"]))
            
            status_item = QTableWidgetItem(item["status"])
            if item["status"] == "Recording":
                status_item.setForeground(Qt.red)
            self.table.setItem(i, 2, status_item)

            # Actions buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            stop_btn = QPushButton("Stop")
            stop_btn.setStyleSheet("background-color: #f44336; color: white; border-radius: 3px;")
            actions_layout.addWidget(stop_btn)
            
            self.table.setCellWidget(i, 3, actions_widget)
