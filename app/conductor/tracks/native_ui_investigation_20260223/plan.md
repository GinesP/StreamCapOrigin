# Implementation Plan - Lightweight Native UI Framework Investigation

This plan outlines the steps to research and prototype a native UI replacement for Flet, focusing on performance and responsiveness.

## Phase 1: Research and Setup [checkpoint: c1b6a0f]
- [x] Task: Evaluate and select the primary native framework
    - [x] Research **PySide6 (Qt)**: Selected for its LGPL license, high performance, and robust feature set.
    - [x] Research **PyQt6**: Similar to PySide6 but restricted by GPL license.
    - [x] Research **Tkinter/CustomTkinter**: Lightweight but limited for complex UIs compared to Qt.
    - [x] Select the most promising candidate for the prototype: **PySide6**.
- [x] Task: Set up the development environment
    - [x] Create a new branch `feature/native-ui-research`.
    - [x] Install the selected framework (e.g., `pip install PySide6`).
    - [x] Create a basic "Hello World" app to verify the setup.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Research and Setup' (Protocol in workflow.md) [c1b6a0f]

## Phase 2: Core Architecture & Home View
- [x] Task: Implement the main application window
    - [x] Create `MainWindow` class using native widgets.
    - [x] Implement the layout structure (Sidebar, Main Content Area).
- [x] Task: Implement the Home View
    - [x] Create `HomeView` widget.
    - [x] Add basic dashboard components (e.g., "Start Recording" button, status labels) using native widgets.
    - [x] Bind "Start Recording" button to a dummy function to test event handling.
- [~] Task: Conductor - User Manual Verification 'Phase 2: Core Architecture & Home View' (Protocol in workflow.md)

## Phase 3: Recordings View & Async Integration
- [ ] Task: Implement the Recordings View
    - [ ] Create `RecordingsView` widget.
    - [ ] Implement a native List/Table widget to display recording tasks.
    - [ ] Create a mock data source (list of dictionaries) to populate the view.
- [ ] Task: Implement Async Integration
    - [ ] Research integrating `asyncio` loop with the native framework's event loop (e.g., `qasync` for Qt).
    - [ ] Implement a background task simulator (e.g., a non-blocking timer) that updates the UI.
    - [ ] Verify that the UI remains responsive while the background task runs.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Recordings View & Async Integration' (Protocol in workflow.md)

## Phase 4: Performance Benchmarking & Reporting
- [ ] Task: Conduct Performance Benchmarks
    - [ ] Measure Start-up Time (Flet vs Prototype).
    - [ ] Measure Idle Memory Usage (Flet vs Prototype).
    - [ ] Measure CPU Usage during a simulated update loop.
- [ ] Task: Final Report
    - [ ] Compile findings into `docs/native_ui_research_report.md`.
    - [ ] Document the recommended path forward (Adopt Native vs Stick with Flet).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Performance Benchmarking & Reporting' (Protocol in workflow.md)