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
    QFrame,
    QLineEdit,
    QComboBox,
    QButtonGroup
)

from app.qt.components.recording_card import QtRecordingCard
from app.qt.utils.filters import RecordingFilters
from app.utils.logger import logger


class QtRecordingsView(QWidget):
    """
    Shows the grid or list of recordings currently being monitored/recorded.
    """

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self._cards: dict = {}
        self._view_mode = "list"   # list is default; user can switch to grid
        self._current_status_filter = "all"
        self._current_platform_filter = "all"
        self._search_query = ""
        
        self._setup_ui()
        self._load_data()
        self._update_platform_list()
        self._subscribe_events()
        
        # Apply filters initially to make cards visible and redraw the grid
        self._apply_filters()

    def resizeEvent(self, event):
        """Handle resize to adjust grid columns."""
        self._redraw_grid()
        super().resizeEvent(event)

    def showEvent(self, event):
        """Triggered when the view becomes visible (e.g. first show or tab switch).
        
        We defer _redraw_grid() with QTimer.singleShot(0) so it runs AFTER Qt
        has finished laying out the window and scroll.viewport().width() returns
        the real width. Without this, the initial grid layout computed during
        __init__ uses width=0 (viewport not yet sized) and all cards stack at
        the top-left corner.
        """
        super().showEvent(event)
        QTimer.singleShot(0, self._redraw_grid)

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

        # View Mode Toggle — label reflects CURRENT mode, click switches
        self.view_toggle_btn = QPushButton("田 Grid View")
        self.view_toggle_btn.setProperty("class", "secondary")
        self.view_toggle_btn.setFixedWidth(110)
        self.view_toggle_btn.clicked.connect(self._toggle_view_mode)
        header.addWidget(self.view_toggle_btn)
        
        # Add button
        self.add_btn = QPushButton("Add Stream")
        self.add_btn.setProperty("class", "primary-btn")
        self.add_btn.clicked.connect(self._on_add_stream_clicked)
        header.addWidget(self.add_btn)
        
        main_layout.addLayout(header)

        # ── Filter Bar ────────────────────────────────────────────────
        filter_bar_layout = QHBoxLayout()
        filter_bar_layout.setSpacing(10)
        
        # 1. Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search streamers...")
        self.search_box.setFixedWidth(200)
        self.search_box.textChanged.connect(self._on_search_changed)
        filter_bar_layout.addWidget(self.search_box)
        
        # 2. Status Filters
        self.status_grp = QButtonGroup(self)
        self.status_grp.setExclusive(True)
        
        status_filters = [
            ("All", "all"),
            ("Recording", "recording"),
            ("Live", "living"),
            ("Offline", "offline"),
            ("Error", "error"),
            ("Stopped", "stopped"),
        ]
        
        for i, (label, key) in enumerate(status_filters):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "filter-btn")
            if key == "all": btn.setChecked(True)
            btn.setProperty("filter_key", key)
            btn.clicked.connect(self._on_filter_clicked)
            self.status_grp.addButton(btn, i)
            filter_bar_layout.addWidget(btn)
            
        filter_bar_layout.addStretch()
        
        # 3. Platform Dropdown
        self.platform_combo = QComboBox()
        self.platform_combo.setFixedWidth(120)
        self.platform_combo.addItem("All Platforms", "all")
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        filter_bar_layout.addWidget(QLabel("Platform:"))
        filter_bar_layout.addWidget(self.platform_combo)
        
        main_layout.addLayout(filter_bar_layout)

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

    def _toggle_view_mode(self) -> None:
        self._view_mode = "grid" if self._view_mode == "list" else "list"
        # Button label shows the OPPOSITE mode (what you'll switch TO)
        self.view_toggle_btn.setText(
            "≡ List View" if self._view_mode == "grid" else "田 Grid View"
        )
        for card in self._cards.values():
            card.set_view_mode(self._view_mode)
        self._redraw_grid()

    def _on_search_changed(self, text):
        self._search_query = text
        self._apply_filters()

    def _on_filter_clicked(self):
        btn = self.sender()
        self._current_status_filter = btn.property("filter_key")
        self._apply_filters()

    def _on_platform_changed(self, index):
        self._current_platform_filter = self.platform_combo.itemData(index)
        self._apply_filters()

    def _apply_filters(self):
        """Apply search, status and platform filters to cards."""
        for rec_id, card in self._cards.items():
            rec = card.recording
            
            match_status = RecordingFilters.matches_status(rec, self._current_status_filter)
            match_platform = RecordingFilters.matches_platform(rec, self._current_platform_filter)
            match_search = RecordingFilters.matches_search(rec, self._search_query)
            
            card.setVisible(match_status and match_platform and match_search)
            
        self._redraw_grid()

    def _update_platform_list(self):
        """Populate platform combo with existing platforms."""
        prev_data = self.platform_combo.currentData()
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem("All Platforms", "all")
        
        platforms = {}
        for rec in self.app.record_manager.recordings:
            if rec.platform and rec.platform_key:
                platforms[rec.platform_key] = rec.platform
        
        for key, name in platforms.items():
            self.platform_combo.addItem(name, key)
            
        # Try to restore selection
        idx = self.platform_combo.findData(prev_data)
        if idx != -1:
            self.platform_combo.setCurrentIndex(idx)
            
        self.platform_combo.blockSignals(False)

    def _load_data(self):
        """Initial load of recordings from the manager."""
        recordings = self.app.record_manager.recordings
        logger.info(f"QtRecordingsView: Loading {len(recordings)} recordings.")
        for i, rec in enumerate(recordings):
            self._add_card(rec, i)

    def _add_card(self, recording, index):
        """Create and add a card for a recording."""
        # IMPORTANT: pass self.card_container as the parent.
        # Without a parent, Qt treats the card as a top-level window.
        # Calling setVisible(True) on a parentless widget SHOWS it as a
        # floating window -- causing the 'popup storm' on startup.
        card = QtRecordingCard(recording, self.app, parent=self.card_container)
        card.set_view_mode(self._view_mode)
        card.hide()  # Start hidden; _apply_filters will show as needed
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
        self._update_platform_list()
        self._apply_filters()
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
        self._update_platform_list()
        self._redraw_grid()

    def _on_add_stream_clicked(self):
        """Open the Add Stream dialog."""
        from app.qt.components.add_stream_dialog import QtAddStreamDialog
        dialog = QtAddStreamDialog(self.app, self)
        if dialog.exec():
            # Data should be added via the dialog and published to EventBus
            pass

    def _redraw_grid(self) -> None:
        """Rearrange visible cards in the grid layout."""
        width = self.scroll.viewport().width()
        if width < 100:
            width = self.width() or 1000

        if self._view_mode == "list":
            cols      = 1
            card_w    = width - 40   # full width minus scroll padding
            card_h    = 72
        else:
            cols   = max(1, (width - 10) // 335)
            card_w = 320
            card_h = 165

        visible = [c for c in self._cards.values() if c.isVisible()]

        for i, card in enumerate(visible):
            self.grid_layout.removeWidget(card)
            if self._view_mode == "list":
                card.setFixedWidth(card_w)
                card.setFixedHeight(card_h)
            else:
                card.setFixedSize(card_w, card_h)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

