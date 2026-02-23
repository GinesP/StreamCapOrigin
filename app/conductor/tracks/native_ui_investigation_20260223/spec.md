# Specification - Lightweight Native UI Framework Investigation

## Overview
This track focuses on researching and prototyping an alternative native UI framework for StreamCapOrigin to replace Flet. The goal is to achieve a lighter, faster, and more memory-efficient interface using native OS components while maintaining core functionality (recording management, stream monitoring, and async tasks). **Native components are preferred over WebView-based solutions.**

## Functional Requirements
- **Framework Research:** Evaluate native UI frameworks like **PySide6 (Qt)**, **PyQt6**, or **Tkinter/CustomTkinter** for their performance, native look-and-feel, and integration ease with the existing Python backend.
- **Functional Prototype:** Develop a native UI prototype that includes:
    - **Home View:** Basic dashboard and status overview using native widgets.
    - **Recordings View:** List and manage recording tasks with real data binding and native list components.
- **Async Integration:** Verify that the native framework integrates seamlessly with `asyncio` for handling `ffmpeg` processes and network requests without blocking the UI main loop.
- **Component Mapping:** Identify how Flet components (Sidebar, Page containers, Cards) map to the selected native framework's equivalent widgets.

## Non-Functional Requirements
- **Performance:** Significant reduction in memory footprint compared to the current Flet (Flutter) implementation.
- **Native Look & Feel:** Prioritize frameworks that provide or closely emulate native OS components and behavior.
- **Responsiveness:** Improved start-up time and snappy UI interaction.

## Acceptance Criteria
- A research report comparing Flet vs. the investigated native alternative(s).
- A functional native prototype demonstration showing the Home and Recordings views.
- Successful execution of an asynchronous recording task within the native prototype.
- Performance benchmarks (Memory, CPU, Start-up time) comparing Flet and the native prototype.

## Out of Scope
- Full migration of all application pages (About, Settings, Storage, etc.).
- Final production-ready styling and themes.
- Implementation of system tray integration in the initial prototype.