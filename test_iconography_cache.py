import sys
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from app.qt.utils import iconography
from app.qt.utils.iconography import clear_icon_cache, icon_cache_stats, icon_pixmap, icon_svg_path


class IconographyCacheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        clear_icon_cache()

    def test_reuses_cached_tinted_svg_pixmap(self):
        if icon_svg_path("home") is None:
            self.skipTest("home.svg is not available")

        before = icon_cache_stats()["renders"]

        first = icon_pixmap("home", size=18, color="#A0A0A0")
        after_first = icon_cache_stats()
        second = icon_pixmap("home", size=18, color="#A0A0A0")
        after_second = icon_cache_stats()

        assert not first.isNull()
        assert not second.isNull()
        assert after_first["renders"] == before + 1
        assert after_second["renders"] == after_first["renders"]
        assert after_second["entries"] == 1

    def test_clear_icon_cache_removes_entries(self):
        if icon_svg_path("home") is None:
            self.skipTest("home.svg is not available")

        icon_pixmap("home", size=18, color="#A0A0A0")
        assert icon_cache_stats()["entries"] > 0

        clear_icon_cache()

        assert icon_cache_stats()["entries"] == 0

    def test_high_dpi_svg_render_uses_full_physical_viewport(self):
        if icon_svg_path("home") is None:
            self.skipTest("home.svg is not available")

        with patch.object(iconography, "_device_pixel_ratio", return_value=2.0):
            pix = icon_pixmap("home", size=18, color="#A0A0A0")

        image = pix.toImage()
        painted_points = [
            (x, y)
            for y in range(image.height())
            for x in range(image.width())
            if image.pixelColor(x, y).alpha() > 0
        ]
        xs = [point[0] for point in painted_points]
        ys = [point[1] for point in painted_points]

        assert pix.devicePixelRatio() == 2.0
        assert max(xs) - min(xs) > 20
        assert max(ys) - min(ys) > 20


if __name__ == "__main__":
    unittest.main()
