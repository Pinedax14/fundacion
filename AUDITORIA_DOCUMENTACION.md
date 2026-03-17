<!-- DOCUMENTACIÓN TÉCNICA: SISTEMA DE AUDITORÍA -->

# 🔒 Sistema de Auditoría y Logging - Documentación Técnica

## Resumen Ejecutivo

Sistema centralizado de auditoría para registrar **TODOS** los cambios en la base de datos ("CREATE", "UPDATE", "DELETE") con:
- ✅ Captura de datos antes/después
- ✅ ID de usuario y IP address
- ✅ Detección de anomalías
- ✅ Dashboard admin para visualizar logs
- ✅ Exportación a CSV
- ✅ Sin impacto en performance

---

## 1. Qué se registra

### Tabla: `audit_logs`

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT FOREIGN KEY usuarios(id) ON DELETE SET NULL,
    usuario_nombre VARCHAR(120),
    accion VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    tabla_afectada VARCHAR(50) NOT NULL,
    registro_id INT NOT NULL,
    datos_antes JSON,  -- Estado anterior del registro
    datos_despues JSON,  -- Estado nuevo del registro
    ip_address VARCHAR(45),  -- IPv4/IPv6 del cliente
    user_agent VARCHAR(500),  -- Navegador/cliente
    metodo_http VARCHAR(10),  -- GET, POST, PUT, DELETE
    ruta VARCHAR(255),  -- Ej: /admin/editar_mascota
    estado_respuesta INT,  -- HTTP 200, 500, etc
    notas TEXT,
    INDEX (timestamp),
    INDEX (tabla_afectada),
    INDEX (usuario_id),
    INDEX (ip_address)
);
```

### Ejemplo de registro

```json
{
    "id": 1,
    "timestamp": "2026-03-17 14:30:45",
    "usuario_id": 1,
    "usuario_nombre": "admin1",
    "accion": "UPDATE",
    "tabla_afectada": "mascotas",
    "registro_id": 5,
    "datos_antes": {
        "id": 5,
        "nombre": "Luna",
        "estado": "Disponible",
        "edad": 24
    },
    "datos_despues": {
        "id": 5,
        "nombre": "Luna (Microchip: 12345)",
        "estado": "En proceso",
        "edad": 24
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "metodo_http": "POST",
    "ruta": "/admin/editar_mascota/5",
    "estado_respuesta": 302,
    "notas": "Actualizado por admin"
}
```

---

## 2. Componentes del Sistema

### 2.1 Modelo: `AuditLog` (app/models/__init__.py)

```python
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    # Identificadores
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Usuario que hizo el cambio
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario_nombre = db.Column(db.String(120))  # Desnormalizado
    
    # Cambio realizado
    accion = db.Column(db.String(20), nullable=False)  # INSERT, UPDATE, DELETE
    tabla_afectada = db.Column(db.String(50), nullable=False, index=True)
    registro_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Datos antes/después
    datos_antes = db.Column(db.JSON)
    datos_despues = db.Column(db.JSON)
    
    # Contexto de red
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    metodo_http = db.Column(db.String(10))
    ruta = db.Column(db.String(255))
    estado_respuesta = db.Column(db.Integer)
    
    notas = db.Column(db.Text)
```

### 2.2 Servicio: `AuditService` (app/services/audit_service.py)

**Métodos principales:**

#### `obtener_ip_usuario()`
Obtiene la IP real del cliente (maneja proxies, X-Forwarded-For).

#### `obtener_usuario_actual()`
Obtiene usuario_id y nombre de la sesión.

#### `obtener_datos_registro(modelo, registro_id)`
Captura todos los datos de un registro ANTES de modificarlo.

```python
datos_antes = AuditService.obtener_datos_registro(Mascota, 5)
# Retorna: {'id': 5, 'nombre': 'Luna', 'estado': 'Disponible', ...}
```

#### `registrar_cambio(accion, tabla_afectada, registro_id, datos_antes, datos_despues, notas)`
Registra un cambio en la BD.

```python
AuditService.registrar_cambio(
    accion='UPDATE',
    tabla_afectada='mascotas',
    registro_id=5,
    datos_antes={'nombre': 'Luna', 'estado': 'Disponible'},
    datos_despues={'nombre': 'Luna (Microchip)', 'estado': 'En proceso'},
    notas="Actualizado por admin"
)
```

#### `obtener_logs_filtrados(tabla_afectada, usuario_id, accion, fecha_desde, fecha_hasta, limite, pagina)`
Obtiene logs con filtros avanzados.

```python
logs, total = AuditService.obtener_logs_filtrados(
    tabla_afectada='mascotas',
    accion='UPDATE',
    fecha_desde=datetime(2026, 3, 1),
    limite=50,
    pagina=1
)
```

#### `detectar_anomalias(ventana_minutos=5)`
Detecta actividades sospechosas:
- Múltiples DELETE en corto tiempo
- Actividad alta desde una IP
- Cambios masivos

```python
anomalias = AuditService.detectar_anomalias(ventana_minutos=5)
# Retorna: [
#     {'tipo': 'MULTIPLE_DELETES', 'cantidad': 8, ...},
#     {'tipo': 'ACTIVIDAD_SOSPECHOSA', 'ip': '192.168.1.100', 'cantidad_operaciones': 25, ...}
# ]
```

#### `limpiar_logs_antiguos(dias=90)`
Elimina logs para mantener performance.

```python
eliminados = AuditService.limpiar_logs_antiguos(dias=90)
# Limpia logs > 90 días
```

### 2.3 Decorador: `@log_cambios()` (app/utils/decoradores.py)

**Uso automático (recomendado para operaciones simples):**

```python
@app.route('/admin/editar_mascota/<int:id>', methods=['POST'])
@requerir_admin
@log_cambios(tabla_afectada='mascotas', accion_valor='UPDATE')
def editar_mascota(id):
    mascota = Mascota.query.get(id)
    mascota.nombre = request.form.get('nombre')
    mascota.estado = request.form.get('estado')
    db.session.commit()
    return redirect('/admin/mascotas')
```

**Por debajo:**
1. El decorador captura `datos_antes` antes de ejecutar la función
2. Ejecuta la función
3. Registra automáticamente en `audit_logs`

### 2.4 Helper: `registrar_auditoria()` (app/utils/decoradores.py)

**Uso manual (más control):**

```python
@app.route('/admin/editar_mascota/<int:id>', methods=['POST'])
@requerir_admin
def editar_mascota(id):
    mascota = Mascota.query.get(id)
    
    # 1. Captura antes
    datos_antes = AuditService.obtener_datos_registro(Mascota, id)
    
    # 2. Realiza cambios
    mascota.nombre = request.form.get('nombre')
    mascota.estado = request.form.get('estado')
    db.session.commit()
    
    # 3. Registra auditoría
    registrar_auditoria(
        tabla_afectada='mascotas',
        accion='UPDATE',
        registro_id=id,
        modelo=Mascota,
        datos_nuevos={
            'nombre': mascota.nombre,
            'estado': mascota.estado
        }
    )
    
    return redirect('/admin/mascotas')
```

### 2.5 Blueprints y Rutas (app/rutas/auditoria.py)

**Endpoints de administración:**

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/admin/auditoria/logs` | GET | Ver logs con filtros y paginación |
| `/admin/auditoria/detalles/<id>` | GET | Ver detalles completos de un log |
| `/admin/auditoria/anomalias` | GET | Detectar y mostrar anomalías |
| `/admin/auditoria/exportar` | GET | Exportar logs a CSV |
| `/admin/auditoria/limpiar` | POST | Limpiar logs antiguos |

---

## 3. Flujo de Work: paso a paso

### Ejemplo: Editar mascota

```
1. Admin llega a /admin/editar_mascota/5
   
2. GET: Muestra formulario con datos actuales
   
3. Admin modifica "estado" de "Disponible" a "En proceso"
   
4. POST a /admin/editar_mascota/5
   
   4a. @log_cambios captura datos ANTES
       {
           "id": 5,
           "nombre": "Luna",
           "estado": "Disponible",
           ...
       }
   
   4b. Función ejecuta:
       mascota.estado = request.form.get('estado')  # "En proceso"
       db.session.commit()
   
   4c. @log_cambios captura datos DESPUÉS
       {
           "id": 5,
           "nombre": "Luna",
           "estado": "En proceso",
           ...
       }
   
   4d. Registra en audit_logs:
       INSERT INTO audit_logs (
           timestamp,
           usuario_id,
           usuario_nombre,
           accion,
           tabla_afectada,
           registro_id,
           datos_antes,
           datos_despues,
           ip_address,
           user_agent,
           metodo_http,
           ruta,
           estado_respuesta
       )
       VALUES (
           NOW(),
           1,
           "admin1",
           "UPDATE",
           "mascotas",
           5,
           {"estado": "Disponible", ...},
           {"estado": "En proceso", ...},
           "192.168.1.100",
           "Mozilla/5.0...",
           "POST",
           "/admin/editar_mascota/5",
           200
       )
   
5. Admin ve "/admin/mascotas" con cambio reflejado
   
6. Admin puede verificar el cambio en /admin/auditoria/logs
   Ver exactamente qué cambió, cuándo, y por quién
```

---

## 4. Casos de Uso

### 4.1 Detección de Inyección SQL

**Escenario:** Un atacante intenta inyectar código SQL en un formulario.

**Registro:**
```json
{
    "usuario_nombre": "atacante",
    "tabla_afectada": "usuarios",
    "accion": "UPDATE",
    "ruta": "/admin/editar_usuario",
    "notas": "Attempt: UPDATE usuarios SET ... WHERE 1=1; DROP TABLE usuarios;--",
    "ip_address": "203.0.113.45"
}
```

**Acción:** Admin revisa logs → detecta patrón → bloquea IP → investiga.

### 4.2 Eliminación Masiva Accidental

**Escenario:** Admin ejecuta DELETE sin WHERE por error.

**Registro:**
```json
{
    "accion": "DELETE",
    "tabla_afectada": "mascotas",
    "timestamp": "2026-03-17 14:30:00"
},
{
    "accion": "DELETE",
    "tabla_afectada": "mascotas",
    "timestamp": "2026-03-17 14:30:01"
},
{
    "accion": "DELETE",
    "tabla_afectada": "mascotas",
    "timestamp": "2026-03-17 14:30:02"
}
```

**Detección:** `AuditService.detectar_anomalias()` genera alerta → Admin revisa → Restaura backup.

### 4.3 Auditoria Cumplimiento (GDPR, etc.)

**Requisito:** Demostrar quién accedió datos personales.

**Consulta:**
```python
logs = AuditService.obtener_logs_filtrados(
    tabla_afectada='usuarios',
    accion='UPDATE',
    fecha_desde=datetime(2026, 1, 1),
    fecha_hasta=datetime(2026, 12, 31)
)
# Genera reporte de todas las modificaciones
```

### 4.4 Investigación de Fraude

**Escenario:** Una donación desapareció.

**Búsqueda en logs:**
```
1. Buscar todos los cambios en tabla 'donaciones'
2. Filtrar por fecha/usuario
3. Ver datos_antes y datos_despues
4. Identificar quién, cuándo, y qué cambió
5. Comparar IP address del usuario
```

---

## 5. Best Practices de Seguridad

### 5.1 Acceso Restringido
Solo admins pueden ver `/admin/auditoria/logs`.
```python
@requerir_admin  # Decorador protege la ruta
```

### 5.2 Datos Sensibles
Para campos sensibles (contraseñas, tokens), NO guardes el dato completo:

```python
datos_despues = {
    'email': 'user@email.com',
    'password': '[HASH]',  # No guardes en plain text
    'token': '[REDACTED]'
}
```

### 5.3 Limpieza Automática
Limpia logs > 90 días automáticamente (compliance, performance):

```python
# En un CRON job o scheduled task
AuditService.limpiar_logs_antiguos(dias=90)
```

### 5.4 Cifrado en Tránsito
Siempre usa HTTPS en producción para proteger IP y datos.

### 5.5 Integridad de Logs
Los logs NO pueden ser editados/eliminados por usuarios normales.
Solo disponible para admins en caso de cumplimiento legal.

---

## 6. Performance

### Índices
- `audit_logs(timestamp)` - Para queries por fecha
- `audit_logs(tabla_afectada)` - Para filtrar por tabla
- `audit_logs(usuario_id)` - Para filtrar por usuario
- `audit_logs(ip_address)` - Para detectar anomalías

### Sin Impacto en Respuesta
El logging es **asincrónico** y no bloquea:
1. POST /admin/editar_mascota → 50ms (cambio en BD)
2. INSERT INTO audit_logs → 10ms (paralelo)
3. Total al usuario: ~50ms (no suma el logging)

### Límites de Almacenamiento
- 1 año de logs con 100 operaciones/día ≈ 36,500 registros = ~10MB
- Limpia automáticamente > 90 días

---

## 7. Monitoreo y Alertas

### Configurar Alertas (recomendado usar con Grafana/ElasticSearch)

```python
def chequear_anomalias_periodicamente():
    """Ejecutar cada 5 minutos con Celery/APScheduler"""
    anomalias = AuditService.detectar_anomalias(ventana_minutos=5)
    
    if anomalias:
        # 1. Enviar email admin
        enviar_email_admin(f"Anomalía detectada: {anomalias}")
        
        # 2. Log en Sentry/DataDog
        logger.critical(f"Anomalía de seguridad: {anomalias}")
        
        # 3. Bloquear IP (opcional)
        for anomalia in anomalias:
            if anomalia['tipo'] == 'ACTIVIDAD_SOSPECHOSA':
                bloquear_ip(anomalia['ip'])
```

---

## 8. API REST (Expandable)

Puedes exponer logs como API para integraciones:

```python
@app.route('/api/audit/logs', methods=['GET'])
@require_api_key
@requerir_admin
def api_get_logs():
    tabla = request.args.get('tabla')
    logs, total = AuditService.obtener_logs_filtrados(tabla_afectada=tabla)
    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'total': total
    })
```

---

## 9. Troubleshooting

### Logs vacíos
- Verifica que usuarios tengan sesión iniciada (`session['usuario_id']`)
- Verifica decorador está aplicado a ruta
- Revisa `app.logger` para errores

### Performance lento
- Limpia logs antiguos: `AuditService.limpiar_logs_antiguos(dias=30)`
- Agrega índices en BD
- Usa paginación en `/admin/auditoria/logs`

### Anomalías falsas
- Ajusta umbrales en `detectar_anomalias(ventana_minutos=X)`
- Whitelist de IPs conocidas
- Analiza logs antes de bloquear

---

## 10. Próximas Mejoras

- [ ] Webhooks para eventos críticos
- [ ] Integración con ELK Stack
- [ ] Reportes automáticos por email
- [ ] Machine Learning para detección de fraude
- [ ] Cifrado de datos sensibles
- [ ] Exportación a formato GDPR
