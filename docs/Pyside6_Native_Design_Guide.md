# Guía Premium PySide6 Nivel 10: Elite Design Framework

Esta guía documenta la arquitectura definitiva para aplicaciones de alto rendimiento con diseño **Neutral-Dark**, reactividad estética instantánea (**Hot-Reload**) e integración nativa perfecta en Windows.

## 1. El Motor de Temas Reactivo (Data-Driven JSON)

En el Nivel 10, el diseño no está "quemado" en el código. Se gestiona un **ThemeManager** que vigila un archivo `theme.json` externo.

### Arquitectura del ThemeManager
```python
from PySide6.QtCore import QFileSystemWatcher, Signal, QObject
import json, os

class ThemeManager(QObject):
    themeChanged = Signal() # Se emite al detectar cambios en el JSON

    def _init_themes(self):
        self.theme_file = "theme.json"
        self.watcher = QFileSystemWatcher([self.theme_file])
        self.watcher.fileChanged.connect(self._reload)

    def _reload(self):
        # Recarga el JSON y notifica a toda la App
        with open(self.theme_file, "r") as f:
            self.current = json.load(f)["neutral_dark"]
        self.themeChanged.emit()
```

---

## 2. Reactividad en Tiempo Real (Hot-Reload)

Para que toda la App cambie de color sin reiniciarse, usamos el patrón de **Suscripción y Pulido**.

### El Secreto del "Unpolish/Polish"
Qt requiere forzar la reevaluación del motor CSS al cambiar propiedades dinámicas.
```python
def update_widget_style(w, state=None):
    if state: w.setProperty("state", state)
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()
```

### Suscripción de Componentes
Los componentes con dibujo manual (`QPainter`) deben suscribirse a la señal para refrescar su caché de colores:
```python
class CustomChart(QWidget):
    def __init__(self):
        theme.themeChanged.connect(self._refresh_cache)
        self._refresh_cache()

    def _refresh_cache(self):
        self._color = theme.get_color("accent")
        self.update()
```

---

## 3. Renderizado de Élite (Nivel 10 Anti-Aliasing)

Para eliminar bordes dentados en interfaces oscuras, aplicamos una triple estrategia de renderizado gráfico.

### Estrategia de Rasterización en Componentes Custom
```python
def paintEvent(self, event):
    p = QPainter(self)
    # CONFIGURACIÓN ÉLITE:
    p.setRenderHints(
        QPainter.Antialiasing |             # Suaviza bordes de formas
        QPainter.TextAntialiasing |         # Suaviza curvas de fuentes
        QPainter.SmoothPixmapTransform      # Suaviza transformaciones de imágenes
    )
```

---

## 4. Sombra Nativa Premium (WM_NCCALCSIZE)

Para ventanas sin bordes, interceptamos los mensajes del sistema para que Windows aplique la sombra DWM real (acelerada por GPU).

```python
def nativeEvent(self, eventType, message):
    if eventType == "windows_generic_MSG":
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x0083: # WM_NCCALCSIZE
            return True, 0 # Elimina bordes blancos pero mantiene la sombra
    return super().nativeEvent(eventType, message)
```

---

## 5. Tokens de Diseño (theme.json)

| Token | Propósito | Valor Sugerido |
|---|---|---|
| `bg` | Fondo profundo | `#252525` |
| `sidebar` | Contraste máximo | `#1A1A1A` |
| `surface` | Cards elevadas | `#2D2D2D` |
| `surface2`| Estado Hover | `#333333` |
| `accent` | Color de marca 🟠 | `#FF6428` |
| `border` | Líneas de definición | `#383838` |

---

> [!TIP]
> **Optimización de Memoria**: En el Nivel 10, cacheamos los objetos `QColor` y `QPen` en los widgets. Consultar el diccionario de temas 60 veces por segundo en un `paintEvent` es un desperdicio de ciclos que evitamos con el sistema de señales.

## 6. Despliegue Élite: Nuitka & Qt Resources (.qrc)

Para convertir el script en un producto comercial, pasamos de la interpretación a la **compilación real en C++**.

### A. El Sistema de Recursos (.qrc)
Evita que el usuario pierda el JSON o los activos. Integra todo en la memoria del binario.
1. Crea `resources.qrc`:
   ```xml
   <RCC><qresource><file>theme.json</file></qresource></RCC>
   ```
2. Compila a Python: `pyside6-rcc resources.qrc -o resources_rc.py`
3. Carga en código: `QFile(":/theme.json")`

### B. Compilación con Nuitka
Nuitka traduce Python a C++ y genera un binario optimizado, protegido y de arranque instantáneo.

```bash
python -m nuitka --standalone --onefile --plugin-enable=pyside6 --zig \
--windows-disable-console --include-data-file=theme.json=theme.json \
--windows-icon-from-ico=assets/logo.ico --output-dir=dist main.py
```

### C. Por qué Nuitka vs PyInstaller
- **Rendimiento**: Ejecución nativa, no descompresión temporal.
- **Protección**: Código máquina, no bytecode de Python fácil de leer.
- **Seguridad**: Binario único sin dependencias visibles.

---

## 7. Micro-interacciones: Transiciones de Lujo (Nivel 10.1)

Para evitar el "latigazo visual" al cambiar de estado o de tema, implementamos transiciones de opacidad.

```python
def fade_transition(widget, duration=300):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    ani = QPropertyAnimation(effect, b"opacity")
    ani.setDuration(duration)
    # ... lógica de fade out / fade in
```

## 8. Paletas Duales Estándar

### Neutral Dark (Default)
`#252525` (BG) | `#E1E1E1` (Text) | `#FF6428` (Accent)

### Neutral Light (Professional Light)
`#F5F5F7` (BG) | `#1D1D1F` (Text) | `#007AFF` / `#FF6428` (Accent)

---

> [!TIP]
> **Consistencia Visual**: Al usar el modo claro, reduce ligeramente la opacidad de los bordes (`border_h`) para evitar que la interfaz se sienta "enjaulada". El espacio negativo es tu aliado en el Nivel 10.
