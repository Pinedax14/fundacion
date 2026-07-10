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
| Aseguramiento de calidad | 🟡 Parcial | Hay tests (`tests/test_auth_service.py`, `tests/test_api.py`, `test_fecha_nacimiento.py`, `test_exhaustivo.py`) pero sin informe formal de resultados ni cobertura, sin `pytest.ini`. Se encontraron y corrigieron defectos reales durante el trabajo de API: 4 modelos ORM desincronizados con el esquema real de la BD, credenciales hardcodeadas, y un `.env` con secretos commiteado en git desde el primer commit — buen material real para el "informe de pruebas de calidad" (punto 5 del plan) |
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
   - Correr la suite de pytest existente (`tests/`) y registrar resultados (cuántos pasan, cuántos fallan, qué cubren). Estado actual: 20/20 tests pasan (`tests/test_auth_service.py` + `tests/test_api.py`, nuevo).
   - Ampliar cobertura donde haya huecos evidentes (ej. rutas de donaciones/reportes no tienen test más allá de la API).
   - Redactar un informe corto con los defectos reales encontrados y corregidos durante este trabajo, que ya están documentados y son reales (no hay que inventarlos):
     - 4 modelos ORM (`Mascota`, `SolicitudAdopcion`, `Reporte`, `SolicitudVoluntariado`) declaraban columnas que no existen en la BD de producción, y `Item_Donacion` tenía el esquema completo desincronizado — nadie lo notó porque ninguna ruta los consultaba vía ORM antes de esta sesión.
     - Contraseña de Gmail hardcodeada en `app/rutas/auth.py` (movida a variables de entorno).
     - `.env` con la contraseña real de la BD Neon commiteado en git desde el primer commit y expuesto en GitHub (sacado del tracking, contraseña rotada en Neon).
     - Falta de rate limiting en `/login` (corregido con Flask-Limiter).

6. **README del proyecto** — aunque no lo pide explícitamente la rúbrica, sirve como base común para los manuales de instalación/usuario de la materia de Móviles y como carta de presentación del repo.
