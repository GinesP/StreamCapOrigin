from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QHeaderView,
    QSizePolicy,
    QFrame,
    QGridLayout,
    QScrollArea,
)

from app.qt.components.heatmap_chart import HeatmapChart
from app.qt.themes.theme import theme_manager
from app.qt.utils.formatters import fmt_duration
from app.qt.views.home_view import StatCard, SparklineChart, QueueBarChart
from app.utils.i18n import tr


class QtStatsView(QWidget):
    CACHE_TTL = 60.0

    def __init__(self, app_context) -> None:
        super().__init__()
        self.app = app_context
        self._cache: dict[str, tuple[Any, float]] = {}
        self._current_tab = 0

        self._setup_ui()
        self._retranslate_ui()
        self._refresh_current_tab()

        self.app.event_bus.subscribe("language_changed", self._on_language_changed)
        theme_manager.themeChanged.connect(self._on_theme_changed)

    # ── Cache ────────────────────────────────────────────────────────

    def _get_cached_or_compute(self, key: str, compute: Callable[[], Any]) -> Any:
        now = time.time()
        if key in self._cache:
            data, expire = self._cache[key]
            if now < expire:
                return data
        data = compute()
        self._cache[key] = (data, now + self.CACHE_TTL)
        return data

    def _invalidate_cache(self, key: str | None = None) -> None:
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    # ── UI Setup ─────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        scroll.setWidget(content)

        # Header
        header = QHBoxLayout()
        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {theme_manager.get_color('text')}; background: transparent;"
        )
        header.addWidget(self._title_lbl)
        header.addStretch()

        self._refresh_btn = QPushButton()
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header.addWidget(self._refresh_btn)
        layout.addLayout(header)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

        self._setup_general_tab()
        self._setup_predictor_tab()
        self._setup_heatmap_tab()

    def _setup_general_tab(self) -> None:
        self._general_tab = QWidget()
        layout = QVBoxLayout(self._general_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        # Stat cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._gen_cards: dict[str, StatCard] = {}
        for key in ("total_streamers", "total_sessions", "avg_priority", "avg_consistency"):
            card = StatCard("▣", key, "0", accent="use_theme_accent")
            cards_row.addWidget(card)
            self._gen_cards[key] = card
        layout.addLayout(cards_row)

        # Table
        self._gen_table = QTableWidget()
        self._gen_table.setColumnCount(7)
        self._gen_table.setSortingEnabled(True)
        header = self._gen_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # streamer name
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)    # fav
        header.resizeSection(6, 30)
        self._gen_table.verticalHeader().setVisible(False)
        self._gen_table.setAlternatingRowColors(True)
        self._gen_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._gen_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._gen_table.cellDoubleClicked.connect(self._on_general_table_dblclick)
        self._gen_table.setStyleSheet(
            f"QTableWidget {{ background: {theme_manager.get_color('surface')}; alternate-background-color: {theme_manager.get_color('surface2')}; border: 1px solid {theme_manager.get_color('border')}; border-radius: 8px; }}"
            f"QHeaderView::section {{ background: {theme_manager.get_color('card')}; color: {theme_manager.get_color('text')}; padding: 6px; border: none; }}"
        )
        layout.addWidget(self._gen_table)
        self._tabs.addTab(self._general_tab, "General")

    def _setup_heatmap_tab(self) -> None:
        self._heatmap_tab = QWidget()
        layout = QVBoxLayout(self._heatmap_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        selector_row = QHBoxLayout()
        self._hm_selector = QComboBox()
        self._hm_selector.setMinimumWidth(200)
        self._hm_selector.currentIndexChanged.connect(self._on_heatmap_streamer_changed)
        selector_row.addWidget(self._hm_selector)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        self._hm_chart = HeatmapChart()
        layout.addWidget(self._hm_chart)

        # Legend
        legend_row = QHBoxLayout()
        legend_row.addStretch()
        self._hm_legend_lbl = QLabel()
        self._hm_legend_lbl.setStyleSheet(
            f"color: {theme_manager.get_color('text_muted')}; font-size: 11px; background: transparent;"
        )
        legend_row.addWidget(self._hm_legend_lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        self._tabs.addTab(self._heatmap_tab, "Heatmap")

    def _setup_predictor_tab(self) -> None:
        self._predictor_tab = QWidget()
        layout = QVBoxLayout(self._predictor_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._pred_cards: dict[str, StatCard] = {}
        for key in ("total_checks", "live_detections", "avg_latency", "avg_likelihood"):
            card = StatCard("▣", key, "0", accent="use_theme_accent")
            cards_row.addWidget(card)
            self._pred_cards[key] = card
        layout.addLayout(cards_row)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        spark_col = QVBoxLayout()
        self._pred_spark_label = QLabel()
        self._pred_spark_label.setStyleSheet(
            f"font-size: 10px; color: {theme_manager.get_color('text_muted')}; background: transparent;"
        )
        spark_col.addWidget(self._pred_spark_label)
        self._pred_sparkline = SparklineChart()
        spark_col.addWidget(self._pred_sparkline)
        charts_row.addLayout(spark_col, 2)

        bar_col = QVBoxLayout()
        self._pred_bar_label = QLabel()
        self._pred_bar_label.setStyleSheet(
            f"font-size: 10px; color: {theme_manager.get_color('text_muted')}; background: transparent;"
        )
        bar_col.addWidget(self._pred_bar_label)
        self._pred_barchart = QueueBarChart(self)
        bar_col.addWidget(self._pred_barchart)
        charts_row.addLayout(bar_col, 1)

        layout.addLayout(charts_row)

        # Detail section
        detail_grid = QGridLayout()
        detail_grid.setSpacing(8)
        self._pred_detail_labels: dict[str, QLabel] = {}
        detail_items = [
            "latency_p50", "latency_p95", "latency_p99",
            "dispatch_p50", "dispatch_p95", "dispatch_breakdown",
        ]
        for i, key in enumerate(detail_items):
            lbl = QLabel()
            lbl.setStyleSheet(
                f"color: {theme_manager.get_color('text_sec')}; font-size: 12px; background: transparent;"
            )
            detail_grid.addWidget(lbl, i // 3, i % 3)
            self._pred_detail_labels[key] = lbl
        layout.addLayout(detail_grid)

        self._pred_empty = QLabel()
        self._pred_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pred_empty.setStyleSheet(
            f"color: {theme_manager.get_color('text_muted')}; font-size: 13px; background: transparent;"
        )
        self._pred_empty.setVisible(False)
        layout.addWidget(self._pred_empty)

        self._tabs.addTab(self._predictor_tab, "Predictor")

    # ── Data Aggregation ─────────────────────────────────────────────

    def _aggregate_general_data(self) -> dict:
        recordings = self.app.record_manager.recordings
        cutoff = datetime.now() - timedelta(hours=72)
        total_sessions = 0
        priorities = []
        consistencies = []
        seen_urls: set[str] = set()
        streamers: list[dict] = []

        for rec in recordings:
            # Deduplicate by URL — skip if we already saw this URL
            url = (rec.url or "").strip()
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            sessions = [
                s for s in rec.live_sessions
                if s.get("start_time") and datetime.fromisoformat(s["start_time"]) >= cutoff
            ]
            total_sessions += len(sessions)
            priorities.append(rec.priority_score or 0.0)
            consistencies.append(rec.consistency_score or 0.0)
            streamers.append({
                "name": rec.streamer_name,
                "platform": rec.platform_key or rec.platform or "—",
                "sessions": len(sessions),
                "avg_duration": rec.avg_session_duration_minutes,
                "priority": rec.priority_score or 0.0,
                "consistency": rec.consistency_score or 0.0,
                "favorite": bool(rec.is_favorite),
            })

        streamers.sort(key=lambda x: x["sessions"], reverse=True)

        return {
            "total_streamers": len(streamers),
            "total_sessions": total_sessions,
            "avg_priority": round(sum(priorities) / len(priorities), 2) if priorities else 0.0,
            "avg_consistency": round(sum(consistencies) / len(consistencies), 2) if consistencies else 0.0,
            "streamers": streamers,
        }

    def _build_heatmap_data(self, rec_id: str | None) -> list[tuple[int, int, int]]:
        recordings = self.app.record_manager.recordings
        if rec_id:
            recordings = [r for r in recordings if r.rec_id == rec_id]
        counts: dict[tuple[int, int], int] = {}
        for rec in recordings:
            for s in rec.live_sessions:
                wd = s.get("weekday")
                hr = s.get("start_hour")
                if wd is not None and hr is not None:
                    counts[(wd, hr)] = counts.get((wd, hr), 0) + 1
        return [(wd, hr, c) for (wd, hr), c in counts.items()]

    def _load_predictor_data(self) -> dict | None:
        store = self.app.record_manager.predictor_metrics
        summary = store.summarize(lookback_hours=72)
        d = summary.to_dict()
        if d.get("total_checks", 0) == 0:
            return None
        return d

    # ── Refresh / Render ─────────────────────────────────────────────

    def _on_refresh_clicked(self) -> None:
        self._invalidate_cache()
        self._refresh_current_tab()

    def _on_tab_changed(self, index: int) -> None:
        self._current_tab = index
        self._refresh_current_tab()

    def _refresh_current_tab(self) -> None:
        if self._current_tab == 0:
            self._render_general_tab()
        elif self._current_tab == 1:
            self._render_predictor_tab()
        elif self._current_tab == 2:
            self._render_heatmap_tab()

    def _render_general_tab(self) -> None:
        data = self._get_cached_or_compute("general", self._aggregate_general_data)
        self._gen_cards["total_streamers"].set_value(str(data["total_streamers"]))
        self._gen_cards["total_sessions"].set_value(str(data["total_sessions"]))
        self._gen_cards["avg_priority"].set_value(str(data["avg_priority"]))
        self._gen_cards["avg_consistency"].set_value(str(data["avg_consistency"]))

        streamers = data["streamers"]

        # Disable sorting while populating to prevent Qt row artifacts
        self._gen_table.setSortingEnabled(False)
        self._gen_table.setRowCount(0)
        self._gen_table.setRowCount(max(len(streamers), 1))

        if not streamers:
            self._gen_table.setItem(0, 0, QTableWidgetItem(tr("stats_view.no_streamers", "No streamers configured")))
            for c in range(1, 7):
                self._gen_table.setItem(0, c, QTableWidgetItem(""))
            self._gen_table.setSortingEnabled(True)
            return

        headers = [
            tr("stats_view.col_streamer", "Streamer"),
            tr("stats_view.col_platform", "Platform"),
            tr("stats_view.col_sessions", "Sessions"),
            tr("stats_view.col_avg_duration", "Avg Duration"),
            tr("stats_view.col_priority", "Priority"),
            tr("stats_view.col_consistency", "Consistency"),
            tr("stats_view.col_favorite", "Fav"),
        ]
        self._gen_table.setHorizontalHeaderLabels(headers)

        for i, s in enumerate(streamers):
            self._gen_table.setItem(i, 0, QTableWidgetItem(s["name"]))
            self._gen_table.setItem(i, 1, QTableWidgetItem(s["platform"]))
            self._gen_table.setItem(i, 2, QTableWidgetItem(str(s["sessions"])))
            self._gen_table.setItem(i, 3, QTableWidgetItem(fmt_duration(s["avg_duration"])))
            self._gen_table.setItem(i, 4, QTableWidgetItem(str(round(s["priority"], 2))))
            self._gen_table.setItem(i, 5, QTableWidgetItem(str(round(s["consistency"], 2))))
            fav = "★" if s["favorite"] else ""
            self._gen_table.setItem(i, 6, QTableWidgetItem(fav))

        self._gen_table.setSortingEnabled(True)

    def _render_heatmap_tab(self) -> None:
        # Populate selector if empty
        if self._hm_selector.count() == 0:
            self._hm_selector.addItem(tr("stats_view.select_streamer", "All Streamers"), None)
            for rec in self.app.record_manager.recordings:
                self._hm_selector.addItem(rec.streamer_name, rec.rec_id)

        data = self._get_cached_or_compute("heatmap", lambda: self._build_heatmap_data(self._hm_selector.currentData()))
        self._hm_chart.set_data(data)
        self._hm_chart.set_colors(
            theme_manager.get_color("surface"),
            theme_manager.get_color("accent"),
        )
        self._hm_legend_lbl.setText(tr("stats_view.no_sessions", "No sessions recorded") if not data else "")

    def _on_heatmap_streamer_changed(self) -> None:
        self._invalidate_cache("heatmap")
        self._render_heatmap_tab()

    def _render_predictor_tab(self) -> None:
        data = self._get_cached_or_compute("predictor", self._load_predictor_data)
        has_data = data is not None

        for card in self._pred_cards.values():
            card.setVisible(has_data)
        self._pred_sparkline.setVisible(has_data)
        self._pred_barchart.setVisible(has_data)
        self._pred_spark_label.setVisible(has_data)
        self._pred_bar_label.setVisible(has_data)
        for lbl in self._pred_detail_labels.values():
            lbl.setVisible(has_data)
        self._pred_empty.setVisible(not has_data)

        if not has_data:
            self._pred_empty.setText(tr("stats_view.no_predictor_data", "No predictor data available yet."))
            return

        self._pred_cards["total_checks"].set_value(str(data.get("total_checks", 0)))
        self._pred_cards["live_detections"].set_value(str(data.get("live_detections", 0)))
        lat = data.get("avg_detection_latency_seconds")
        self._pred_cards["avg_latency"].set_value("—" if lat is None else f"{lat:.1f}")
        lh = data.get("avg_likelihood_at_dispatch")
        self._pred_cards["avg_likelihood"].set_value("—" if lh is None else f"{lh:.2f}")

        # Sparkline: build synthetic deque from recent latency values
        # We don't have per-check latencies in summary, so use avg as single point
        # Or better: read raw records and extract latencies
        latencies = self._extract_recent_latencies()
        self._pred_sparkline._data.clear()
        for v in latencies:
            self._pred_sparkline.add_point(int(v))

        disp = [
            data.get("dispatch_fast", 0),
            data.get("dispatch_medium", 0),
            data.get("dispatch_slow", 0),
        ]
        busy = [0, 0, 0]
        self._pred_barchart.set_data(disp, busy, 0)

        self._pred_detail_labels["latency_p50"].setText(
            f"{tr('stats_view.latency_p50', 'Latency P50')}: {data.get('latency_p50') or '—'}"
        )
        self._pred_detail_labels["latency_p95"].setText(
            f"{tr('stats_view.latency_p95', 'Latency P95')}: {data.get('latency_p95') or '—'}"
        )
        self._pred_detail_labels["latency_p99"].setText(
            f"{tr('stats_view.latency_p99', 'Latency P99')}: {data.get('latency_p99') or '—'}"
        )
        self._pred_detail_labels["dispatch_p50"].setText(
            f"{tr('stats_view.dispatch_p50', 'Dispatch P50')}: {data.get('dispatch_p50') or '—'}"
        )
        self._pred_detail_labels["dispatch_p95"].setText(
            f"{tr('stats_view.dispatch_p95', 'Dispatch P95')}: {data.get('dispatch_p95') or '—'}"
        )
        self._pred_detail_labels["dispatch_breakdown"].setText(
            f"{tr('stats_view.dispatch_breakdown', 'Dispatch Breakdown')}: F={data.get('dispatch_fast',0)} M={data.get('dispatch_medium',0)} S={data.get('dispatch_slow',0)}"
        )

    def _extract_recent_latencies(self) -> list[float]:
        store = self.app.record_manager.predictor_metrics
        # Access internal loading or file directly is not ideal; fallback to summary
        # For sparkline we need a series. Use summarize and if avg exists add it.
        summary = store.summarize(lookback_hours=72)
        if summary.avg_detection_latency_seconds is not None:
            return [summary.avg_detection_latency_seconds]
        return []

    # ── Translations / Theme ─────────────────────────────────────────

    def _retranslate_ui(self) -> None:
        l = self.app.language_manager.language.get("stats_view", {})
        self._title_lbl.setText(l.get("title", "Stats"))
        self._refresh_btn.setText(l.get("refresh", "Refresh"))
        self._tabs.setTabText(0, l.get("tab_general", "General"))
        self._tabs.setTabText(1, l.get("tab_predictor", "Predictor"))
        self._tabs.setTabText(2, l.get("tab_heatmap", "Heatmap"))

        for key, card in self._gen_cards.items():
            card.title_lbl.setText(l.get(key, key))
        for key, card in self._pred_cards.items():
            card.title_lbl.setText(l.get(key, key))

        self._pred_spark_label.setText(l.get("avg_latency", "Avg Latency (s)"))
        self._pred_bar_label.setText(l.get("dispatch_breakdown", "Dispatch Breakdown"))

        # Localize heatmap labels and tooltips
        day_keys = ["day_mon", "day_tue", "day_wed", "day_thu", "day_fri", "day_sat", "day_sun"]
        day_labels = [l.get(k, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]) for i, k in enumerate(day_keys)]
        self._hm_chart.set_day_labels(day_labels)
        fmt_template = l.get("cell_tooltip", "{day}, {hour}:00 — {count} sessions")
        self._hm_chart.set_tooltip_formatter(
            lambda d, h, c: fmt_template.format(day=day_labels[d], hour=h, count=c)
        )
        self._hm_legend_lbl.setText(
            l.get("no_sessions", "No sessions recorded") if not self._hm_chart._data else ""
        )

        # NOTE: Tab re-render is done by the caller (e.g. _on_language_changed → _refresh_current_tab).
        # Do NOT render here to avoid duplicate row artifacts in the table.

    def _on_language_changed(self, topic, new_language) -> None:
        self._invalidate_cache()
        # Rebuild heatmap selector so labels pick up new language
        self._hm_selector.clear()
        self._retranslate_ui()
        self._refresh_current_tab()

    def _on_general_table_dblclick(self, row: int, _col: int) -> None:
        """Double-click on a streamer row → navigate to Recordings view with search pre-filled."""
        item = self._gen_table.item(row, 0)
        if not item or not item.text():
            return
        streamer_name = item.text()
        mw = self.app.main_window
        if not mw:
            return
        mw.show_page("recordings")
        rec_view = mw._pages.get("recordings")
        if rec_view and hasattr(rec_view, "search_box"):
            rec_view.search_box.setText(streamer_name)

    def _on_theme_changed(self) -> None:
        c = theme_manager.colors
        self._title_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {c['text']}; background: transparent;"
        )
        self._refresh_btn.setStyleSheet(
            f"QPushButton {{ background: {c['card']}; color: {c['text']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 4px 12px; }}"
        )
        self._gen_table.setStyleSheet(
            f"QTableWidget {{ background: {c['surface']}; alternate-background-color: {c['surface2']}; border: 1px solid {c['border']}; border-radius: 8px; }}"
            f"QHeaderView::section {{ background: {c['card']}; color: {c['text']}; padding: 6px; border: none; }}"
        )
        self._pred_empty.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 13px; background: transparent;"
        )
        self._hm_legend_lbl.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 11px; background: transparent;"
        )

    def refresh(self) -> None:
        self._on_refresh_clicked()
