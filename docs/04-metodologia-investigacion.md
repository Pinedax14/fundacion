# Metodología de la Investigación

Aplicado sobre: **Fundación Almas con Cola** (Flask + PostgreSQL/Neon).

## 1. Requisitos de la materia

### Temas que debe cubrir el proyecto
- [ ] Investigación de necesidades de usuarios
- [ ] Definición de objetivos
- [ ] Diseño de evaluación de usabilidad
- [ ] Medición de impacto en la toma de decisiones
- [ ] Métodos de análisis de datos

### Entregables
- [ ] Informe de investigación de usuarios
- [ ] Documento de objetivos
- [ ] Plan de usabilidad
- [ ] Estudio de impacto
- [ ] Documento de métodos de análisis

## 2. Estado actual del proyecto

| Requisito | Estado | Evidencia |
|---|---|---|
| Investigación de usuarios (real) | ❌ No existe | `PRODUCT.md` describe segmentos de usuario ("Adoptantes potenciales", "Voluntarios y donantes", "Administradores", "Público general") de forma informal, sin encuestas/entrevistas reales detrás |
| Definición de objetivos (formal) | ❌ No existe | Los objetivos del producto están implícitos en `PRODUCT.md`, no como documento de investigación |
| Evaluación de usabilidad (con usuarios reales) | 🟡 Existe una versión automatizada, no la pedida | `.impeccable/critique/*.md` — 2 críticas heurísticas de Nielsen (automáticas, sobre el home) — es una auditoría de diseño, **no** una prueba de usabilidad con personas reales |
| Medición de impacto en decisiones | ❌ No existe | — |
| Métodos de análisis de datos (documentado) | ❌ No existe | — |

Esta materia depende en parte de que el **MVP funcional** (Materia 1) y el **EDA** (Materia 3) ya existan, porque la investigación de usuarios y el estudio de impacto se hacen *sobre* el producto real y sus datos.

**Actualización**: el EDA de la Materia 3 ya está completo (`notebooks/eda_fundacion.ipynb`) y la API JSON + dashboard de la Materia 1 también — el bloqueador ya no es técnico. Esta materia puede empezar ya: el punto 4 (estudio de impacto, opción B) puede usar directamente los hallazgos del notebook (ej. tasa de conversión de solicitudes de adopción, distribución de mascotas por especie) en vez de esperar más datos.

## 3. Plan de acción

1. **Documento de objetivos** — partir de los objetivos ya implícitos en `PRODUCT.md` y formalizarlos como preguntas de investigación, por ejemplo:
   - ¿Qué fricciones encuentran los adoptantes al buscar y solicitar una mascota?
   - ¿Qué información necesitan los donantes antes de donar?
   - ¿El flujo de reporte de maltrato es lo suficientemente rápido/claro en un momento de urgencia?

2. **Investigación de necesidades de usuarios**:
   - Diseñar una encuesta corta (Google Forms) dirigida a adoptantes/voluntarios reales o a un grupo simulado (compañeros, familia, conocidos que adopten el rol de usuario) sobre necesidades y fricciones con apps de adopción de mascotas.
   - Documentar hallazgos y, si aplica, construir 1-2 personas (perfiles representativos) a partir de los segmentos ya nombrados en `PRODUCT.md`.

3. **Plan de evaluación de usabilidad**:
   - Definir tareas típicas medibles sobre el MVP real: "adoptar una mascota", "hacer una donación", "reportar un caso de maltrato", "registrarse como voluntario".
   - Definir protocolo (moderado o no moderado, *thinking aloud*) y métricas (tasa de éxito, tiempo por tarea, errores, SUS score).
   - Ejecutar el test con 3-5 usuarios reales sobre la app ya funcionando y recolectar los resultados — esto sí reemplaza/complementa la crítica heurística automática que ya existe.

4. **Estudio de impacto en la toma de decisiones**:
   - Opción A (retrospectiva): comparar alguna métrica antes/después de un cambio ya hecho (ej. el rediseño visual reciente de la paleta y de la sección de donaciones) usando los datos reales de la BD.
   - Opción B (proyectiva): usar los hallazgos del EDA (Materia 3) para proyectar impacto esperado — por ejemplo, si el análisis muestra que cierto tipo de mascota tarda más en adoptarse, proponer una intervención (destacarla más en el home) y estimar el impacto esperado.

5. **Documento de métodos de análisis**:
   - Cualitativo: cómo se codificarán/agruparán las respuestas abiertas de la encuesta y las observaciones del test de usabilidad (codificación temática simple).
   - Cuantitativo: qué estadística descriptiva se usará sobre las métricas de usabilidad y sobre los datos de la encuesta (promedios, tasas, distribución), enlazando con las herramientas ya usadas en la Materia 3 (pandas/matplotlib).
