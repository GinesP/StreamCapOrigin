import unittest

from PySide6.QtWidgets import QApplication
from app.qt.components.heatmap_chart import HeatmapChart

# Needed for QApplication instantiation in tests
_app = QApplication.instance() or QApplication([])


class HeatmapChartTests(unittest.TestCase):
    def test_set_data_empty(self):
        chart = HeatmapChart()
        chart.set_data([])
        self.assertEqual(chart._data, [])

    def test_set_data_populates_grid(self):
        chart = HeatmapChart()
        chart.set_data([(0, 14, 5), (3, 20, 2)])
        self.assertEqual(chart._data, [(0, 14, 5), (3, 20, 2)])
        self.assertEqual(chart._grid[0][14], 5)
        self.assertEqual(chart._grid[3][20], 2)

    def test_paint_event_empty_data_does_not_crash(self):
        chart = HeatmapChart()
        chart.set_data([])
        chart.resize(400, 300)
        try:
            chart.repaint()
        except Exception as e:
            self.fail(f"repaint raised {e}")

    def test_paint_event_with_data_does_not_crash(self):
        chart = HeatmapChart()
        chart.set_data([(0, 14, 5), (3, 20, 2)])
        chart.resize(400, 300)
        try:
            chart.repaint()
        except Exception as e:
            self.fail(f"repaint raised {e}")

    def test_tooltip_text(self):
        chart = HeatmapChart()
        chart.set_data([(1, 10, 3)])
        chart.resize(400, 300)
        # Simulate mouse move over cell (1,10)
        # cell_rect logic mirrors internal calculation
        chart._hover_cell = (1, 10)
        text = chart._build_tooltip(1, 10)
        self.assertIn("10:00", text)
        self.assertIn("3", text)

    def test_max_count_for_color_scale(self):
        chart = HeatmapChart()
        chart.set_data([(0, 0, 1), (0, 1, 10)])
        self.assertEqual(chart._max_count, 10)


if __name__ == "__main__":
    unittest.main()
