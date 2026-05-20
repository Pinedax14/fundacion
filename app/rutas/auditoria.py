"""
Rutas para visualizar logs de auditoría (admin)
"""

from flask import Blueprint, render_template, request, session, flash, redirect, current_app
from datetime import datetime, timedelta
from types import SimpleNamespace
from functools import wraps
from app.models import db, AuditLog
from app.services.audit_service import AuditService
from app.services.admin_data_service import AdminDataStructureService

admin_data_service = AdminDataStructureService()

# Crear blueprint
auditoria_bp = Blueprint('auditoria', __name__, url_prefix='/admin/auditoria')


def admin_required(f):
    """Decorador para verificar que el usuario sea administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado. Debes ser administrador.', 'danger')
            return redirect('/home')
        return f(*args, **kwargs)
    return decorated_function


@auditoria_bp.route('/logs', methods=['GET'])
@admin_required
def ver_logs():
    """
    Visualiza los logs de auditoría con filtros.
    
    Query params:
        - tabla: Filtrar por tabla (mascotas, usuarios, etc)
        - usuario: Filtrar por usuario_id
        - accion: Filtrar por acción (INSERT, UPDATE, DELETE)
        - fecha_desde: Filtrar por fecha mínima (YYYY-MM-DD)
        - fecha_hasta: Filtrar por fecha máxima (YYYY-MM-DD)
        - pagina: Número de página (default 1)
    """
    try:
        # Obtiene parámetros de filtro
        tabla = request.args.get('tabla')
        usuario_id = request.args.get('usuario', type=int)
        accion = request.args.get('accion')
        fecha_desde_str = request.args.get('fecha_desde')
        fecha_hasta_str = request.args.get('fecha_hasta')
        pagina = request.args.get('pagina', 1, type=int)
        
        # Convierte fechas
        fecha_desde = None
        fecha_hasta = None
        
        if fecha_desde_str:
            try:
                fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        if fecha_hasta_str:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d')
                # Incluye todo el día
                fecha_hasta = fecha_hasta + timedelta(days=1)
            except ValueError:
                pass
        
        # Cargar todos los logs en memoria usando LinkedList
        audit_logs_linkedlist = admin_data_service.cargar_audit_logs_en_linkedlist()

        # Filtrar en memoria según los criterios
        filtered_logs = admin_data_service.filtrar_audit_logs(
            audit_logs_linkedlist,
            tabla=tabla,
            usuario_id=usuario_id,
            accion=accion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        total = len(filtered_logs)
        total_paginas = (total + 49) // 50  # ceil(total / 50)
        
        # Paginación en memoria
        offset = (pagina - 1) * 50
        logs_page = filtered_logs[offset:offset + 50]
        
        # Convertir a objetos tipo atributo para plantilla
        logs_page = [SimpleNamespace(**log) for log in logs_page]
        
        # Tablas de todos los logs para el dropdown
        tablas = sorted({log.get('tabla_afectada') for log in audit_logs_linkedlist if log.get('tabla_afectada')})
        acciones = ['INSERT', 'UPDATE', 'DELETE']
        
        return render_template('admin/audit_logs.html',
                               logs=logs_page,
                               total=total,
                               pagina=pagina,
                               total_paginas=total_paginas,
                               tablas=tablas,
                               acciones=acciones,
                               filtros={
                                   'tabla': tabla,
                                   'usuario_id': usuario_id,
                                   'accion': accion,
                                   'fecha_desde': fecha_desde_str,
                                   'fecha_hasta': fecha_hasta_str
                               })
    
    except Exception as e:
        current_app.logger.error(f"Error en ver_logs: {e}")
        flash('Error cargando los logs', 'error')
        return redirect('/admin')


@auditoria_bp.route('/detalles/<int:log_id>', methods=['GET'])
@admin_required
def detalles_log(log_id):
    """
    Muestra detalles completos de un log.
    """
    try:
        log = AuditLog.query.get(log_id)
        
        if not log:
            flash('Log no encontrado', 'error')
            return redirect('/admin/auditoria/logs')
        
        return render_template('admin/detalles_log.html', log=log)
    
    except Exception as e:
        current_app.logger.error(f"Error en detalles_log: {e}")
        flash('Error cargando el log', 'error')
        return redirect('/admin/auditoria/logs')


@auditoria_bp.route('/anomalias', methods=['GET'])
@admin_required
def detectar_anomalias():
    """
    Muestra anomalías detectadas en los últimos cambios.
    """
    try:
        ventana = request.args.get('ventana', 5, type=int)
        anomalias = AuditService.detectar_anomalias(ventana_minutos=ventana)
        
        return render_template('admin/anomalias.html',
                               anomalias=anomalias,
                               ventana=ventana)
    
    except Exception as e:
        current_app.logger.error(f"Error en detectar_anomalias: {e}")
        flash('Error detectando anomalías', 'error')
        return redirect('/admin')


@auditoria_bp.route('/exportar', methods=['GET'])
@admin_required
def exportar_logs():
    """
    Exporta logs en CSV.
    """
    try:
        tabla = request.args.get('tabla')
        usuario_id = request.args.get('usuario', type=int)
        accion = request.args.get('accion')
        
        audit_logs_linkedlist = admin_data_service.cargar_audit_logs_en_linkedlist()
        filtered_logs = admin_data_service.filtrar_audit_logs(
            audit_logs_linkedlist,
            tabla=tabla,
            usuario_id=usuario_id,
            accion=accion
        )
        
        # Genera CSV
        csv_data = "ID,Timestamp,Usuario,Acción,Tabla,Registro_ID,IP,Método,Ruta\n"
        
        for log in filtered_logs:
            csv_data += f"{log['id']},{log['timestamp'].isoformat()},{log.get('usuario_nombre','')},"
            csv_data += f"{log.get('accion','')},{log.get('tabla_afectada','')},{log.get('registro_id','')},"
            csv_data += f"{log.get('ip_address','')},{log.get('metodo_http','')},{log.get('ruta','')}\n"
        
        from flask import make_response
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = "attachment; filename=audit_logs.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
    
    except Exception as e:
        current_app.logger.error(f"Error en exportar_logs: {e}")
        flash('Error exportando logs', 'error')
        return redirect('/admin/auditoria/logs')


@auditoria_bp.route('/limpiar', methods=['POST'])
@admin_required
def limpiar_logs():
    """
    Limpia logs más antiguos (archivado).
    """
    try:
        dias = request.form.get('dias', 90, type=int)
        eliminados = AuditService.limpiar_logs_antiguos(dias=dias)
        
        flash(f"Se eliminaron {eliminados} logs más antiguos de {dias} días", 'success')
        return redirect('/admin/auditoria/logs')
    
    except Exception as e:
        current_app.logger.error(f"Error en limpiar_logs: {e}")
        flash('Error limpiando logs', 'error')
        return redirect('/admin/auditoria/logs')
