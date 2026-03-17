"""
Decoradores para la aplicación, incluyendo logging de auditoría
"""

from functools import wraps
from flask import request, session, jsonify, g, current_app
from app.services.audit_service import AuditService
from app.models import db
import json


def log_cambios(
    tabla_afectada=None,
    accion_valor=None,
    capturar_antes=True,
    capturar_despues=True
):
    """
    Decorador para registrar cambios en auditoría.
    
    Uso:
        @app.route('/admin/editar_mascota/<id>', methods=['POST'])
        @log_cambios(tabla_afectada='mascotas', accion_valor='UPDATE')
        def editar_mascota(id):
            ...
    
    Args:
        tabla_afectada: Nombre de la tabla afectada (ej: 'usuarios', 'mascotas')
        accion_valor: Tipo de acción ('INSERT', 'UPDATE', 'DELETE') o None para detectar
        capturar_antes: Si True, captura datos antes del cambio
        capturar_despues: Si True, captura datos después del cambio
    """
    def decorador(f):
        @wraps(f)
        def decorada(*args, **kwargs):
            try:
                # Almacena info en g (request context) para acceso dentro de la ruta
                g.audit_info = {
                    'tabla_afectada': tabla_afectada,
                    'accion': accion_valor,
                    'capturar_antes': capturar_antes,
                    'capturar_despues': capturar_despues,
                    'datos_antes': None,
                    'datos_despues': None,
                    'registro_id': kwargs.get('id') or request.args.get('id')
                }
                
                # Ejecuta la función
                resultado = f(*args, **kwargs)
                
                # Registra el cambio después de ejecutar
                if hasattr(g, 'audit_info') and g.audit_info.get('tabla_afectada'):
                    _registrar_audit_log(g.audit_info, resultado)
                
                return resultado
                
            except Exception as e:
                current_app.logger.error(f"Error en decorador @log_cambios: {e}")
                # No interrumpe la ejecución si falla el logging
                return f(*args, **kwargs)
        
        return decorada
    
    return decorador


def registrar_auditoria(
    tabla_afectada,
    accion,
    registro_id,
    modelo=None,
    datos_nuevos=None
):
    """
    Helper para registrar auditoría dentro de una función/ruta.
    
    Uso en ruta:
        @app.route('/admin/editar_mascota/<id>', methods=['POST'])
        def editar_mascota(id):
            # Obtiene datos antes
            datos_antes = AuditService.obtener_datos_registro(Mascota, id)
            
            # Realiza la actualización
            mascota = Mascota.query.get(id)
            mascota.nombre = request.form.get('nombre')
            db.session.commit()
            
            # Registra en auditoría
            registrar_auditoria(
                tabla_afectada='mascotas',
                accion='UPDATE',
                registro_id=id,
                modelo=Mascota,
                datos_nuevos={'nombre': mascota.nombre}
            )
            
            return redirect('/admin/mascotas')
    
    Args:
        tabla_afectada: Nombre de la tabla
        accion: INSERT, UPDATE, DELETE
        registro_id: ID del registro afectado
        modelo: Clase del modelo (para obtener datos actuales)
        datos_nuevos: Dict con nuevos datos
    
    Returns:
        AuditLog: Objeto del log creado
    """
    try:
        # Obtiene datos antes si es UPDATE
        datos_antes = None
        if accion == 'UPDATE' and modelo:
            datos_antes = AuditService.obtener_datos_registro(modelo, registro_id)
        
        # Registra el cambio
        log = AuditService.registrar_cambio(
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            datos_antes=datos_antes,
            datos_despues=datos_nuevos
        )
        
        return log
        
    except Exception as e:
        current_app.logger.error(f"Error en registrar_auditoria: {e}")
        return None


def _registrar_audit_log(audit_info, resultado):
    """Helper interno para registrar el log después de ejecutar la ruta."""
    try:
        if not audit_info.get('tabla_afectada'):
            return
        
        accion = audit_info.get('accion') or 'UPDATE'
        tabla = audit_info.get('tabla_afectada')
        registro_id = audit_info.get('registro_id')
        
        if not registro_id:
            return
        
        AuditService.registrar_cambio(
            accion=accion,
            tabla_afectada=tabla,
            registro_id=registro_id,
            datos_antes=audit_info.get('datos_antes'),
            datos_despues=audit_info.get('datos_despues')
        )
        
    except Exception as e:
        current_app.logger.error(f"Error registrando audit log: {e}")


def requerir_admin(f):
    """Decorador que verifica que el usuario sea admin."""
    @wraps(f)
    def decorada(*args, **kwargs):
        usuario_rol = session.get('usuario_rol')
        if usuario_rol != 'admin':
            from flask import redirect, flash
            flash('Acceso denegado: Se requieren permisos de administrador', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorada


def validar_csrf(f):
    """Decorador simple de validación CSRF."""
    @wraps(f)
    def decorada(*args, **kwargs):
        token_form = request.form.get('csrf_token')
        token_session = session.get('_csrf_token')
        
        if not token_form or token_form != token_session:
            return jsonify({'error': 'Token CSRF inválido'}), 403
        
        return f(*args, **kwargs)
    return decorada
