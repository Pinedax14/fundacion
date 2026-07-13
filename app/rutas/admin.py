"""
Módulo de rutas administrativas
Contiene las rutas para gestionar solicitudes, reportes, mascotas y donaciones (admin only)
"""

import os
import traceback
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, session, flash
from app.rutas.decoradores import admin_required_factory
from app.services.admin_data_service import AdminDataStructureService
from app.services.audit_service import AuditService


class RutasAdmin:
    """
    Gestiona rutas administrativas (requieren rol admin):
    - Panel de admin (/admin/panel)
    - Detalles de solicitud (/admin/detalle_solicitud/<id>)
    - Responder solicitud (/admin/respuesta_solicitud/<id>)
    - Detalles de reporte (/admin/reporte/<id>)
    - Resolver reporte (/reporte/resolver/<id>)
    - Eliminar reporte (/reporte/eliminar/<id>)
    - Ingresar mascota (/admin/ingresar_mascota)
    - Recibir donación (/recibir_donacion)
    """

    def __init__(self, app, conexion):
        """
        Inicializa las rutas administrativas

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion
        """
        self.app = app
        self.conexion = conexion
        self.bcrypt = conexion.bcrypt
        self.admin_data_service = AdminDataStructureService()   # Servicio para cargar datos en estructuras de nodos (LinkedList, Queue)            
        # Crear decorador admin que usa la misma sesión/contexto
        self.admin_required = admin_required_factory(app)
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas administrativas"""

        @self.app.route('/admin/panel')
        @self.admin_required    # Solo accesible para administradores
        def admin_panel():
            
            """
            Muestra el panel principal de administración
            Carga solicitudes, reportes y voluntariados en estructuras de nodos (LinkedList, Queue)
            Solo accesible para administradores
            """
            try:
                # Cargar datos en estructuras de nodos
                solicitudes_linkedlist = self.admin_data_service.cargar_solicitudes_en_linkedlist()
                reportes_queue = self.admin_data_service.cargar_reportes_en_queue()
                voluntariados_linkedlist = self.admin_data_service.cargar_voluntariados_en_linkedlist()

                todas_solicitudes = solicitudes_linkedlist.to_list()

                reportes = []
                while len(reportes_queue) > 0:
                    reportes.append(reportes_queue.dequeue())
                solicitudes_voluntariado = voluntariados_linkedlist.to_list()

                # ── KPIs y "lo más urgente" para la vista Hoy (independientes del
                # filtro de la tabla de solicitudes, siempre reflejan el total real) ──
                pendientes_solicitudes = [s for s in todas_solicitudes if s.get('estado_solicitud') == 'pendiente']
                solicitud_urgente = min(pendientes_solicitudes, key=lambda s: s['fecha_solicitud']) if pendientes_solicitudes else None

                # `reportes` ya viene ordenado ascendente por fecha (FIFO de la Queue),
                # así que el primero sin resolver es el más antiguo.
                reportes_sin_resolver = [r for r in reportes if r.get('estado_reporte') != 'resuelto']
                reporte_urgente = reportes_sin_resolver[0] if reportes_sin_resolver else None

                voluntariado_pendiente_count = sum(
                    1 for v in solicitudes_voluntariado if str(v.get('estado', '')).lower() == 'pendiente'
                )

                # Filtrar solicitudes en memoria si se solicita un estado
                estado_filtro = request.args.get('estado')
                if estado_filtro:
                    solicitudes = self.admin_data_service.filtrar_solicitudes_por_estado(solicitudes_linkedlist, estado_filtro)
                else:
                    # Vista por defecto: solo pendientes y aprobadas (las rechazadas
                    # quedan ocultas, se consultan aparte con ?estado=rechazada).
                    # Pendientes primero, luego aprobadas; dentro de cada grupo se
                    # conserva el orden por fecha (más reciente primero) ya traído de la BD.
                    orden_estado = {'pendiente': 0, 'aprobada': 1}
                    solicitudes = sorted(
                        (s for s in todas_solicitudes if s.get('estado_solicitud') != 'rechazada'),
                        key=lambda s: orden_estado.get(s.get('estado_solicitud'), 2)
                    )

                # Tab activo: si viene explícito en la URL se respeta (así las
                # acciones que redirigen de vuelta al panel te dejan donde estabas);
                # si hay un filtro de estado, tiene sentido caer en "Solicitudes";
                # si no, la vista de inicio es "Hoy".
                tab_activo = request.args.get('tab') or ('solicitudes' if estado_filtro else 'hoy')

                print(f"DEBUG: Cargadas {len(solicitudes)} solicitudes en LinkedList")
                print(f"DEBUG: Cargados {len(reportes)} reportes en Queue")
                print(f"DEBUG: Cargadas {len(solicitudes_voluntariado)} solicitudes de voluntariado en LinkedList")

                return render_template(
                    'admin/admin_panel.html',
                    solicitudes=solicitudes,
                    reportes=reportes,
                    solicitudes_voluntariado=solicitudes_voluntariado,
                    mostrar_link_notebook=self.app.debug,
                    estado_filtro=estado_filtro,
                    tab_activo=tab_activo,
                    pendientes_count=len(pendientes_solicitudes),
                    solicitud_urgente=solicitud_urgente,
                    reportes_sin_resolver_count=len(reportes_sin_resolver),
                    reporte_urgente=reporte_urgente,
                    voluntariado_pendiente_count=voluntariado_pendiente_count
                )
            except Exception as e:
                print(f"ERROR en admin_panel: {e}")  # Debug
                flash(f'Error al cargar panel: {e}', 'danger')
                return render_template(
                    'admin/admin_panel.html',
                    solicitudes=[], reportes=[], solicitudes_voluntariado=[],
                    mostrar_link_notebook=self.app.debug, estado_filtro=None, tab_activo='hoy',
                    pendientes_count=0, solicitud_urgente=None,
                    reportes_sin_resolver_count=0, reporte_urgente=None,
                    voluntariado_pendiente_count=0
                )

        @self.app.route('/admin/detalle_solicitud/<int:solicitud_id>')
        @self.admin_required
        def detalle_solicitud(solicitud_id):
            """
            Muestra los detalles completos de una solicitud de adopción
            Incluye información del usuario y la mascota

            Args:
                solicitud_id: ID de la solicitud
            """
            try:
                cursor = self.conexion.get_cursor()
                query = """
                    SELECT s.*, u.nombre AS usuario_nombre, u.email AS usuario_email,
                           m.nombre AS mascota_nombre, m.foto_url AS mascota_foto
                    FROM solicitudes_adopcion s
                    JOIN usuarios u ON s.id_usuario = u.id
                    JOIN mascotas m ON s.id_mascota = m.id
                    WHERE s.id = %s
                """
                cursor.execute(query, [solicitud_id])
                solicitud = cursor.fetchone()
                cursor.close()

                if solicitud:
                    return render_template('admin/detalle_solicitud.html', solicitud=solicitud)

                flash('Solicitud no encontrada.', 'danger')
                return redirect(url_for('admin_panel', tab='solicitudes'))
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al cargar solicitud: {e}', 'danger')
                return redirect(url_for('admin_panel', tab='solicitudes'))

        @self.app.route('/admin/respuesta_solicitud/<int:solicitud_id>', methods=['POST'])
        @self.admin_required
        def respuesta_solicitud(solicitud_id):
            """
            Procesa la respuesta a una solicitud de adopción (aprobada/rechazada)
            También actualiza el estado de la mascota

            Args:
                solicitud_id: ID de la solicitud
            """
            respuesta = request.form.get('respuesta')

            # Validar que la respuesta sea válida
            if respuesta not in ['aprobada', 'rechazada']:
                flash('Respuesta inválida. Se recibió un valor incorrecto desde el formulario.', 'danger')
                return redirect(url_for('admin_panel', tab='solicitudes'))

            try:
                cursor = self.conexion.get_cursor()

                # Actualizar estado de la solicitud
                cursor.execute("UPDATE solicitudes_adopcion SET estado_solicitud = %s WHERE id = %s",
                             (respuesta, solicitud_id))

                # Obtener ID de la mascota
                cursor.execute('SELECT id_mascota FROM solicitudes_adopcion WHERE id = %s', [solicitud_id])
                resultado = cursor.fetchone()

                if resultado:
                    id_mascota = resultado['id_mascota']
                    # Cambiar estado de la mascota según la respuesta
                    nuevo_estado_mascota = 'Adoptado' if respuesta == 'aprobada' else 'Disponible'
                    cursor.execute("UPDATE mascotas SET estado = %s WHERE id = %s",
                                 (nuevo_estado_mascota, id_mascota))

                self.conexion.commit()
                cursor.close()

                # Registrar en auditoría
                AuditService.registrar_cambio(
                    accion='UPDATE',
                    tabla_afectada='solicitudes_adopcion',
                    registro_id=solicitud_id,
                    datos_despues={'estado_solicitud': respuesta},
                    notas=f'Solicitud de adopción {respuesta} por administrador'
                )
                
                flash(f'La solicitud ha sido marcada como \"{respuesta}\".', 'success')
                return redirect(url_for('admin_panel', tab='solicitudes'))

            except Exception as e:
                self.conexion.rollback()
                flash(f'Ocurrió un error de base de datos: {e}', 'danger')
                return redirect(url_for('admin_panel', tab='solicitudes'))

        @self.app.route('/admin/reporte/<int:reporte_id>')
        @self.admin_required
        def detalle_reporte(reporte_id):
            """
            Muestra los detalles completos de un reporte de maltrato

            Args:
                reporte_id: ID del reporte
            """
            try:
                cursor = self.conexion.get_cursor()
                cursor.execute("SELECT * FROM reportes WHERE id = %s", [reporte_id])
                reporte = cursor.fetchone()
                cursor.close()

                if not reporte:
                    flash('El reporte no fue encontrado.', 'warning')
                    return redirect(url_for('admin_panel', tab='reportes'))

                return render_template('admin/detalle_reporte.html', reporte=reporte)
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al cargar reporte: {e}', 'danger')
                return redirect(url_for('admin_panel', tab='reportes'))

        @self.app.route('/reporte/resolver/<int:reporte_id>', methods=['POST'])
        @self.admin_required
        def marcar_reporte_resuelto(reporte_id):
            """
            Marca un reporte como resuelto

            Args:
                reporte_id: ID del reporte
            """
            try:
                cur = self.conexion.get_cursor()
                cur.execute("UPDATE reportes SET estado_reporte = 'resuelto' WHERE id = %s", [reporte_id])
                self.conexion.commit()
                cur.close()
                
                # Registrar en auditoría
                AuditService.registrar_cambio(
                    accion='UPDATE',
                    tabla_afectada='reportes',
                    registro_id=reporte_id,
                    datos_despues={'estado_reporte': 'resuelto'},
                    notas='Reporte de maltrato marcado como resuelto'
                )
                
                flash('El reporte ha sido marcado como resuelto.', 'success')
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al actualizar el reporte: {e}', 'danger')
            return redirect(url_for('admin_panel', tab='reportes'))

        @self.app.route('/reporte/eliminar/<int:reporte_id>', methods=['POST'])
        @self.admin_required
        def eliminar_reporte(reporte_id):
            """
            Elimina un reporte y su foto de evidencia asociada (si existe)

            Args:
                reporte_id: ID del reporte
            """
            try:
                cursor = self.conexion.get_cursor()

                # Obtener foto asociada al reporte
                cursor.execute("SELECT foto_evidencia_url FROM reportes WHERE id = %s", [reporte_id])
                reporte = cursor.fetchone()

                # Eliminar archivo de imagen si existe
                if reporte and reporte['foto_evidencia_url']:
                    try:
                        ruta_foto = os.path.join(self.app.static_folder, reporte['foto_evidencia_url'])
                        if os.path.exists(ruta_foto):
                            os.remove(ruta_foto)
                    except Exception as e:
                        self.app.logger.warning(f"No se pudo eliminar el archivo de imagen: {e}")

                # Eliminar reporte de BD
                cursor.execute("DELETE FROM reportes WHERE id = %s", [reporte_id])
                self.conexion.commit()
                cursor.close()

                # Registrar en auditoría
                AuditService.registrar_cambio(
                    accion='DELETE',
                    tabla_afectada='reportes',
                    registro_id=reporte_id,
                    notas='Reporte de maltrato eliminado por administrador'
                )

                flash('El reporte ha sido eliminado correctamente.', 'success')
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al eliminar el reporte: {e}', 'danger')
            return redirect(url_for('admin_panel', tab='reportes'))

        @self.app.route('/admin/ingresar_mascota', methods=['GET', 'POST'])
        @self.admin_required
        def ingresar_mascota():
            """
            GET: Muestra formulario para ingresar una nueva mascota
            POST: Procesa la creación de una nueva mascota en el sistema
            Incluye carga de foto
            """
            if request.method == 'POST':
                # Obtener datos del formulario
                nombre = request.form.get('nombre')
                especie = request.form.get('especie')
                raza = request.form.get('raza')
                edad = request.form.get('edad')
                sexo = request.form.get('sexo')
                descripcion = request.form.get('descripcion')
                foto = request.files.get('foto')

                # Validar que los campos obligatorios están presentes
                campos_obligatorios = {
                    'nombre': nombre,
                    'especie': especie,
                    'sexo': sexo,
                    'descripcion': descripcion
                }

                for campo, valor in campos_obligatorios.items():
                    if not valor or valor.strip() == '':
                        flash(f'El campo {campo} es obligatorio.', 'danger')
                        return redirect(url_for('ingresar_mascota'))

                # Procesar foto
                foto_url = None
                if foto:
                    # Generar nombre único para la foto
                    extension = ".jpg"
                    nombre_base = secure_filename(nombre.replace(" ", "_"))
                    nombre_archivo = f"{nombre_base}{extension}"
                    ruta_guardado = os.path.join(self.app.static_folder, 'images', 'mascotas', nombre_archivo)

                    # Evitar sobrescribir si el archivo ya existe
                    contador = 1
                    while os.path.exists(ruta_guardado):
                        nombre_archivo = f"{nombre_base}_{contador}{extension}"
                        ruta_guardado = os.path.join(self.app.static_folder, 'images', 'mascotas', nombre_archivo)
                        contador += 1

                    foto.save(ruta_guardado)
                    foto_url = f'images/mascotas/{nombre_archivo}'

                try:
                    # Guardar mascota en BD
                    cursor = self.conexion.get_cursor()
                    cursor.execute("""
                        INSERT INTO mascotas (nombre, especie, raza, edad, sexo, descripcion, foto_url, estado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (nombre, especie, raza, edad, sexo, descripcion, foto_url, 'Disponible'))
                    
                    resultado = cursor.fetchone()
                    mascota_id = resultado['id'] if resultado else None
                    self.conexion.commit()
                    cursor.close()

                    # Registrar en auditoría
                    AuditService.registrar_cambio(
                        accion='INSERT',
                        tabla_afectada='mascotas',
                        registro_id=mascota_id,
                        datos_despues={
                            'nombre': nombre,
                            'especie': especie,
                            'raza': raza,
                            'edad': edad,
                            'sexo': sexo,
                            'estado': 'Disponible'
                        },
                        notas='Mascota ingresada al sistema por administrador'
                    )

                    flash('Mascota agregada correctamente.', 'success')
                    return redirect(url_for('admin_panel'))

                except Exception as e:
                    self.conexion.rollback()
                    self.app.logger.error(f"\n=== DEBUG ERROR: {str(e)} ===\n")
                    flash(f'Ocurrió un error al agregar la mascota: {e}', 'danger')
                    return redirect(url_for('ingresar_mascota'))

            return render_template('admin/ingreso_mascota.html')

        @self.app.route('/recibir_donacion', methods=['POST'])
        @self.admin_required
        def recibir_donacion():
            """
            Procesa la recepción de una donación (por implementar)
            """
            return redirect(url_for('admin_panel'))
