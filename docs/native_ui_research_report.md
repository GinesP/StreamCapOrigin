# Research Report: Native UI Transition (PySide6 vs Flet)

## Executive Summary
This report evaluates the feasibility and performance benefits of replacing the current Flet (Flutter-based) UI with a native Python UI using PySide6 (Qt). Our investigation shows significant improvements in memory efficiency and resource management.

## Performance Benchmarks
Testing was conducted on a Windows environment measuring idle state performance after a 2-second initialization period.

| Metric | Flet (Current) | PySide6 (Prototype) | Improvement |
| :--- | :--- | :--- | :--- |
| **Idle Avg Memory** | 216.43 MB | 71.27 MB | **67.1% Reduction** |
| **Idle Max Memory** | 278.99 MB | 71.27 MB | **74.5% Reduction** |
| **Startup Time** | ~2.0s | ~2.0s | Parity |

## Qualitative Findings
- **Responsive Async:** PySide6 integrated with `qasync` allows for a seamless non-blocking UI during background processing (e.g., ffmpeg tasks).
- **Native Look & Feel:** Qt widgets provide a more consistent experience with the Windows OS compared to Flet's custom rendering.
- **Dependency Management:** PySide6 is a mature, well-documented library with an LGPL license suitable for the project's requirements.

## Implementation Details (Prototype)
- **MainWindow:** Uses `QMainWindow` with `QHBoxLayout` for sidebar navigation.
- **HomeView:** Implements status cards and async task simulation.
- **RecordingsView:** Uses `QTableWidget` for efficient data display.
- **Event Loop:** Unified `asyncio` loop via `qasync.QEventLoop`.

## Recommendation
**Decision: Adopt PySide6 for future UI development.**
The memory savings alone (~150MB - 200MB reduction) justify the transition, especially for users running multiple concurrent recording tasks.

## Next Steps
1. Create a migration plan for remaining pages (Settings, About, Storage).
2. Implement custom styling (QSS) to match StreamCap branding.
3. Integrate system tray and desktop notifications into the native architecture.
