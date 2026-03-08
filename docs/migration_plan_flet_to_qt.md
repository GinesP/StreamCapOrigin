# Plan de Migración: Flet → Qt (StreamCap)

Este documento detalla la estrategia para migrar el frontend de StreamCap de **Flet** a **Qt (PySide6)**, manteniendo una arquitectura limpia y desacoplada que permita la coexistencia de ambas interfaces durante la transición.

## 📁 Estado de la Migración

- [x] **Fase 0: Preparación** (Rama, Directorios, Entry Point)
- [x] **Fase 1: Abstracción de Eventos (EventBus)** - El core ya no depende de Flet
- [x] **Fase 2: Ventana Principal y Navegación** - Shell de Qt con sidebar funcional
- [x] **Fase 3: Vista de Grabaciones (Grid/List)** - Portando RecordingCard a Qt
- [x] **Fase 4: Configuración y Diálogos** (SettingsView y AddStream integrados)
- [x] **Fase 5: Reproductor y Utilidades de UI** (StorageView y VideoPlayer)
- [ ] **Fase 6: Diálogos Restantes y Pulido Final**

---

## 🛠️ Fase 1: Desacoplamiento (Completada)

Se ha implementado un `EventBus` (`app/event_bus.py`) que actúa como puente agnóstico. 

- [x] **Crear clase EventBus** (`app/event_bus.py`)
- [x] **Vincular App Manager** con EventBus
- [x] **Desacoplar Managers Core** (RecordingManager, StreamManager, InstallationManager)
- [x] **Integrar qasync** para soporte de asyncio en el loop de Qt
- [x] **Crear main_qt.py** como punto de entrada paralelo

---

## 🖼️ Fase 2: Layout Principal (Completada)

Se ha creado la estructura base de la aplicación Qt siguiendo el diseño moderno de StreamCap.

- [x] **Sistema de Temas Qt** (`app/qt/themes/theme.py`) - Soporte Dark/Light
- [x] **Barra Lateral de Navegación** (`app/qt/navigation/sidebar.py`)
- [x] **Shell Principal (MainWindow)** (`app/qt/main_window.py`) con QStackedWidget
- [x] **Barra de Estado** (Notificaciones integradas)

---

## 📺 Fase 3: Vista de Grabaciones (Completada)

**Objetivo**: Migrar el grid de grabaciones y sus tarjetas interactivas.

- [x] **Portar RecordingsView** (`app/qt/views/recordings_view.py`) - Layout dinámico
- [x] **Componente QtRecordingCard** (Avatar, indicadores de estado, acciones en hover)
- [x] **Soporte Grid/List Mode** (Toggle funcional y layout responsivo)
- [x] **Diálogo de "Add Stream"** (Versión Qt integrada con el core)
- [x] **Conexión EventBus** (Sincronización total de estados en tiempo real)

---

---

## 🎬 Fase 5: Reproductor y Utilidades de UI (Completada)

**Objetivo**: Implementar el navegador de archivos y el reproductor de vídeo nativo.

- [x] **Vista de Almacenamiento (Storage)** (`app/qt/views/storage_view.py`) - Navegación de archivos
- [x] **Reproductor de Vídeo Nativo** (`app/qt/components/video_player.py`) - Basado en QtMultimedia
- [x] **Soporte Fullscreen** (Doble clic, tecla Esc y botón dedicado)
- [x] **Vista About** (`app/qt/views/about_view.py`) - Información del proyecto y enlaces externos
- [x] **Integración Global** (Acceso al reproductor desde tarjetas y explorador)

---

## 🛠️ Fase 6: Filtros, Diálogos y Pulido (En progreso)

**Objetivo**: Añadir funcionalidades avanzadas de gestión y controles de seguridad.

- [x] **Sistema de Filtros, Búsqueda y Ordenamiento Dinámico** - Filtrado por texto, estado y plataforma con layout fluido.
- [x] **Acciones en Lote (Batch Actions)** - Iniciar y detener monitoreo y eliminación masiva de *streams* en la vista actual.
- [ ] **Diálogo de Edición de Streamers** - Permitir modificar configuración de cada stream.
- [x] **Diálogos de Confirmación y Cierre Limpio** - Avisos antes de borrar o cerrar la app, implementando paradas asíncronas de guardado.
- [ ] **Atajos de Teclado Globales** - Navegación rápida por la app.

---

## ⚙️ Cómo ejecutar el prototipo Qt

Durante la migración, puedes seguir usando la versión Flet con `python main.py`. Para probar la nueva versión Qt, usa:

```bash
python main_qt.py
```
