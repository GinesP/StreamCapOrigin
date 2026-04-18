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
from PySide6.QtGui import QFont

from app.qt.components.recording_card import QtRecordingCard
from app.qt.utils.filters import RecordingFilters
from app.qt.themes.theme import theme_manager
from app.qt.utils.elevation import apply_elevation
from app.utils.logger import logger
from app.utils.i18n import tr


class QtRecordingsView(QWidget):
    """
    Shows the grid or list of recordings currently being monitored/recorded.
    """

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.language = self.app.language_manager.language
        self._l = self.language.get("recordings_page", {})
        self._cards: dict = {}
        self._view_mode = "list"   # list is default; user can switch to grid
        self._current_status_filter = "all"
        self._current_platform_filter = "all"
        self._search_query = ""
        
        self._setup_ui()
        self._load_data()
        self._update_platform_list()
        self._subscribe_events()
        
        # 1-second timer for real-time card updates (timer/status)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_refresh_tick)
        self._refresh_timer.start(1000)

        theme_manager.themeChanged.connect(self._on_theme_changed)

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
        title = QLabel(self._l.get("recording_list", "Recordings"))
        title.setProperty("class", "heading")
        header.addWidget(title)
        
        header.addStretch()

        # View Mode Toggle
        self.view_toggle_btn = QPushButton("⊞")  # Show grid icon while in list mode
        self.view_toggle_btn.setStyleSheet("font-size: 20px;")
        self.view_toggle_btn.setToolTip(self._l.get("toggle_view", "Toggle Grid/List View"))
        self.view_toggle_btn.setProperty("class", "icon")
        self.view_toggle_btn.setFixedSize(36, 36)
        self.view_toggle_btn.clicked.connect(self._toggle_view_mode)
        header.addWidget(self.view_toggle_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setToolTip(self._l.get("refresh", "Refresh List"))
        self.refresh_btn.setProperty("class", "icon")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)

        # Add button
        self.add_btn = QPushButton("+")
        self.add_btn.setToolTip(self._l.get("add_record", "Add New Stream"))
        self.add_btn.setProperty("class", "primary-btn") # Keep it prominent but smaller
        self.add_btn.setFixedSize(36, 36)
        self.add_btn.setStyleSheet("font-size: 20px; font-weight: bold; padding: 0;")
        self.add_btn.clicked.connect(self._on_add_stream_clicked)
        header.addWidget(self.add_btn)

        # Batch Start Button
        self.batch_start_btn = QPushButton("▶")
        self.batch_start_btn.setToolTip(self._l.get("batch_start", "Start Monitor (Visible Streams)"))
        self.batch_start_btn.setProperty("class", "icon")
        self.batch_start_btn.setFixedSize(36, 36)
        self.batch_start_btn.clicked.connect(self._on_batch_start_clicked)
        header.addWidget(self.batch_start_btn)

        # Batch Stop Button
        self.batch_stop_btn = QPushButton("■")
        self.batch_stop_btn.setToolTip(self._l.get("batch_stop", "Stop Monitor (Visible Streams)"))
        self.batch_stop_btn.setProperty("class", "icon")
        self.batch_stop_btn.setFixedSize(36, 36)
        self.batch_stop_btn.clicked.connect(self._on_batch_stop_clicked)
        header.addWidget(self.batch_stop_btn)
        
        main_layout.addLayout(header)

        # ── Filter Bar ────────────────────────────────────────────────
        # Use two rows to handle long translated strings gracefully
        filter_bar_frame = QFrame()
        filter_bar_frame.setProperty("class", "card")
        filter_bar_layout = QVBoxLayout(filter_bar_frame)
        filter_bar_layout.setContentsMargins(14, 12, 14, 12)
        filter_bar_layout.setSpacing(12)
        
        top_filter_row = QHBoxLayout()
        top_filter_row.setSpacing(10)
        
        # 1. Search Box
        self.search_box = QLineEdit()
        # Use simple "Search..." instead of long "Enter search keyword"
        placeholder = self._l.get("search", "Search")
        self.search_box.setPlaceholderText(f"{placeholder}...")
        self.search_box.setMinimumWidth(250)
        self.search_box.textChanged.connect(self._on_search_changed)
        top_filter_row.addWidget(self.search_box)
        top_filter_row.addStretch()
        
        bottom_filter_row = QHBoxLayout()
        bottom_filter_row.setSpacing(10)

        # Status Filter Label
        status_label = QLabel(self._l.get("status_filter", "Status:").split(':')[0] + ":")
        status_label.setProperty("class", "secondary")
        bottom_filter_row.addWidget(status_label)
        
        # 2. Status Filters
        self.status_grp = QButtonGroup(self)
        self.status_grp.setExclusive(True)
        
        status_filters = [
            (self._l.get("filter_all", "Todos"), "all", theme_manager.get_color("accent")),
            (self._l.get("filter_recording", "Grabando"), "recording", "#F44336"),
            (self._l.get("filter_living", "En Vivo"), "living", "#4CAF50"),
            (self._l.get("filter_offline", "Offline"), "offline", "#9E9E9E"),
            (self._l.get("filter_error", "Error"), "error", "#FF9800"),
            (self._l.get("filter_stopped", "Detenido"), "stopped", "#607D8B"),
        ]
        
        self.filter_btns = []
        for i, (label, key, color) in enumerate(status_filters):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "filter-btn")
            if key == "all": 
                btn.setChecked(True)
            
            # Elite Premium Styling: Active state uses the specific status color
            btn.setStyleSheet(f"""
                QPushButton[class="filter-btn"]:checked {{
                    background-color: {color};
                    border-color: {color};
                    color: white;
                }}
            """)
            
            btn.setProperty("filter_key", key)
            btn.setProperty("base_color", color)
            btn.clicked.connect(self._on_filter_clicked)
            self.status_grp.addButton(btn, i)
            bottom_filter_row.addWidget(btn)
            self.filter_btns.append(btn)
            
        bottom_filter_row.addStretch()
        filter_bar_layout.addLayout(bottom_filter_row)
        
        # 3. Platform Dropdown
        self.platform_combo = QComboBox()
        self.platform_combo.setMinimumWidth(140)
        self.platform_combo.addItem(self.language.get("recording_card", {}).get("all", "Todas"), "all")
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        
        platform_label = QLabel(self._l.get("platform_filter", "Plataforma:").split(':')[0] + ":")
        platform_label.setProperty("class", "secondary")
        top_filter_row.addWidget(platform_label)
        top_filter_row.addWidget(self.platform_combo)
        
        filter_bar_layout.insertLayout(0, top_filter_row)
        main_layout.addWidget(filter_bar_frame)
        apply_elevation(filter_bar_frame, level=1)
        self._filter_bar_frame = filter_bar_frame

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
        
        # Update icon and tooltip only (no text to avoid clipping in 36x36 btn)
        icon = "⊞" if self._view_mode == "list" else "≣"
        tip = self._l.get("toggle_view", "Switch View")
        
        self.view_toggle_btn.setText(icon)
        self.view_toggle_btn.setToolTip(tip)
        
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
            
        # Optional sorting dynamically if needed, though grid redraw iterates.
        self._redraw_grid()

    def _on_theme_changed(self):
        for btn in self.filter_btns:
            if btn.property("filter_key") == "all":
                color = theme_manager.get_color("accent")
                btn.setStyleSheet(f"""
                    QPushButton[class="filter-btn"]:checked {{
                        background-color: {color};
                        border-color: {color};
                        color: white;
                    }}
                """)
        if hasattr(self, "_filter_bar_frame"):
            apply_elevation(self._filter_bar_frame, level=1)

    def _update_platform_list(self):
        """Populate platform combo with existing platforms."""
        prev_data = self.platform_combo.currentData()
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem(self.language.get("recording_card", {}).get("all", "All Platforms"), "all")
        
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

    def refresh(self):
        """Force reload data from disk and rebuild cards."""
        # Stop any ongoing incremental loading
        if hasattr(self, "_load_timer") and self._load_timer.isActive():
            self._load_timer.stop()
            
        # Cleanup existing
        for card in list(self._cards.values()):
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        
        # Load again (manager reload)
        self.app.record_manager.load_recordings()
        
        # Re-build UI
        self._load_data()
        self._update_platform_list()
        self._apply_filters()

    def _load_data(self):
        """Initial load of recordings from the manager using incremental loading."""
        recordings = self.app.record_manager.recordings
        # Sort recordings: Live first, then by priority score (descending)
        self._pending_recordings = sorted(
            recordings,
            key=lambda r: (r.is_live, getattr(r, 'priority_score', 0.0), r.streamer_name),
            reverse=True
        )
        
        logger.info(f"QtRecordingsView: Starting incremental load of {len(self._pending_recordings)} recordings.")
        
        # Process first batch immediately (e.g., first 12 cards)
        self._process_load_batch(batch_size=12)
        
        # Schedule the rest in batches
        if self._pending_recordings:
            if not hasattr(self, "_load_timer"):
                self._load_timer = QTimer(self)
                self._load_timer.timeout.connect(lambda: self._process_load_batch(batch_size=8))
            
            self._load_timer.start(50) # Small delay between batches

    def _process_load_batch(self, batch_size=10):
        """Create and add a batch of cards to the view."""
        if not hasattr(self, "_pending_recordings") or not self._pending_recordings:
            if hasattr(self, "_load_timer"):
                self._load_timer.stop()
            return

        batch = self._pending_recordings[:batch_size]
        self._pending_recordings = self._pending_recordings[batch_size:]
        
        start_index = len(self._cards)
        for i, rec in enumerate(batch):
            self._add_card(rec, start_index + i)
            
        # Update layout and filters for the new cards
        self._apply_filters()
        
        if not self._pending_recordings and hasattr(self, "_load_timer"):
            self._load_timer.stop()
            logger.debug("QtRecordingsView: Incremental loading finished.")

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
            # Automatically re-apply filters so if a card no longer matches, it hides
            self._apply_filters()

    def _on_refresh_tick(self):
        """Called every second to update durations/status of visible cards."""
        # Only update visible cards to save CPU
        for card in self._cards.values():
            if card.isVisible():
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

        # Sort the visible cards to guarantee the desired order
        visible.sort(
            key=lambda c: (c.recording.is_live, getattr(c.recording, 'priority_score', 0.0), c.recording.streamer_name),
            reverse=True
        )

        # Check if we need to redraw by comparing state
        current_state = (cols, card_w, self._view_mode, [id(c) for c in visible])
        if getattr(self, "_last_grid_state", None) == current_state:
            return
        self._last_grid_state = current_state

        self.card_container.setUpdatesEnabled(False)
        try:
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
        finally:
            self.card_container.setUpdatesEnabled(True)

    def _on_batch_start_clicked(self):
        """Start monitoring for all currently visible recordings."""
        visible_recordings = [card.recording for card in self._cards.values() if card.isVisible()]
        if not visible_recordings:
            return
            
        import asyncio
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtCore import QTimer
        
        # Disable buttons temporarily
        self.batch_start_btn.setEnabled(False)
        self.batch_stop_btn.setEnabled(False)
        QTimer.singleShot(1500, lambda: self.batch_start_btn.setEnabled(True))
        QTimer.singleShot(1500, lambda: self.batch_stop_btn.setEnabled(True))
        
        # Show toast
        from app.qt.main_window import MainWindow
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.show_toast(tr("toast.starting_monitor", default="Starting monitor for {count} visible stream(s)...").format(count=len(visible_recordings)), duration=3000)
            
        asyncio.ensure_future(self.app.record_manager.start_monitor_recordings(visible_recordings))

    def _on_batch_stop_clicked(self):
        """Stop monitoring for all currently visible recordings."""
        visible_recordings = [card.recording for card in self._cards.values() if card.isVisible()]
        if not visible_recordings:
            return
            
        import asyncio
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtCore import QTimer
        
        # Disable buttons temporarily
        self.batch_start_btn.setEnabled(False)
        self.batch_stop_btn.setEnabled(False)
        QTimer.singleShot(1500, lambda: self.batch_start_btn.setEnabled(True))
        QTimer.singleShot(1500, lambda: self.batch_stop_btn.setEnabled(True))
        
        # Show toast
        from app.qt.main_window import MainWindow
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.show_toast(tr("toast.stopping_monitor", default="Stopping monitor for {count} visible stream(s)...").format(count=len(visible_recordings)), duration=3000)
            
        asyncio.ensure_future(self.app.record_manager.stop_monitor_recordings(visible_recordings))
