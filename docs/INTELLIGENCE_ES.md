# Sistema de Inteligencia de StreamCap (Documentación Técnica)

Este documento detalla el funcionamiento interno de los algoritmos de **Inteligencia de Predicción**, **Probabilidad** y **Gestión de Colas** utilizados en StreamCap para optimizar la monitorización de directos.

---

## 1. El Concepto de "Inteligencia"

StreamCap no utiliza un intervalo de tiempo fijo para todos los canales. En su lugar, actúa como un vigilante que aprende los horarios de tus streamers para saber cuándo estar más atento y cuándo descansar, optimizando el uso de CPU, red y evitando bloqueos de IP.

## 2. Los tres pilares del sistema

### A. La Consistencia (Hábitos)
La **Consistencia** mide qué tan "cuadrado" o disciplinado es un streamer con su horario.

*   **Registro**: Cada vez que se detecta un directo, se anota el **Día de la semana** y la **Hora**. Se guardan un máximo de **5 horas distintas** por día para permitir que el sistema "olvide" horarios antiguos si el streamer cambia su rutina.
*   **Cálculo**: 
    $$\text{Consistencia} = \frac{\text{Total de horas registradas}}{\text{Días activos} \times 5}$$
*   **Propósito**: Determinar si los datos históricos son fiables. Una consistencia del 100% indica un patrón muy predecible.

### B. La Probabilidad (Likelihood)
Es un cálculo dinámico que se realiza en cada ciclo de revisión para decidir la urgencia del canal.

| Nivel | Probabilidad | Criterio |
| :--- | :--- | :--- |
| **Alta** | ≥ 0.9 | El streamer suele emitir a esta hora exacta o falta menos de 1 hora para su inicio habitual. |
| **Media** | ≥ 0.5 | Es un día en el que suele emitir, o no hay datos históricos suficientes todavía. |
| **Baja** | ≤ 0.2 | Es un día o una hora en la que nunca o casi nunca emite. |

### C. Gestión de Colas y Trabajadores (Queues)
Dependiendo de la **Probabilidad**, el canal se asigna a una de las tres colas de procesamiento:

| Cola | Prioridad | Frecuencia de Revisión | Trabajadores (Hilos) |
| :--- | :--- | :--- | :--- |
| **Fast (F)** | Alta | ~60 segundos | 1 |
| **Medium (M)** | Media | Tiempo base / 2 | 2 |
| **Slow (S)** | Baja | Tiempo base * 2 | 1 |

---

## 3. Dinámica de Funcionamiento

Imagina un streamer que suele emitir los lunes a las 21:00 con un tiempo base configurado en 5 minutos:

1.  **Modo Descanso (Mañana)**: El sistema detecta baja probabilidad (0.1). El canal entra en la cola **Slow (S)** y se revisa cada 10 minutos.
2.  **Modo Alerta (20:15)**: Al acercarse la hora habitual, la probabilidad sube. El canal salta a la cola **Medium (M)** y se revisa cada 2.5 minutos.
3.  **Modo Caza (20:55)**: La probabilidad llega a 0.9. El canal salta a la cola **Fast (F)** y se revisa cada 60 segundos para capturar el inicio del directo al instante.
4.  **Post-Directo**: Una vez termina el stream, la probabilidad vuelve a bajar gradualmente y el canal regresa a la cola **Slow**.

## 4. Diseño y Limitaciones

*   **¿Por qué solo 5 horas por día?**: Para permitir que el sistema reaccione rápidamente a cambios de horario reales del streamer (capacidad de olvido).
*   **¿Por qué ciclo semanal?**: Los hábitos humanos se rigen principalmente por la semana (trabajo vs. ocio). Un ciclo mensual sería demasiado lento para aprender y requeriría meses de datos para ser efectivo.
*   **Seguridad**: El uso de **múltiples trabajadores** (especialmente los 2 en Medium) permite vaciar las colas rápidamente sin generar ráfagas de peticiones simultáneas que puedan alertar a las plataformas de streaming.
