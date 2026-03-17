# Arquitectura Refactorizada - Almas con Cola

## Estructura de Carpetas

```
fundacion/
├── app/
│   ├── __init__.py              ← Factory pattern para crear app
│   ├── logger.py                ← Configuración de logging
│   ├── models/                  ← Modelos de SQLAlchemy
│   │   └── __init__.py          ← Definición de modelos (Usuario, Mascota, etc)
│   ├── services/                ← Lógica de negocio (Nueva)
│   │   ├── __init__.py
│   │   └── auth_service.py      ← Servicios de autenticación
│   ├── validators/              ← Validación con Marshmallow (Nueva)
│   │   ├── __init__.py
│   │   └── schemas.py           ← Schemas de validación
│   ├── utils/                   ← Utilidades (Nueva)
│   │   ├── __init__.py
│   │   └── upload_manager.py    ← Gestión segura de uploads
│   ├── rutas/                   ← Rutas/Blueprints (Será refactorizado)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── mascotas.py
│   │   ├── admin.py
│   │   └── ...
│   ├── static/                  ← Archivos estáticos
│   │   ├── css/
│   │   ├── images/
│   │   └── uploads/
│   └── templates/               ← Plantillas Jinja2
│       ├── base/
│       ├── auth/
│       ├── mascotas/
│       └── ...
├── tests/                       ← Tests unitarios (Nueva)
│   ├── conftest.py
│   └── test_auth_service.py
├── config.py                    ← Configuración por ambiente (Nueva)
├── run.py                       ← Punto de entrada
├── .env.example                 ← Plantilla de variables (Nueva)
├── requirements.txt             ← Dependencias
└── README.md
```

## Patrones Utilizados

### 1. Factory Pattern (app/__init__.py)
```python
from app import create_app

# En run.py
app, db = create_app('development')
```

**Beneficios:**
- Crear instancias con diferentes configs
- Facilita testing
- Sigue estándares de Flask

### 2. Separación de Capas

```
Rutas (HTTP)
    ↓
Validadores (Marshmallow)
    ↓
Servicios (Lógica de negocio)
    ↓
Modelos (Datos)
    ↓
Base de Datos (SQLAlchemy ORM)
```

**Antes (acoplado):**
```python
@app.route('/registro', methods=['POST'])
def registro():
    # Validación aquí
    # Query a BD aquí
    # Email aquí
    # Lógica de negocio entrelazada
```

**Después (desacoplado):**
```python
@app.route('/registro', methods=['POST'])
def registro():
    # Solo validar y delegar
    valido, datos = validar_datos(UsuarioRegistroSchema(), request.form)
    if not valido:
        return error
    
    exito, usuario = auth_service.registrar_usuario(**datos)
    if not exito:
        return error
```

### 3. Configuración por Ambiente

```python
# config.py
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
```

Selecciona automáticamente según `FLASK_ENV` en `.env`

### 4. Logging Centralizado

```python
# app/logger.py
setup_logger(app)

# Uso en cualquier lado:
from flask import current_app
current_app.logger.info("Evento importante")
current_app.logger.error("Error crítico")
```

Logs se guardan en `logs/app.log` con rotación automática

### 5. ORM con SQLAlchemy

```python
# Antes (Query directa):
cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))

# Después (ORM):
Usuario.query.filter_by(email=email).first()
```

**Beneficios:**
- Seguridad contra SQL injection
- Type hints
- Migraciones fáciles
- Query más legibles

### 6. Validación Centralizada con Marshmallow

```python
# schemas.py
class UsuarioRegistroSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=3))
    email = fields.Email(required=True)
    password = fields.Str(required=True)

# Uso:
valido, datos = validar_datos(UsuarioRegistroSchema(), request.form)
```

### 7. Upload Manager Seguro

```python
# Valida extensión
# Valida MIME type
# Genera nombre único con secret
# Evita path traversal

nuevo_nombre = UploadManager.save_upload(
    file=request.files['photo'],
    folder='images/mascotas',
    prefix='mascota'
)
```

## Flujo Actual vs Refactorizado

### Flujo: Registro de Usuario

**ANTES (acoplado):**
```
POST /registro
    ↓
auth.py::RutasAuth.registro()
    - Validar manualmente (regex, etc)
    - Hash con bcrypt
    - INSERT en BD
    - Enviar email SMPT
    - Generar código
```

**DESPUÉS (desacoplado):**
```
POST /registro
    ↓
RutaAuth::registro()
    ↓
validar_datos(UsuarioRegistroSchema, request.form)
    ↓
AuthService.registrar_usuario()
    - Hash
    - Guardar
    - Generar código
    - Enviar email
    ↓
Response
```

## Migraciones a BD

Usando SQLAlchemy ORM en lugar de SQL directo:

```python
# Crear tablas:
python
>>> from app import create_app, db
>>> app, db = create_app()
>>> with app.app_context():
...     db.create_all()

# Agregar modelo nuevo: Solo edita app/models/__init__.py
# Las tablas se crean automáticamente en next app.app_context()
```

## Testing

```bash
# Correr tests
pytest tests/

# Con cobertura
pytest tests/ --cov=app

# Test específico
pytest tests/test_auth_service.py::TestAuthService::test_registrar_usuario_exitoso
```

## Siguiente Fase: Blueprints

Las rutas aún están en clases (legacy). Próximo paso es convertir a Blueprints:

```python
# Futuro blueprints/auth.py
from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/registro', methods=['POST'])
def registro():
    pass
```

Beneficios:
- Namespacing de rutas
- Versioning de API (/api/v1/mascotas)
- Lazy loading de componentes
- Mejor organización

## Variables de Entorno

Copia `.env.example` a `.env` y configura:

```bash
# .env
FLASK_ENV=development
SECRET_KEY=generado-con-secrets.token_hex(32)
DATABASE_URL=postgresql://...  # Preferida
# O MySQL local:
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=fundacion
```

## Instalación y Run

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear .env desde .env.example
cp .env.example .env

# 3. Configurar variables en .env

# 4. Correr:
python run.py

# 5. Visitar:
http://localhost:5000
```

## Logs

Los logs se guardan automáticamente en `logs/app.log`:

```
[2026-03-17 14:32:10,123] INFO: Logging configurado correctamente
[2026-03-17 14:32:10,234] INFO: Nivel de log: INFO
[2026-03-17 14:32:10,345] ERROR: Error al registrar usuario: Email inválido
```

## Conclusión

La arquitectura refactorizada es:

✅ **Modular**: Cada capa tiene responsabilidad clara
✅ **Testeable**: Lógica de negocio separada de HTTP
✅ **Segura**: Validación centralizada, ORM, uploads seguros
✅ **Escalable**: Factory pattern, logging, configuraciones
✅ **Mantenible**: Código limpio, documentado, fácil de cambiar

Próximos pasos:
1. Convertir rutas a Blueprints formales
2. Agregar más servicios (MascotaService, AdopcionService, etc)
3. Agregar cache
4. API REST
