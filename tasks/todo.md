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

## Verification Log
- [x] Startup time verified manually: Window shows instantly.
- [x] Recordings view verified manually: Lists population is fluid.
- [ ] Nuitka build verification: Pending user feedback from tonight's build.
