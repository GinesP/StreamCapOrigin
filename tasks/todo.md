# Project Tasks Tracker

## Status
- [x] **Phase 1: Startup Optimization**
  - [x] Lazy loading for UI pages in `MainWindow`
  - [x] Parallel startup sequence in `main_qt.py` (show window before long background tasks)
  - [x] Incremental (staggered) loading in `QtRecordingsView` to keep UI fluid
  - [x] Refactor `QtApp` constructor to allow early UI creation
- [ ] **Phase 2: Build & Deployment Reliability**
  - [x] Fix Nuitka build: missing multimedia plugins
  - [x] Fix Nuitka build: include lazy-loaded packages (`app.qt.views`, `components`)
  - [ ] **NEXT:** Verify standalone executable results (user will run build now)
- [ ] **Phase 3: Native Feature Parity**
  - [ ] (Ongoing) Migrate remaining Flet views/features to Qt

## Task: Log Viewer (full rewrite of log_view.py)
- [x] Plan
- [x] Rewrite `app/qt/views/log_view.py`
  - [x] Sink loguru → Qt signal con timestamp + level + message
  - [x] `QTextEdit` con HTML rich-text para colores por nivel
  - [x] Paleta de colores: DEBUG/INFO/SUCCESS/WARNING/ERROR/RETRY/STREAM + INTELLIGENCE highlight
  - [x] Toolbar: Auto-scroll toggle, filtro por nivel (ComboBox), búsqueda, Clear, Copy-all
  - [x] Badge contador de errores/warnings en tiempo real
  - [x] Límite de líneas (circular buffer 2000) para no crecer sin límite
  - [x] Reaccionar a cambios de tema (ThemeManager)

## Verification Log
- [x] Startup time verified manually: Window shows instantly.
- [x] Recordings view verified manually: Lists population is fluid.
- [ ] Nuitka build verification: Pending user feedback from tonight's build.
