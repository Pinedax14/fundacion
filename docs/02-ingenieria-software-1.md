# Ingeniería de Software I

Aplicado sobre: **Fundación Almas con Cola** (Flask + PostgreSQL/Neon).

## 1. Requisitos de la materia

### Temas que debe cubrir el proyecto
- [ ] Requisitos funcionales y no funcionales
- [ ] Elección del ciclo de vida (ágil)
- [ ] Planificación y cronograma
- [ ] Diseño de arquitectura
- [ ] Aseguramiento de calidad

### Entregables
- [ ] Documento de requisitos
- [ ] Plan de desarrollo
- [ ] Cronograma con tareas
- [ ] Documento de arquitectura
- [ ] Informe de pruebas de calidad

## 2. Estado actual del proyecto

| Requisito | Estado | Evidencia |
|---|---|---|
| Requisitos funcionales/no funcionales (documentados) | ❌ No existe | Los requisitos existen *implícitos* en el código (rutas, modelos) pero no hay ningún documento formal |
| Ciclo de vida ágil (elegido y justificado) | ❌ No existe | Sin backlog, sin sprints, sin user stories documentadas |
| Planificación y cronograma | ❌ No existe | Ningún `.xlsx`/Gantt/plan de fechas en el repo |
| Arquitectura (documentada) | 🟡 Existe en código, no documentada | Patrón factory (`app/__init__.py`), capas `rutas → services → models → validators/utils`, esquema en `sql/fundacion.sql` (dump crudo, no diagrama) |
| Aseguramiento de calidad | 🟡 Parcial | Hay tests (`tests/test_auth_service.py`, `test_fecha_nacimiento.py`, `test_exhaustivo.py`) pero sin informe formal de resultados ni cobertura, sin `pytest.ini` |
| README / documentación general | ❌ No existe | No hay `README.md` en la raíz del repo |

## 3. Plan de acción

1. **Documento de requisitos**:
   - Funcionales: extraerlos de las funcionalidades ya construidas (registro/login, catálogo y filtro de mascotas, solicitud de adopción, donaciones, reporte de maltrato con evidencia fotográfica, voluntariado, panel admin con auditoría).
   - No funcionales: definir explícitamente rendimiento (tiempos de carga esperados), seguridad (los hallazgos de la materia de Móviles), usabilidad, disponibilidad (uso de Neon/Postgres en la nube), y mantenibilidad (estructura en capas).

2. **Elegir y justificar el ciclo de vida ágil** — dado que el proyecto ya tiene funcionalidad construida de forma incremental (evidenciado en los commits: rediseño visual, refactor de BD a nodos, arreglos de formularios), documentar esto como **Scrum simplificado o Kanban** con entregas incrementales, justificando por tamaño de equipo y necesidad de mostrar avances por materia cada corte.

3. **Cronograma con tareas** — construir una tabla/Gantt simple que:
   - Documente retroactivamente lo ya hecho (fases pasadas: BD, auth, mascotas, donaciones, rediseño visual).
   - Planifique lo pendiente: API JSON + gráficos (Móviles), notebook EDA (Ciencia de Datos), investigación de usuarios (Metodología), y los propios entregables de esta materia.
   - Herramienta sugerida: tabla en Markdown o Excel con columnas *Tarea | Responsable | Inicio | Fin | Estado*.

4. **Documento de arquitectura**:
   - Diagrama de capas (rutas → services → models → BD), representable en Mermaid dentro de un `.md` para que quede versionado con el código.
   - Diagrama entidad-relación derivado de `sql/fundacion.sql` (tablas: `usuarios`, `mascotas`, `solicitudes_adopcion`, `reportes`, `voluntariados`, `donaciones`, `donaciones_items`, `verificaciones_email`, `audit_logs`) — se puede generar con dbdiagram.io o Mermaid `erDiagram`.
   - Justificar decisiones clave: por qué Flask monolítico, por qué Postgres/Neon, por qué SQLAlchemy.

5. **Informe de pruebas de calidad**:
   - Correr la suite de pytest existente (`tests/`) y registrar resultados (cuántos pasan, cuántos fallan, qué cubren).
   - Ampliar cobertura donde haya huecos evidentes (ej. rutas de donaciones/reportes no tienen test).
   - Redactar un informe corto: alcance de las pruebas, resultados, defectos encontrados y corregidos (por ejemplo, los hallazgos de seguridad de la materia de Móviles pueden documentarse aquí como "defectos encontrados en QA").

6. **README del proyecto** — aunque no lo pide explícitamente la rúbrica, sirve como base común para los manuales de instalación/usuario de la materia de Móviles y como carta de presentación del repo.
