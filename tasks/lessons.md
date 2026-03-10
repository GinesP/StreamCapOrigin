# Lessons Learned & Error Prevention Patterns

## 1. UI Performance & Startup
- **Pattern:** Lazy Loading (Carga Perezosa).
- **Rule:** Do not instantiate all views in `MainWindow.__init__`. Use a factory method (`_create_page`) and load on-demand in `show_page`.
- **Why:** Prevents freezing the app on startup while Qt creates hundreds of widgets.
- **Applied to:** `app/qt/main_window.py`.

## 2. Startup Sequencing
- **Pattern:** Parallel Startup.
- **Rule:** Show the `MainWindow` BEFORE `awaiting` long asynchronous tasks (update checks, environment verification).
- **Why:** Drastically improves perceived performance; the user sees the interface immediately.
- **Applied to:** `main_qt.py`.

## 3. Nuitka & Standalone Executables
- **Pattern:** Missing Multimedia Plugins.
- **Rule:** When using `PySide6.QtMultimedia`, explicitly include plugins using `--include-qt-plugins=multimedia`.
- **Why:** Nuitka's standalone mode might not detect DLL dependencies for audio/video playback.
- **Pattern:** Hidden/Lazy Imports.
- **Rule:** Explicitly include packages that are loaded dynamically (e.g., inside functions) using `--include-package=app.qt.views`.
- **Why:** Avoids `ImportError` in the compiled executable for components that work fine in the Python environment.

## 4. Initialization Order
- **Error:** `AttributeError: 'QtApp' object has no attribute 'page'`.
- **Lesson:** Define basic compatibility attributes (`self.page`, `self.is_web_mode`, etc.) at the VERY TOP of the `QtApp.__init__` constructor.
- **Why:** Some managers (`InstallationManager`, etc.) access these attributes immediately upon instantiation.
