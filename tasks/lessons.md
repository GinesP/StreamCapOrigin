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

## 5. Windows File Lock After Subprocess Termination
- **Error:** `WinError 32: El proceso no puede tener acceso al archivo porque está siendo utilizado por otro proceso` al intentar convertir/borrar el archivo `.ts` justo después de que ffmpeg termina.
- **Symptom:** Quedan duplicados (`.ts` + `.mp4`) porque la conversión falla con el fichero bloqueado y el original no se puede borrar.
- **Root cause:** En Windows, el kernel puede tardar unos instantes en liberar el handle de fichero de un proceso hijo incluso después de que `process.communicate()` o `process.wait()` retornan en el proceso padre. La versión Flet no lo sufría porque su event loop añadía latencia suficiente de forma accidental.
- **Rule:** Nunca acceder a un fichero producido por un subproceso (ffmpeg, etc.) inmediatamente después de su terminación. Implementar un **bucle de espera activa** que pruebe abrir el fichero (`open(..., "rb")`) y reintente con `asyncio.sleep` hasta confirmar que está desbloqueado.
- **Pattern:** Retry-with-backoff en `_do_converts_mp4` → hasta 10 intentos (2 s entre cada uno) antes de la conversión; hasta 5 intentos (2 s entre cada uno) antes de borrar el original.
- **Applied to:** `app/core/recording/stream_manager.py` → `_do_converts_mp4`.

## 6. Recording Model Initialization
- **Error:** `'<=' not supported between instances of 'NoneType' and 'int'` en recording_card.py al mostrar nuevas grabaciones.
- **Root cause:** `Recording.__init__` no inicializa `loop_time_seconds`. Se setea después en `record_manager.initialize_dynamic_state()`, pero las grabaciones creadas en diálogos la saltan.
- **Rule:** Cuando se crea un Recording fuera de `record_manager`, inicializar todos los campos que usa la UI (`loop_time_seconds`, `added_at`).
- **Applied to:** `app/qt/components/add_stream_dialog.py` y `app/qt/components/recording_card.py`.

## 7. Dialog Translation Dictionary
- **Error:** `AttributeError: 'QtAddStreamDialog' object has no attribute '_'` al usar `self._["live_room"]`.
- **Root cause:** `self._` es un patrón de traducciones usado en managers, no en diálogos Qt.
- **Rule:** En diálogos Qt, usar strings hardcodeados o acceder a traducciones via `app.language_manager`.
- **Applied to:** `app/qt/components/add_stream_dialog.py`.

## 8. Recording ID Generation
- **Error:** La lista de streams no se actualizaba al agregar nuevos - las cards no aparecían.
- **Root cause:** El diálogo creaba `Recording(rec_id=None)`. La UI usaba `self._cards[recording.rec_id]` con key `None`, pero luego buscaba por UUID real.
- **Rule:** Generar UUID con `uuid.uuid4()` al crear Recording en la UI (igual que hace Flet en `recordings_view.py`).
- **Pattern:** `rec_id=str(uuid.uuid4())`
- **Applied to:** `app/qt/components/add_stream_dialog.py`.

## 9. Flet → Qt Migration Patterns
- **Pattern:** `page.run_task()` en Flet → `event_bus.run_task()` en Qt
- **Pattern:** `self._["key"]` en Flet → strings hardcodeados o `language_manager` en Qt
- **Pattern:** UI dialogs no tienen acceso a `self._` - deben usar strings locales o pedir traducciones al app
- **Reference:** `docs/migration_plan_flet_to_qt.md`
