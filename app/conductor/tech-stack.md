# Technology Stack

## Core Technologies
- **Programming Language:** Python
- **UI Framework:** [PySide6 (Qt for Python)](https://doc.qt.io/qtforpython-6/)
- **Asynchronous Runtime:** `asyncio`
- **Event Loop Integration:** `qasync` (Unified Qt and asyncio loop)

## Media Processing
- **Engine:** `ffmpeg` (via custom builders and process management)
- **Downloaders:** Direct stream capture implementation

## Application Architecture
- **State Management:** Page-based state and component-level managers
- **Process Management:** Asynchronous subprocess management for media tasks
- **Configuration:** Custom `ConfigManager` and `LanguageManager`
- **Logging:** Structured logging via a dedicated utility

## Platform & Runtime
- **OS Support:** Windows (primary development environment)
- **Lifecycle Management:** System tray integration and application close handling
