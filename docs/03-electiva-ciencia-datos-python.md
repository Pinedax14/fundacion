# Electiva III — Ciencia de Datos con Python

Aplicado sobre: **Fundación Almas con Cola** (Flask + PostgreSQL/Neon).

## 1. Requisitos de la materia

### Temas que debe cubrir el proyecto
- [ ] Limpieza y preprocesamiento de datos
- [ ] Análisis exploratorio de datos (EDA)
- [ ] Visualizaciones (Matplotlib/Seaborn/Plotly)
- [ ] Modelos predictivos (opcional)
- [ ] Exportación de datos finales (.csv/.json/BD)

### Entregables
- [ ] Script de limpieza
- [ ] Informe EDA
- [ ] Dataset limpio y documentado
- [ ] Gráficos exportables
- [ ] Notebook Jupyter final

## 2. Estado actual del proyecto

| Requisito | Estado | Evidencia |
|---|---|---|
| Limpieza/preprocesamiento | ❌ No existe | `migrate_ingresos_type.py` es una migración de esquema puntual, no limpieza de datos para análisis |
| EDA | ❌ No existe | — |
| Visualizaciones | ❌ No existe | `matplotlib`, `seaborn`, `plotly`, `pandas`, `numpy`, `jupyter` **no están ni en `requirements.txt`** |
| Modelos predictivos | ❌ No existe | — |
| Notebook Jupyter | ❌ No existe | Cero archivos `.ipynb` en el repo |
| Datos fuente disponibles | ✅ Sí | Hay datos reales en la BD Postgres/Neon: `mascotas`, `solicitudes_adopcion`, `donaciones`, `donaciones_items`, `reportes`, `voluntariados` |
| Exportación CSV (mecanismo) | 🟡 Existe uno, no es el pedido | `/admin/auditoria/exportar` exporta logs de auditoría a CSV desde la app — útil como referencia técnica, pero no es el dataset de análisis que pide la materia |
| Script de conteo | 🟡 Parcial/reutilizable | `check_counts.py` ya conecta a la BD y cuenta registros por tabla — buen punto de partida para el script de extracción |

Esta es la materia con **más trabajo pendiente**: no hay ningún artefacto de ciencia de datos todavía, pero el proyecto tiene la ventaja de contar con datos reales y propios en vez de un dataset externo.

## 3. Plan de acción

1. **Preparar el entorno** — agregar `pandas`, `numpy`, `matplotlib`, `seaborn`, `plotly`, `jupyter`, `sqlalchemy` (ya está) a un archivo separado, ej. `requirements-datascience.txt`, para no mezclar dependencias de análisis con las de producción.

2. **Script de extracción** — partir de la lógica de conexión que ya usa `check_counts.py`/`app/rutas/conexion.py` para exportar a CSV crudo las tablas relevantes: `mascotas`, `solicitudes_adopcion`, `donaciones`, `donaciones_items`, `reportes`, `voluntariados`.

3. **Script de limpieza** (`scripts/limpieza_datos.py` o celda inicial del notebook):
   - Normalizar fechas y tipos (ej. edades, especie, estado de la mascota).
   - Manejar nulos/vacíos de forma explícita (documentar la decisión, no solo eliminarlos).
   - Eliminar duplicados y estandarizar categorías (ej. texto libre de "especie" o "raza" si aplica).

4. **Notebook Jupyter con el EDA** — análisis sugeridos usando los propios datos de la fundación:
   - Tiempo promedio de adopción por especie/edad/tamaño de mascota.
   - Tendencia de donaciones por mes (monto y cantidad).
   - Distribución de reportes de maltrato por tipo/zona (si el modelo tiene ubicación).
   - Tasa de conversión: solicitudes de adopción → adopciones efectivas.

5. **Visualizaciones exportables** — generar los gráficos del EDA como PNG/HTML reutilizables. Esto conecta directamente con el requisito de "gráficos interactivos" de la materia de Dispositivos Móviles: los mismos insights pueden alimentar el dashboard del panel admin (vía Chart.js) usando los números que salgan de este análisis.

6. **Modelo predictivo (opcional/plus)** — por ejemplo, un modelo simple (regresión logística o árbol de decisión con `scikit-learn`) que estime la probabilidad de adopción rápida según atributos de la mascota (especie, edad, tiempo en el refugio). Se puede marcar como "extra" si el tiempo no alcanza para todo.

7. **Dataset final documentado** — exportar el dataset limpio (`.csv` y/o `.json`) junto a un diccionario de datos (qué significa cada columna, tipo, unidad) como entregable final.
