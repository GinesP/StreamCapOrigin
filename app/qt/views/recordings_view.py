"""
Qt Recordings View for StreamCap.

Migrates the Flet GridView of recording cards to a Qt layout.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QPushButton,
    QFrame
)

from app.qt.components.recording_card import QtRecordingCard
from app.utils.logger import logger


class QtRecordingsView(QWidget):
    """
    Shows the grid or list of recordings currently being monitored/recorded.
    """

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self._cards = {}
        self._view_mode = "grid" # grid or list
        
        self._setup_ui()
        self._load_data()
        self._subscribe_events()

    def resizeEvent(self, event):
        """Handle resize to adjust grid columns."""
        self._redraw_grid()
        super().resizeEvent(event)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header: Title + Actions
        header = QHBoxLayout()
        title = QLabel("Recordings")
        title.setProperty("class", "heading")
        header.addWidget(title)
        
        header.addStretch()

        # View Mode Toggle
        self.view_toggle_btn = QPushButton("≡ List View")
        self.view_toggle_btn.setProperty("class", "secondary")
        self.view_toggle_btn.setFixedWidth(100)
        self.view_toggle_btn.clicked.connect(self._toggle_view_mode)
        header.addWidget(self.view_toggle_btn)
        
        # Add button
        self.add_btn = QPushButton("Add Stream")
        self.add_btn.setProperty("class", "primary-btn")
        self.add_btn.clicked.connect(self._on_add_stream_clicked)
        header.addWidget(self.add_btn)
        
        main_layout.addLayout(header)

        # Scrollable Area for cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.card_container = QWidget()
        self.card_container.setObjectName("cardContainer")
        self.card_container.setStyleSheet("#cardContainer { background: transparent; }")
        
        self.grid_layout = QGridLayout(self.card_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        # Fix alignment to Top-Left
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll.setWidget(self.card_container)
        main_layout.addWidget(self.scroll)

    def _toggle_view_mode(self):
        self._view_mode = "list" if self._view_mode == "grid" else "grid"
        label = "田 Grid View" if self._view_mode == "list" else "≡ List View"
        self.view_toggle_btn.setText(label)
        
        # Update cards and redraw
        for card in self._cards.values():
            card.set_view_mode(self._view_mode)
        
        self._redraw_grid()

    def _load_data(self):
        """Initial load of recordings from the manager."""
        recordings = self.app.record_manager.recordings
        logger.info(f"QtRecordingsView: Loading {len(recordings)} recordings.")
        for i, rec in enumerate(recordings):
            self._add_card(rec, i)
            
        # Schedule a redraw to ensure correct columns after layout
        QTimer.singleShot(100, self._redraw_grid)

    def _add_card(self, recording, index):
        """Create and add a card for a recording."""
        card = QtRecordingCard(recording, self.app)
        card.set_view_mode(self._view_mode)
        self._cards[recording.rec_id] = card

    def _subscribe_events(self):
        """Subscribe to EventBus to react to data changes."""
        self.app.event_bus.subscribe("update", self._on_recording_updated)
        self.app.event_bus.subscribe("add", self._on_recording_added)
        self.app.event_bus.subscribe("delete", self._on_recording_deleted)

    def _on_recording_updated(self, topic, recording):
        """Handle 'update' event from EventBus."""
        if recording.rec_id in self._cards:
            card = self._cards[recording.rec_id]
            card.update_content()

    def _on_recording_added(self, topic, recording):
        """Handle 'add' event from EventBus."""
        self._add_card(recording, len(self._cards))
        self._redraw_grid()

    def _on_recording_deleted(self, topic, recordings):
        """Handle 'delete' event from EventBus."""
        # Remove deleted cards
        if not isinstance(recordings, list):
            recordings = [recordings]
            
        for rec in recordings:
            rec_id = getattr(rec, "rec_id", rec)
            if rec_id in self._cards:
                card = self._cards.pop(rec_id)
                self.grid_layout.removeWidget(card)
                card.deleteLater()
        
        # Redraw grid to fill gaps
        self._redraw_grid()

    def _on_add_stream_clicked(self):
        """Open the Add Stream dialog."""
        from app.qt.components.add_stream_dialog import QtAddStreamDialog
        dialog = QtAddStreamDialog(self.app, self)
        if dialog.exec():
            # Data should be added via the dialog and published to EventBus
            pass

    def _redraw_grid(self):
        """Rearrange cards based on available width and mode."""
        width = self.scroll.viewport().width()
        if width < 100:
            width = self.width() or 1000
            
        if self._view_mode == "list":
            cols = 1
            card_width = width - 40 # Padding
        else:
            cols = max(1, (width - 10) // 335)
            card_width = 320

        # Clear and re-add to layout
        for i, (rec_id, card) in enumerate(self._cards.items()):
            # Update card size for list mode
            if self._view_mode == "list":
                card.setFixedWidth(card_width)
            else:
                card.setFixedSize(320, 160)
                
            self.grid_layout.removeWidget(card)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)
