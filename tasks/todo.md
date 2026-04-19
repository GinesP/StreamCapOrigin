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
  - [ ] NEXT: Verify standalone executable results
- [ ] **Phase 3: Native Feature Parity**
  - [ ] (Ongoing) Migrate remaining Flet views/features to Qt

## Task: Intelligence Dashboard in Home View
- [x] Plan
- [ ] `record_manager.py` → publish `"intelligence_cycle"` event with parsed data dict
- [ ] `home_view.py` → new `IntelligenceMonitor` widget  
  - [ ] `QueueBarChart` (QPainter): grouped bars F/M/S for Dispatched + Busy
  - [ ] `SparklineChart` (QPainter): rolling history of total_dispatched over last 30 cycles
  - [ ] Numeric counters row (Disp F/M/S, Busy F/M/S, Waiting)
  - [ ] Subscribe to `"intelligence_cycle"` event bus event
  - [ ] Animate bar height changes smoothly
- [ ] Insert `IntelligenceMonitor` section into home layout (between stat cards and quick actions)

## Verification Log
- [x] Startup time verified manually: Window shows instantly.
- [x] Recordings view verified manually: Lists population is fluid.
- [ ] Nuitka build verification: Pending user feedback.
