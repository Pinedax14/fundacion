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
| Limpieza/preprocesamiento | ✅ Existe | `scripts/limpieza_datos.py`: parsea fechas, normaliza categóricas, elimina duplicados, documenta nulos explícitamente, y maneja 2 problemas reales de calidad de datos encontrados en el proceso (ver abajo) |
| EDA | ✅ Existe | `notebooks/eda_fundacion.ipynb`, ejecutado de punta a punta (20 celdas, 0 errores) |
| Visualizaciones | ✅ Existe | 5 gráficos exportados a PNG (`data/processed/grafico_*.png`) con `matplotlib`/`seaborn`, paleta salvia/terracota de la marca |
| Modelos predictivos | ❌ No existe | Opcional según el plan original; no se hizo por tiempo — dataset actual es muy pequeño (8 solicitudes) para que un modelo sea significativo |
| Notebook Jupyter | ✅ Existe | `notebooks/eda_fundacion.ipynb` |
| Datos fuente disponibles | ✅ Sí | Datos reales en la BD Postgres/Neon: `mascotas`, `solicitudes_adopcion`, `donaciones`, `donaciones_items`, `reportes`, `voluntariados` |
| Script de extracción | ✅ Existe | `scripts/extraer_datos.py` — exporta las 7 tablas relevantes a `data/raw/*.csv` reutilizando `create_app()`/`db.engine` |
| Dataset documentado | ✅ Existe | `data/diccionario_datos.md` — describe cada columna de cada tabla, marca explícitamente cuáles son PII |
| Entorno de análisis separado | ✅ Existe | `requirements-datascience.txt` (pandas, numpy, matplotlib, seaborn, jupyter, notebook) — no mezclado con `requirements.txt` de producción |

Ya no es la materia con más trabajo pendiente — los 3 artefactos núcleo (script de extracción, limpieza, notebook EDA) están completos y verificados corriendo contra la BD real. Lo que queda es opcional (modelo predictivo) o de pulido (dataset anonimizado para entrega).

## 3. Plan de acción

1. ~~**Preparar el entorno**~~ ✅ **Hecho** — `requirements-datascience.txt` separado de `requirements.txt`.

2. ~~**Script de extracción**~~ ✅ **Hecho** — `scripts/extraer_datos.py`. Se corre con `python scripts/extraer_datos.py`; regenera `data/raw/*.csv` desde la BD real cuando se necesite un corte nuevo.

3. ~~**Script de limpieza**~~ ✅ **Hecho** — `scripts/limpieza_datos.py`. Además de lo planeado, documentó y manejó explícitamente 2 problemas de calidad de datos reales encontrados en producción:
   - `mascotas.especie` tenía un valor `"Si"` (typo de captura en el panel admin).
   - `solicitudes_adopcion.ingresos` mezclaba rangos válidos (`"2000000-3000000"`) con enteros crudos heredados de antes de la migración `migrate_ingresos_type.py` — incluyendo un sentinel de overflow `2147483647` (máximo de un INTEGER de 32 bits). Se marcan como `"legacy_invalido"` en vez de descartarse.

4. ~~**Notebook Jupyter con el EDA**~~ ✅ **Hecho** — `notebooks/eda_fundacion.ipynb`:
   - Distribución de mascotas por especie/estado/sexo/edad.
   - Tasa de conversión de solicitudes de adopción (pendiente/aprobada/rechazada) + solicitudes por mes.
   - Tiempo hasta la primera solicitud de adopción por mascota (proxy de "qué tan rápido genera interés"), con nota metodológica de que la muestra actual (8 solicitudes) es muy pequeña para generalizar.
   - Reportes de maltrato por estado y por mes.
   - Donaciones monetarias: sección lista pero sin datos aún (tabla vacía en este corte).

5. ~~**Visualizaciones exportables**~~ ✅ **Hecho** — 5 PNG en `data/processed/grafico_*.png`. Los mismos insights (donaciones por mes, mascotas por especie/estado, adopciones por mes) ya alimentan el dashboard de Chart.js del panel admin vía la API JSON de la materia de Móviles — la conexión que proponía este punto ya está tendida en código, no solo en teoría.

6. **Modelo predictivo (opcional/plus)** — sigue pendiente y sigue siendo opcional. Con el volumen actual de datos (8 solicitudes, 17 mascotas) no aportaría una predicción confiable; tiene más sentido revisitarlo cuando haya más historial.

7. ~~**Dataset final documentado**~~ ✅ **Hecho parcialmente** — `data/diccionario_datos.md` documenta cada columna. Los CSV en sí (`data/raw/`, `data/processed/*.csv`) **no están en git** a propósito: contienen PII real (dirección, teléfono de solicitantes de adopción, ubicación de reportes). Si se van a entregar como parte de un trabajo académico, hay que generar antes una versión anonimizada (quitar `direccion`, `telefono`, `correo`, `nombre_completo`, `ubicacion`) — está anotado como recomendación en el propio diccionario de datos.
