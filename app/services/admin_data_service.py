"""
Servicio para cargar datos en estructuras de nodos (LinkedList, Queue).
Encapsula la lógica de transformar resultados de BD a estructuras basadas en nodos.
"""

from sqlalchemy import text
from app.models import db
from app.utils.data_structures import LinkedList, Queue


class AdminDataStructureService:
    """Servicio que carga datos de la BD en estructuras de nodos para procesamiento en memoria."""

    @staticmethod
    def cargar_solicitudes_en_linkedlist():
        """
        Carga todas las solicitudes de adopción en una LinkedList.
        
        Returns:
            LinkedList: Lista enlazada con solicitudes de adopción.
        """
        sql = text("""
            SELECT s.id, u.nombre AS usuario_nombre, m.nombre AS mascota_nombre,
                   s.fecha_solicitud, s.estado_solicitud, s.id_usuario, s.id_mascota
            FROM solicitudes_adopcion s
            JOIN usuarios u ON s.id_usuario = u.id
            JOIN mascotas m ON s.id_mascota = m.id
            ORDER BY s.fecha_solicitud DESC
        """)
        result = db.session.execute(sql).mappings().all()
        
        lista = LinkedList()
        for row in result:
            lista.append(dict(row))
        
        return lista

    @staticmethod
    def cargar_usuarios_en_linkedlist():
        """
        Carga todos los usuarios en una LinkedList para procesamiento en memoria.
        """
        sql = text("""
            SELECT id, nombre, email, password, fecha_registro, rol
            FROM usuarios
            ORDER BY fecha_registro DESC
        """)
        result = db.session.execute(sql).mappings().all()

        lista = LinkedList()
        for row in result:
            lista.append(dict(row))

        return lista

    @staticmethod
    def cargar_solicitudes_usuario_en_linkedlist(usuario_id):
        """
        Carga las solicitudes de adopción de un usuario específico en una LinkedList.
        Incluye nombre y foto de la mascota para mostrar en el perfil.
        """
        sql = text("""
            SELECT s.id,
                   s.fecha_solicitud,
                   s.estado_solicitud AS estado_solicitud,
                   m.nombre AS mascota_nombre,
                   m.foto_url AS mascota_foto
            FROM solicitudes_adopcion s
            JOIN mascotas m ON s.id_mascota = m.id
            WHERE s.id_usuario = :usuario_id
            ORDER BY s.fecha_solicitud DESC
        """)
        result = db.session.execute(sql, {'usuario_id': usuario_id}).mappings().all()

        lista = LinkedList()
        for row in result:
            lista.append(dict(row))

        return lista

    @staticmethod
    def cargar_reportes_en_queue():
        """
        Carga todos los reportes en una Queue (FIFO).
        Útil para procesar reportes en orden de llegada.
        
        Returns:
            Queue: Cola con reportes de maltrato.
        """
        sql = text("""
            SELECT id, ubicacion, descripcion_incidente, foto_evidencia_url,
                   estado_reporte, fecha_reporte
            FROM reportes
            ORDER BY fecha_reporte ASC
        """)
        result = db.session.execute(sql).mappings().all()
        
        cola = Queue()
        for row in result:
            cola.enqueue(dict(row))
        
        return cola

    @staticmethod
    def cargar_voluntariados_en_linkedlist():
        """
        Carga todas las solicitudes de voluntariado en una LinkedList.
        
        Returns:
            LinkedList: Lista enlazada con solicitudes de voluntariado.
        """
        sql = text("""
            SELECT id, nombre_completo, correo, telefono, franja_dias, dias_semana,
                   franja_horaria, motivo_voluntariado, estado, fecha_solicitud
            FROM solicitudes_voluntariado
            ORDER BY fecha_solicitud DESC
        """)
        result = db.session.execute(sql).mappings().all()
        
        lista = LinkedList()
        for row in result:
            lista.append(dict(row))
        
        return lista

    @staticmethod
    def cargar_mascotas_en_linkedlist():
        """
        Carga todas las mascotas en una LinkedList.
        Ideal para filtrar por estado, especie, etc. en memoria.
        
        Returns:
            LinkedList: Lista enlazada con mascotas.
        """
        sql = text("""
            SELECT id, nombre, especie, raza, edad, sexo, descripcion,
                   foto_url, estado, fecha_ingreso
            FROM mascotas
            ORDER BY fecha_ingreso DESC
        """)
        result = db.session.execute(sql).mappings().all()
        
        lista = LinkedList()
        for row in result:
            lista.append(dict(row))
        
        return lista

    @staticmethod
    def cargar_donaciones_en_linkedlist():
        """
        Carga todas las donaciones en una LinkedList para procesamiento en memoria.
        """
        sql = text("""
            SELECT id, nombre_donante, contacto_email, tipo_donacion,
                   descripcion_donacion, fecha_donacion, estado_entrega
            FROM donaciones_items
            ORDER BY fecha_donacion DESC
        """)
        result = db.session.execute(sql).mappings().all()

        lista = LinkedList()
        for row in result:
            lista.append(dict(row))

        return lista

    @staticmethod
    def cargar_audit_logs_en_linkedlist():
        """
        Carga todos los logs de auditoría en una LinkedList.
        """
        sql = text("""
            SELECT id, timestamp, usuario_id, usuario_nombre, accion, tabla_afectada,
                   registro_id, ip_address, metodo_http, ruta
            FROM audit_logs
            ORDER BY timestamp DESC
        """)
        result = db.session.execute(sql).mappings().all()

        lista = LinkedList()
        for row in result:
            lista.append(dict(row))

        return lista

    @staticmethod
    def filtrar_audit_logs(audit_logs_linkedlist, tabla=None, usuario_id=None, accion=None, fecha_desde=None, fecha_hasta=None):
        """
        Filtra logs en memoria con los criterios suministrados.
        
        Args:
            audit_logs_linkedlist: LinkedList con logs de auditoría
            tabla: Filtrar por tabla_afectada
            usuario_id: Filtrar por usuario_id
            accion: Filtrar por acción (INSERT, UPDATE, DELETE)
            fecha_desde: Filtrar desde esta fecha (datetime)
            fecha_hasta: Filtrar hasta esta fecha (datetime)
            
        Returns:
            list: Lista de logs que coinciden con los criterios
        """
        logs = []
        for log in audit_logs_linkedlist:
            if tabla and log.get('tabla_afectada') != tabla:
                continue
            if accion and log.get('accion') != accion:
                continue
            if usuario_id is not None and log.get('usuario_id') != usuario_id:
                continue
            
            # Manejar timestamp como datetime o string
            timestamp = log.get('timestamp')
            if timestamp and isinstance(timestamp, str):
                try:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    pass
            
            if fecha_desde and timestamp:
                if isinstance(timestamp, str) and isinstance(fecha_desde, str):
                    if timestamp < fecha_desde:
                        continue
                elif hasattr(timestamp, '__lt__'):
                    if timestamp < fecha_desde:
                        continue
                        
            if fecha_hasta and timestamp:
                if isinstance(timestamp, str) and isinstance(fecha_hasta, str):
                    if timestamp >= fecha_hasta:
                        continue
                elif hasattr(timestamp, '__ge__'):
                    if timestamp >= fecha_hasta:
                        continue
            
            logs.append(log)

        return logs

    @staticmethod
    def filtrar_solicitudes_por_estado(solicitudes_linkedlist, estado):
        """
        Filtra solicitudes en memoria por estado.
        
        Args:
            solicitudes_linkedlist (LinkedList): Lista de solicitudes.
            estado (str): Estado a filtrar (pendiente, aprobada, rechazada).
        
        Returns:
            list: Solicitudes que coinciden.
        """
        return [s for s in solicitudes_linkedlist if s.get('estado_solicitud') == estado]

    @staticmethod
    def filtrar_reportes_por_estado(reportes_queue, estado):
        """
        Filtra reportes en memoria por estado.
        NOTA: Las colas se destruyen al iterar, así que esto devuelve una lista.
        
        Args:
            reportes_queue (Queue): Cola de reportes.
            estado (str): Estado a filtrar (recibido, en_proceso, resuelto).
        
        Returns:
            list: Reportes que coinciden.
        """
        reportes = []
        while len(reportes_queue) > 0:
            reporte = reportes_queue.dequeue()
            reportes.append(reporte)
        
        return [r for r in reportes if r.get('estado_reporte') == estado]

    @staticmethod
    def filtrar_mascotas_por_estado(mascotas_linkedlist, estado):
        """
        Filtra mascotas en memoria por estado.
        
        Args:
            mascotas_linkedlist (LinkedList): Lista de mascotas.
            estado (str): Estado a filtrar (Disponible, En proceso, Adoptado).
        
        Returns:
            list: Mascotas que coinciden.
        """
        return [m for m in mascotas_linkedlist if m.get('estado') == estado]

    @staticmethod
    def buscar_solicitud_por_id(solicitudes_linkedlist, solicitud_id):
        """
        Busca una solicitud en la LinkedList por ID.
        
        Args:
            solicitudes_linkedlist (LinkedList): Lista de solicitudes.
            solicitud_id (int): ID de la solicitud.
        
        Returns:
            dict | None: Solicitud encontrada o None.
        """
        return solicitudes_linkedlist.find(lambda s: s.get('id') == solicitud_id)

    @staticmethod
    def buscar_reporte_por_id(reportes_list, reporte_id):
        """
        Busca un reporte en una lista por ID.
        
        Args:
            reportes_list (list): Lista de reportes.
            reporte_id (int): ID del reporte.
        
        Returns:
            dict | None: Reporte encontrado o None.
        """
        return next((r for r in reportes_list if r.get('id') == reporte_id), None)

    @staticmethod
    def buscar_mascota_por_id(mascotas_linkedlist, mascota_id):
        """
        Busca una mascota en la LinkedList por ID.
        
        Args:
            mascotas_linkedlist (LinkedList): Lista de mascotas.
            mascota_id (int): ID de la mascota.
        
        Returns:
            dict | None: Mascota encontrada o None.
        """
        return mascotas_linkedlist.find(lambda m: m.get('id') == mascota_id)
