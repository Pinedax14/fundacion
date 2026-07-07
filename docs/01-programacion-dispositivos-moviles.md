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
| Interfaz responsiva | ✅ Existe | Media queries en `app/static/css/{home,layout,mascotas,perfil,donaciones_premium,solicitud_adopcion}.css`, meta viewport en `layout.html`/`layoutin.html`, Bootstrap 5.3.3 |
| Consumo de APIs | ❌ No existe | Todas las rutas devuelven HTML renderizado server-side. No hay ni un endpoint que devuelva JSON (ni `/filtrar_mascotas` en `app/rutas/mascotas.py`, que re-renderiza HTML en vez de responder JSON) |
| Gráficos interactivos | ❌ No existe | Cero uso de Chart.js, Plotly, D3, Recharts o similar en todo el repo |
| Optimización de rendimiento | ❌ No existe | Sin caché, sin bundling/minificación de assets, sin lazy-loading explícito |
| Autenticación | 🟡 Parcial | Bcrypt para hash de contraseñas (`app/services/auth_service.py`), sesiones Flask, verificación de correo por código. Falta rate limiting (sin protección de fuerza bruta) |
| Encriptación | ❌ No existe | No hay cifrado de datos sensibles (solo hash de contraseñas, que no es "encriptación" de PII) |
| CSRF | 🟡 Código muerto | Existe `validar_csrf` en `app/utils/decoradores.py` pero **no se usa en ninguna ruta** |
| Wireframes en Figma | ❌ No existe | Sin archivos `.fig` ni carpeta de diseño |
| Código documentado | 🟡 Parcial | Estructura en capas clara (`rutas/services/models/validators`), pero sin docstrings consistentes ni README |
| Informe multi-dispositivo | ❌ No existe | Sin Selenium/Playwright, sin evidencia de pruebas en distintos navegadores/tamaños |
| MVP funcional | ✅ Existe (de facto) | La app funciona end-to-end: registro, adopción, donaciones, reportes, panel admin — pero no está documentado formalmente como "MVP" |
| Manual de usuario/instalación | ❌ No existe | — |

## 3. Plan de acción

1. **Definir el MVP formalmente** — redactar una lista corta de funcionalidades núcleo ya construidas (registro/login, catálogo de mascotas, solicitud de adopción, donaciones, reportes, panel admin) y marcarlas como "MVP v1" en un documento.

2. **Construir una capa de API JSON** — crear un blueprint nuevo (`app/rutas/api.py`) con endpoints como `GET /api/v1/mascotas`, `GET /api/v1/donaciones/resumen`, `GET /api/v1/reportes` que reutilicen los `services` ya existentes y respondan con `jsonify(...)` en vez de `render_template(...)`. Esto es lo mínimo para justificar "consumo de APIs".

3. **Agregar gráficos interactivos** — integrar **Chart.js** (más simple de justificar en un stack Flask+Jinja que D3/Recharts) en el panel de admin y/o home público, alimentado por los endpoints del punto 2. Ejemplos de gráficos: adopciones por mes, donaciones por mes, mascotas por especie/estado.

4. **Cerrar los huecos de seguridad**:
   - Activar CSRF real con `Flask-WTF` (el decorador actual está muerto).
   - Agregar `Flask-Limiter` al login para mitigar fuerza bruta.
   - Mover las credenciales hardcodeadas de `app/rutas/auth.py` (remitente/contraseña de correo) a variables de entorno (`.env` + `os.getenv`).
   - (Opcional, para "encriptación") cifrar con `cryptography`/Fernet algún campo sensible si el modelo lo tiene (ej. dirección, cédula), o documentar por qué no aplica.

5. **Wireframes en Figma (retroactivos)** — tomar capturas de las pantallas ya construidas (Home, Mascotas, Detalle de mascota, Donaciones, Adopción, Panel admin) y reconstruirlas como frames en un tablero de Figma. Aunque el diseño ya existe en código, la materia pide el artefacto de diseño como entregable independiente.

6. **Informe de pruebas en varios dispositivos** — usar la emulación de dispositivos de Chrome DevTools (o Edge) en al menos 3 breakpoints (móvil ~390px, tablet ~768px, desktop ~1440px) y probar en 2 navegadores reales (Chrome/Edge o Firefox). Documentar hallazgos en una tabla simple: dispositivo/navegador → qué se probó → resultado.

7. **Documentación técnica**:
   - Manual de instalación: pasos para clonar, crear venv, instalar `requirements.txt`, configurar `.env`, correr migraciones/`run.py`.
   - Manual de usuario: flujos principales (adoptar, donar, reportar, voluntariado) con capturas de pantalla.

8. **Documentar el código** — agregar docstrings a los métodos públicos de `app/services/*.py` y a las rutas principales; considerar un `README.md` en la raíz que hoy no existe.
