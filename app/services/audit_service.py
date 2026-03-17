"""
Servicio de Auditoría para registrar cambios en la BD
"""

import json
from datetime import datetime
from flask import request, session, current_app
from app.models import db, AuditLog, Usuario
from app.logger import setup_logger  # Solo importamos la función


class AuditService:
    """Servicio centralizado para logging de auditoría."""
    
    @staticmethod
    def obtener_ip_usuario():
        """Obtiene la IP real del cliente (maneja X-Forwarded-For)."""
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ.get('HTTP_X_FORWARDED_FOR').split(',')[0].strip()
        return request.remote_addr or 'desconocida'
    
    @staticmethod
    def obtener_user_agent():
        """Obtiene el User-Agent del cliente."""
        return request.user_agent.string[:500] if request.user_agent else 'desconocido'
    
    @staticmethod
    def obtener_usuario_actual():
        """Obtiene el usuario actual de la sesión."""
        usuario_id = session.get('usuario_id')
        usuario_nombre = session.get('usuario_nombre', 'anonimo')
        return usuario_id, usuario_nombre
    
    @staticmethod
    def convertir_a_json_serializable(valor):
        """Convierte valores no serializables a JSON."""
        if valor is None:
            return None
        if isinstance(valor, (dict, list, str, int, float, bool)):
            return valor
        if isinstance(valor, datetime):
            return valor.isoformat()
        if hasattr(valor, '__dict__'):  # Objeto personalizado
            return str(valor)
        return str(valor)
    
    @staticmethod
    def obtener_datos_registro(modelo, registro_id):
        """
        Obtiene los datos actuales de un registro.
        
        Args:
            modelo: Clase del modelo SQLAlchemy
            registro_id: ID del registro a obtener
            
        Returns:
            Dict con los datos del registro o None
        """
        try:
            registro = modelo.query.get(registro_id)
            if not registro:
                return None
            
            # Convierte a dict excluyendo relaciones
            datos = {}
            for columna in modelo.__table__.columns:
                valor = getattr(registro, columna.name)
                datos[columna.name] = AuditService.convertir_a_json_serializable(valor)
            return datos
        except Exception as e:
            current_app.logger.error(f"Error obteniendo datos del registro {modelo.__name__} {registro_id}: {e}")
            return None
    
    @staticmethod
    def registrar_cambio(
        accion,
        tabla_afectada,
        registro_id,
        datos_antes=None,
        datos_despues=None,
        notas=None
    ):
        """
        Registra un cambio en el audit_log.
        
        Args:
            accion: 'INSERT', 'UPDATE', 'DELETE'
            tabla_afectada: Nombre de la tabla (ej: 'usuarios', 'mascotas')
            registro_id: ID del registro modificado
            datos_antes: Dict con datos antes del cambio
            datos_despues: Dict con datos después del cambio
            notas: Notas adicionales
        
        Returns:
            AuditLog: El objeto creado o None si falló
        """
        try:
            usuario_id, usuario_nombre = AuditService.obtener_usuario_actual()
            ip = AuditService.obtener_ip_usuario()
            user_agent = AuditService.obtener_user_agent()
            
            log = AuditLog(
                usuario_id=usuario_id,
                usuario_nombre=usuario_nombre,
                accion=accion,
                tabla_afectada=tabla_afectada,
                registro_id=registro_id,
                datos_antes=datos_antes,
                datos_despues=datos_despues,
                ip_address=ip,
                user_agent=user_agent,
                metodo_http=request.method,
                ruta=request.path,
                notas=notas
            )
            
            db.session.add(log)
            db.session.commit()
            
            current_app.logger.info(
                f"[AUDIT] {accion} {tabla_afectada}[{registro_id}] "
                f"usuario={usuario_nombre} ip={ip}"
            )
            
            return log
            
        except Exception as e:
            current_app.logger.error(f"Error registrando cambio en audit_log: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def registrar_actualizacion(
        modelo,
        registro_id,
        datos_nuevos,
        notas=None
    ):
        """
        Registra una actualización capturando datos antes y después.
        
        Args:
            modelo: Clase del modelo SQLAlchemy
            registro_id: ID del registro a actualizar
            datos_nuevos: Dict con los nuevos datos
            notas: Notas adicionales
        """
        # Captura datos antes
        datos_antes = AuditService.obtener_datos_registro(modelo, registro_id)
        
        # Realiza la actualización (asume que ya se hizo en la ruta)
        # Captura datos después
        datos_despues = datos_nuevos  # O puedes hacer refresh si quieres
        
        # Registra el cambio
        AuditService.registrar_cambio(
            accion='UPDATE',
            tabla_afectada=modelo.__tablename__,
            registro_id=registro_id,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
            notas=notas
        )
    
    @staticmethod
    def obtener_logs_filtrados(
        tabla_afectada=None,
        usuario_id=None,
        accion=None,
        fecha_desde=None,
        fecha_hasta=None,
        limite=100,
        pagina=1
    ):
        """
        Obtiene logs con filtros avanzados.
        
        Args:
            tabla_afectada: Filtrar por tabla
            usuario_id: Filtrar por usuario
            accion: Filtrar por acción (INSERT, UPDATE, DELETE)
            fecha_desde: Filtrar por fecha mínima
            fecha_hasta: Filtrar por fecha máxima
            limite: Registros por página
            pagina: Número de página
            
        Returns:
            (logs, total): Lista de logs y total de registros
        """
        try:
            query = AuditLog.query
            
            if tabla_afectada:
                query = query.filter_by(tabla_afectada=tabla_afectada)
            
            if usuario_id:
                query = query.filter_by(usuario_id=usuario_id)
            
            if accion:
                query = query.filter_by(accion=accion)
            
            if fecha_desde:
                query = query.filter(AuditLog.timestamp >= fecha_desde)
            
            if fecha_hasta:
                query = query.filter(AuditLog.timestamp <= fecha_hasta)
            
            total = query.count()
            
            logs = query.order_by(AuditLog.timestamp.desc()).limit(limite).offset(
                (pagina - 1) * limite
            ).all()
            
            return logs, total
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo logs filtrados: {e}")
            return [], 0
    
    @staticmethod
    def detectar_anomalias(ventana_minutos=5):
        """
        Detecta anomalías como múltiples cambios rápidos de la misma IP.
        
        Returns:
            Lista de anomalías detectadas
        """
        try:
            from datetime import timedelta
            
            hace = datetime.utcnow() - timedelta(minutes=ventana_minutos)
            
            # Detecta múltiples DELETE en poco tiempo
            deletes = AuditLog.query.filter(
                AuditLog.accion == 'DELETE',
                AuditLog.timestamp >= hace
            ).all()
            
            anomalias = []
            if len(deletes) > 5:  # Más de 5 deletes en 5 minutos es sospechoso
                anomalias.append({
                    'tipo': 'MULTIPLE_DELETES',
                    'cantidad': len(deletes),
                    'ventana_minutos': ventana_minutos,
                    'logs': [d.id for d in deletes]
                })
            
            # Detecta múltiples intentos fallidos de la misma IP
            ips = {}
            for log in AuditLog.query.filter(
                AuditLog.timestamp >= hace
            ).all():
                if not log.ip_address:
                    continue
                if log.ip_address not in ips:
                    ips[log.ip_address] = []
                ips[log.ip_address].append(log.id)
            
            for ip, log_ids in ips.items():
                if len(log_ids) > 20:  # Más de 20 operaciones en 5 minutos
                    anomalias.append({
                        'tipo': 'ACTIVIDAD_SOSPECHOSA',
                        'ip': ip,
                        'cantidad_operaciones': len(log_ids),
                        'logs': log_ids
                    })
            
            return anomalias
            
        except Exception as e:
            current_app.logger.error(f"Error detectando anomalías: {e}")
            return []
    
    @staticmethod
    def limpiar_logs_antiguos(dias=90):
        """
        Limpia logs más antiguos que X días (por rendimiento).
        
        Args:
            dias: Días de antigüedad para eliminar
        """
        try:
            from datetime import timedelta
            
            fecha_limite = datetime.utcnow() - timedelta(days=dias)
            eliminados = AuditLog.query.filter(
                AuditLog.timestamp < fecha_limite
            ).delete()
            
            db.session.commit()
            current_app.logger.info(f"Se eliminaron {eliminados} logs antiguos (> {dias} días)")
            return eliminados
            
        except Exception as e:
            current_app.logger.error(f"Error limpiando logs antiguos: {e}")
            db.session.rollback()
            return 0
