"""
Módulo de rutas administrativas
Contiene las rutas para gestionar solicitudes, reportes, mascotas y donaciones (admin only)
"""

import os
import traceback
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, session, flash
from app.models import Mascota
from app.rutas.decoradores import admin_required_factory


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
        # Crear decorador admin que usa la misma sesión/contexto
        self.admin_required = admin_required_factory(app)
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas administrativas"""

        @self.app.route('/admin/panel')
        @self.admin_required
        def admin_panel():
             if db.session.is_active:
              db.session.rollback()
    
             try:
                mascotas = Mascota.query.order_by(Mascota.estado.asc()).all()
                return render_template('admin/mascotas.html', mascotas=mascotas)
             except Exception as e:
                db.session.rollback()
                print(f"DB Error: {e}")  # Terminal debug
                flash('Error cargando datos', 'error')
                return redirect(url_for('home'))
            """
            Muestra el panel principal de administración
            Lista solicitudes de adopción y reportes de maltrato
            Solo accesible para administradores
            """
            cursor = self.conexion.get_cursor()

            # Obtener solicitudes pendientes y en proceso
            query_solicitudes = """
                SELECT s.id, u.nombre AS usuario_nombre, m.nombre AS mascota_nombre,
                       s.fecha_solicitud, s.estado_solicitud
                FROM solicitudes_adopcion s
                JOIN usuarios u ON s.id_usuario = u.id
                JOIN mascotas m ON s.id_mascota = m.id
                WHERE TRIM(LOWER(s.estado_solicitud)) IN ('pendiente', 'en proceso')
                ORDER BY s.fecha_solicitud DESC
            """
            cursor.execute(query_solicitudes)
            solicitudes = cursor.fetchall()

            # Obtener todos los reportes
            cursor.execute("SELECT * FROM reportes ORDER BY fecha_reporte DESC")
            reportes = cursor.fetchall()

            cursor.close()
            return render_template('admin/admin_panel.html', solicitudes=solicitudes, reportes=reportes)

        @self.app.route('/admin/detalle_solicitud/<int:solicitud_id>')
        @self.admin_required
        def detalle_solicitud(solicitud_id):
            """
            Muestra los detalles completos de una solicitud de adopción
            Incluye información del usuario y la mascota

            Args:
                solicitud_id: ID de la solicitud
            """
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
            return redirect(url_for('admin_panel'))

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
                return redirect(url_for('admin_panel'))

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

                flash(f'La solicitud ha sido marcada como \"{respuesta}\".', 'success')
                return redirect(url_for('admin_panel'))

            except Exception as e:
                flash(f'Ocurrió un error de base de datos: {e}', 'danger')
                return redirect(url_for('admin_panel'))

        @self.app.route('/admin/reporte/<int:reporte_id>')
        @self.admin_required
        def detalle_reporte(reporte_id):
            """
            Muestra los detalles completos de un reporte de maltrato

            Args:
                reporte_id: ID del reporte
            """
            cursor = self.conexion.get_cursor()
            cursor.execute("SELECT * FROM reportes WHERE id = %s", [reporte_id])
            reporte = cursor.fetchone()
            cursor.close()

            if not reporte:
                flash('El reporte no fue encontrado.', 'warning')
                return redirect(url_for('admin_panel'))

            return render_template('admin/detalle_reporte.html', reporte=reporte)

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
                flash('El reporte ha sido marcado como resuelto.', 'success')
            except Exception as e:
                flash(f'Error al actualizar el reporte: {e}', 'danger')
            return redirect(url_for('admin_panel'))

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
                        print(f"No se pudo eliminar el archivo de imagen: {e}")

                # Eliminar reporte de BD
                cursor.execute("DELETE FROM reportes WHERE id = %s", [reporte_id])
                self.conexion.commit()
                cursor.close()

                flash('El reporte ha been eliminado correctamente.', 'success')
            except Exception as e:
                flash(f'Error al eliminar el reporte: {e}', 'danger')
            return redirect(url_for('admin_panel'))

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
                    """, (nombre, especie, raza, edad, sexo, descripcion, foto_url, 'Disponible'))

                    self.conexion.commit()
                    cursor.close()

                    flash('Mascota agregada correctamente.', 'success')
                    return redirect(url_for('admin_panel'))

                except Exception as e:
                    print(f"\n=== DEBUG ERROR: Traceback completo ===")
                    traceback.print_exc()
                    print(f"=== Fin del error ===\n")
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
