"""
EJEMPLO DE INTEGRACIÓN - Sistema de Auditoría en Rutas Existentes
==================================================================

Este archivo muestra cómo integrar auditoría en tus rutas existentes.

OPCIÓN 1: Usando el decorador @log_cambios (automático)
OPCIÓN 2: Usando registrar_auditoria() (manual)
"""

from flask import request, session, redirect, flash, render_template
from app.models import db, Mascota, Usuario
from app.services.audit_service import AuditService
from app.utils.decoradores import log_cambios, registrar_auditoria, requerir_admin


# ============================================================================
# OPCIÓN 1: Usando decorador @log_cambios (automático, simple)
# ============================================================================

@app.route('/admin/editar_mascota/<int:id>', methods=['GET', 'POST'])
@requerir_admin
@log_cambios(tabla_afectada='mascotas', accion_valor='UPDATE')
def editar_mascota_v1(id):
    """
    Versión simple: El decorador registra automáticamente.
    
    Entrada:
        - form['nombre']
        - form['especie']
        - form['raza']
        - etc.
    
    El decorador automáticamente:
     1. Captura el registro_id (id)
     2. Obtiene datos antes del cambio
     3. Ejecuta la función
     4. Registra en audit_logs
    """
    if request.method == 'GET':
        mascota = Mascota.query.get(id)
        if not mascota:
            flash('Mascota no encontrada', 'error')
            return redirect('/admin/mascotas')
        return render_template('admin/editar_mascota.html', mascota=mascota)
    
    # POST: actualización
    mascota = Mascota.query.get(id)
    if not mascota:
        flash('Mascota no encontrada', 'error')
        return redirect('/admin/mascotas')
    
    # Realiza cambios
    mascota.nombre = request.form.get('nombre')
    mascota.especie = request.form.get('especie')
    mascota.raza = request.form.get('raza')
    mascota.edad = request.form.get('edad', type=int)
    mascota.sexo = request.form.get('sexo')
    mascota.descripcion = request.form.get('descripcion')
    mascota.estado = request.form.get('estado')
    
    db.session.commit()
    
    flash('Mascota actualizada correctamente', 'success')
    return redirect('/admin/mascotas')


# ============================================================================
# OPCIÓN 2: Usando registrar_auditoria() (manual, más control)
# ============================================================================

@app.route('/admin/editar_mascota_manual/<int:id>', methods=['GET', 'POST'])
@requerir_admin
def editar_mascota_v2(id):
    """
    Versión con control manual: Tú decides exactamente qué se registra.
    
    Ventajas:
     - Control total de qué se registra
     - Puedes capturar datos personalizados
     - Más flexible para casos complejos
    """
    if request.method == 'GET':
        mascota = Mascota.query.get(id)
        if not mascota:
            flash('Mascota no encontrada', 'error')
            return redirect('/admin/mascotas')
        return render_template('admin/editar_mascota.html', mascota=mascota)
    
    # POST: actualización
    mascota = Mascota.query.get(id)
    if not mascota:
        flash('Mascota no encontrada', 'error')
        return redirect('/admin/mascotas')
    
    # *** 1. CAPTURA DATOS ANTES ***
    datos_antes = AuditService.obtener_datos_registro(Mascota, id)
    
    # *** 2. REALIZA CAMBIOS ***
    mascota.nombre = request.form.get('nombre')
    mascota.especie = request.form.get('especie')
    mascota.raza = request.form.get('raza')
    mascota.edad = request.form.get('edad', type=int)
    mascota.sexo = request.form.get('sexo')
    mascota.descripcion = request.form.get('descripcion')
    mascota.estado = request.form.get('estado')
    
    db.session.commit()
    
    # *** 3. REGISTRA EN AUDITORÍA ***
    AuditService.registrar_cambio(
        accion='UPDATE',
        tabla_afectada='mascotas',
        registro_id=id,
        datos_antes=datos_antes,
        datos_despues={
            'nombre': mascota.nombre,
            'especie': mascota.especie,
            'raza': mascota.raza,
            'edad': mascota.edad,
            'sexo': mascota.sexo,
            'descripcion': mascota.descripcion,
            'estado': mascota.estado
        },
        notas=f"Actualizado por admin {session.get('usuario_nombre')}"
    )
    
    flash('Mascota actualizada correctamente', 'success')
    return redirect('/admin/mascotas')


# ============================================================================
# OPCIÓN 3: Inserción de nuevos registros
# ============================================================================

@app.route('/admin/nueva_mascota', methods=['GET', 'POST'])
@requerir_admin
def nueva_mascota():
    """
    Crear mascota con auditoría de INSERT.
    """
    if request.method == 'GET':
        return render_template('admin/nueva_mascota.html')
    
    # POST: crear
    mascota = Mascota(
        nombre=request.form.get('nombre'),
        especie=request.form.get('especie'),
        raza=request.form.get('raza'),
        edad=request.form.get('edad', type=int),
        sexo=request.form.get('sexo'),
        descripcion=request.form.get('descripcion'),
        estado='Disponible'
    )
    
    db.session.add(mascota)
    db.session.commit()
    
    # Registra el INSERT
    AuditService.registrar_cambio(
        accion='INSERT',
        tabla_afectada='mascotas',
        registro_id=mascota.id,
        datos_antes=None,  # Para INSERT no hay datos antes
        datos_despues={
            'id': mascota.id,
            'nombre': mascota.nombre,
            'especie': mascota.especie,
            'raza': mascota.raza,
            'edad': mascota.edad,
            'sexo': mascota.sexo,
            'descripcion': mascota.descripcion,
            'estado': mascota.estado
        },
        notas=f"Mascota ingresada por {session.get('usuario_nombre')}"
    )
    
    flash('Mascota creada correctamente', 'success')
    return redirect('/admin/mascotas')


# ============================================================================
# OPCIÓN 4: Eliminar registro (DELETE)
# ============================================================================

@app.route('/admin/eliminar_mascota/<int:id>', methods=['POST'])
@requerir_admin
def eliminar_mascota(id):
    """
    Eliminar mascota con auditoría de DELETE.
    """
    mascota = Mascota.query.get(id)
    if not mascota:
        flash('Mascota no encontrada', 'error')
        return redirect('/admin/mascotas')
    
    # Captura datos antes de eliminar
    datos_antes = AuditService.obtener_datos_registro(Mascota, id)
    
    # Elimina
    db.session.delete(mascota)
    db.session.commit()
    
    # Registra el DELETE
    AuditService.registrar_cambio(
        accion='DELETE',
        tabla_afectada='mascotas',
        registro_id=id,
        datos_antes=datos_antes,
        datos_despues=None,  # Para DELETE no hay datos después
        notas=f"Mascota {mascota.nombre} eliminada por {session.get('usuario_nombre')}"
    )
    
    flash('Mascota eliminada correctamente', 'success')
    return redirect('/admin/mascotas')


# ============================================================================
# OPCIÓN 5: Registrar acciones complejas con múltiples cambios
# ============================================================================

@app.route('/admin/procesar_solicitud/<int:solicitud_id>', methods=['POST'])
@requerir_admin
def procesar_solicitud(solicitud_id):
    """
    Procesar una solicitud de adopción (UPDATE a múltiples tablas).
    Demuestra auditoría de múltiples cambios en una acción.
    """
    from app.models import SolicitudAdopcion
    
    accion = request.form.get('accion')  # 'aprobar' o 'rechazar'
    
    solicitud = SolicitudAdopcion.query.get(solicitud_id)
    if not solicitud:
        flash('Solicitud no encontrada', 'error')
        return redirect('/admin')
    
    mascota = solicitud.mascota
    
    # Captura datos antes
    datos_solicitud_antes = AuditService.obtener_datos_registro(SolicitudAdopcion, solicitud_id)
    datos_mascota_antes = AuditService.obtener_datos_registro(Mascota, mascota.id)
    
    # Realiza cambios
    if accion == 'aprobar':
        solicitud.estado = 'aprobada'
        mascota.estado = 'Adoptado'
        mensaje = "Solicitud aprobada"
    else:
        solicitud.estado = 'rechazada'
        mensaje = "Solicitud rechazada"
    
    db.session.commit()
    
    # Registra ambos cambios
    AuditService.registrar_cambio(
        accion='UPDATE',
        tabla_afectada='solicitudes_adopcion',
        registro_id=solicitud_id,
        datos_antes=datos_solicitud_antes,
        datos_despues=AuditService.obtener_datos_registro(SolicitudAdopcion, solicitud_id),
        notas=mensaje
    )
    
    if accion == 'aprobar':
        AuditService.registrar_cambio(
            accion='UPDATE',
            tabla_afectada='mascotas',
            registro_id=mascota.id,
            datos_antes=datos_mascota_antes,
            datos_despues=AuditService.obtener_datos_registro(Mascota, mascota.id),
            notas=f"Estado cambió a Adoptado por {mensaje}"
        )
    
    flash(f"{mensaje} correctamente", 'success')
    return redirect('/admin/solicitudes')


# ============================================================================
# VISIONAR LOGS DE AUDITORÍA
# ============================================================================

# Las rutas ya están creadas en app/rutas/auditoria.py:
# - GET /admin/auditoria/logs       -> Ver logs con filtros
# - GET /admin/auditoria/detalles/<id> -> Ver detalles de un log
# - GET /admin/auditoria/anomalias  -> Detectar anomalías
# - GET /admin/auditoria/exportar   -> Exportar logs a CSV
# - POST /admin/auditoria/limpiar   -> Limpiar logs antiguos


# ============================================================================
# BEST PRACTICES
# ============================================================================

"""
1. USO DE DECORADOR vs MANUAL:
   - Usa @log_cambios para operaciones simples
   - Usa registrar_auditoria() para lógica compleja o múltiples cambios

2. INFORMACIÓN A REGISTRAR:
   - Siempre incluye: usuario_id, ip_address, timestamp
   - Para datos sensibles: cifra o limpia antes de guardar
   - Incluye notas útiles para investigación

3. PERFORMANCE:
   - Los logs son asíncronos y no bloquean la respuesta
   - Limpia regularmente logs antiguos (>90 días)
   - Usa índices en timestamp, usuario_id, tabla_afectada

4. SEGURIDAD:
   - Solo admins pueden ver logs (/admin/auditoria/logs)
   - Los logs NO pueden ser editados/eliminados por usuarios
   - Encripta datos sensibles en tránsito

5. DETECCIÓN DE FRAUDES:
   - Usa AuditService.detectar_anomalias() periódicamente
   - Alerta si múltiples DELETE en poco tiempo
   - Bloquea IPs con actividad sospechosa

6. CAMPOS ÚTILES:
   - datos_antes / datos_despues: Comparar cambios
   - ip_address: Detectar acceso no autorizado
   - user_agent: Detectar bots o automatización
   - estado_respuesta: Detectar errores o ataques

7. INTEGRACIONES AVANZADAS:
   - Exportar logs a ELK/Grafana para análisis
   - Configurar alertas en tiempo real
   - Crear dashboards de actividad
   - Generar reportes de cumplimiento (GDPR, etc.)
"""
