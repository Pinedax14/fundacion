# Programación para Dispositivos Móviles

Aplicado sobre: **Fundación Almas con Cola** (Flask + PostgreSQL/Neon).

## 1. Requisitos de la materia

### Temas que debe cubrir el proyecto
- [ ] Interfaz responsiva (UX/UI)
- [ ] Consumo de APIs
- [ ] Gráficos interactivos (tipo MPAndroidChart, Charts, Recharts o D3)
- [ ] Optimización de rendimiento
- [ ] Seguridad (autenticación, encriptación)

### Entregables
- [ ] Wireframes / mockups en Figma
- [ ] Código fuente documentado
- [ ] Informe de pruebas en varios dispositivos
- [ ] MVP funcional
- [ ] Documentación técnica (manual de usuario + manual de instalación)

## 2. Estado actual del proyecto

| Requisito | Estado | Evidencia |
|---|---|---|
| Interfaz responsiva | ✅ Existe | Media queries en `app/static/css/{home,layout,mascotas,perfil,donaciones_premium,solicitud_adopcion,reporte}.css`, meta viewport en `layout.html`/`layoutin.html`, Bootstrap 5.3.3 |
| Consumo de APIs | ✅ Existe | Blueprint `app/rutas/api.py` (`/api/v1/mascotas`, `/api/v1/donaciones/resumen`, `/api/v1/adopciones/resumen`, `/api/v1/reportes`), responde `jsonify(...)`, cubierto por `tests/test_api.py` |
| Gráficos interactivos | ✅ Existe | Chart.js en el panel admin (`admin/admin_panel.html`, tab "Estadísticas"): donaciones por mes, adopciones por mes, mascotas por especie/estado, alimentado por la API de arriba |
| Optimización de rendimiento | ❌ No existe | Sin caché, sin bundling/minificación de assets, sin lazy-loading explícito |
| Autenticación | 🟡 Parcial | Bcrypt para hash de contraseñas (`app/services/auth_service.py`), sesiones Flask, verificación de correo por código. **Rate limiting agregado** (`Flask-Limiter`, 5 intentos/min en `/login`, `app/extensions.py`) |
| Encriptación | ❌ No existe | No hay cifrado de datos sensibles (solo hash de contraseñas, que no es "encriptación" de PII) |
| Credenciales hardcodeadas | ✅ Corregido | `REMITENTE`/`CONTRASENA_APP` de `app/rutas/auth.py` ahora vienen de `app.config` (`.env`/`MAIL_USERNAME`/`MAIL_PASSWORD`) |
| CSRF | 🟡 Código muerto (aplazado) | Sigue existiendo `validar_csrf` sin usar en `app/utils/decoradores.py`. Activar `Flask-WTF` real requiere tocar **todos** los formularios existentes — aplazado a propósito a una sesión dedicada para no romper submits en producción |
| Wireframes en Figma | ❌ No existe | Sin archivos `.fig` ni carpeta de diseño |
| Código documentado | 🟡 Parcial | Estructura en capas clara (`rutas/services/models/validators`), pero sin docstrings consistentes ni README |
| Informe multi-dispositivo | ❌ No existe | Sin Selenium/Playwright, sin evidencia de pruebas en distintos navegadores/tamaños |
| MVP funcional | ✅ Existe (de facto) | La app funciona end-to-end: registro, adopción, donaciones, reportes, panel admin — pero no está documentado formalmente como "MVP" |
| Manual de usuario/instalación | ❌ No existe | — |

## 3. Plan de acción

1. **Definir el MVP formalmente** — redactar una lista corta de funcionalidades núcleo ya construidas (registro/login, catálogo de mascotas, solicitud de adopción, donaciones, reportes, panel admin) y marcarlas como "MVP v1" en un documento. *(pendiente)*

2. ~~**Construir una capa de API JSON**~~ ✅ **Hecho** — `app/rutas/api.py`: `GET /api/v1/mascotas` (público), `GET /api/v1/donaciones/resumen`, `GET /api/v1/adopciones/resumen`, `GET /api/v1/reportes` (los 3 últimos protegidos con sesión de admin), reutilizando `AdminDataStructureService` y los modelos ORM. Tests en `tests/test_api.py`.

3. ~~**Agregar gráficos interactivos**~~ ✅ **Hecho** — Chart.js en `admin/admin_panel.html` (tab "Estadísticas"): 4 tarjetas KPI + gráficos de donaciones por mes, solicitudes de adopción por mes, mascotas por especie/estado, todo alimentado vía `fetch()` a la API del punto 2.

4. **Cerrar los huecos de seguridad**:
   - ✅ **Rate limiting**: `Flask-Limiter` en `/login` (5 intentos/min por IP), con handler 429 que redirige con mensaje flash (`app/__init__.py`).
   - ✅ **Credenciales a variables de entorno**: `app/rutas/auth.py` ya no tiene la contraseña de Gmail hardcodeada.
   - ⚠️ **Hallazgo de seguridad no planeado, ya corregido**: el `.env` con la contraseña real de la BD Neon estaba commiteado en git desde el primer commit (expuesto en GitHub). Se sacó del tracking (`git rm --cached .env` + `.gitignore`) y se rotó la contraseña en el dashboard de Neon.
   - 🔲 **CSRF real con Flask-WTF** — aplazado a propósito (ver tabla arriba). Requiere agregar `csrf_token` a cada formulario existente (registro, login, cambiar contraseña, editar perfil, adopción, reporte, donaciones, admin, etc.).
   - 🔲 (Opcional, para "encriptación") cifrar con `cryptography`/Fernet algún campo sensible (ej. dirección, cédula), o documentar por qué no aplica.

5. **Wireframes en Figma (retroactivos)** — tomar capturas de las pantallas ya construidas (Home, Mascotas, Detalle de mascota, Donaciones, Adopción, Reportar, Panel admin) y reconstruirlas como frames en un tablero de Figma. *(pendiente)*

6. **Informe de pruebas en varios dispositivos** — usar la emulación de dispositivos de Chrome DevTools (o Edge) en al menos 3 breakpoints (móvil ~390px, tablet ~768px, desktop ~1440px) y probar en 2 navegadores reales (Chrome/Edge o Firefox). *(pendiente)*

7. **Documentación técnica**:
   - Manual de instalación: pasos para clonar, crear venv, instalar `requirements.txt`, configurar `.env`, correr migraciones/`run.py`. *(pendiente)*
   - Manual de usuario: flujos principales (adoptar, donar, reportar, voluntariado) con capturas de pantalla. *(pendiente)*

8. **Documentar el código** — agregar docstrings a los métodos públicos de `app/services/*.py` y a las rutas principales; considerar un `README.md` en la raíz que hoy no existe. *(pendiente)*

## 4. Trabajo adicional realizado (fuera del plan original)

- **Rediseño completo de `/reporte`**: la página usaba un tema oscuro/glassmorphism sobrante de antes del rediseño visual general. Ahora sigue el mismo sistema de diseño que adopción/donaciones (`app/static/css/reporte.css`), con una zona de evidencia con arrastrar-y-soltar + vista previa, y una franja "Qué pasa con tu reporte" que explica el proceso post-envío.
- **Limpieza de emojis en toda la interfaz** (templates, JS, CSS) — reemplazados por Bootstrap Icons (`bi bi-*`), ya usados en el resto del sitio, para consistencia visual.
- **Bug de esquema corregido**: 4 modelos ORM (`Mascota`, `SolicitudAdopcion`, `Reporte`, `SolicitudVoluntariado`, `Item_Donacion`) declaraban columnas que no existen en la BD real de Neon (y viceversa). Nadie lo había notado porque ninguna ruta activa los consultaba vía ORM. Corregido y verificado con un diff automatizado modelo↔BD.
