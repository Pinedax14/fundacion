"""
Módulo de rutas para mascotas
Contiene las rutas para listar, filtrar, ver detalles y solicitar adopción de mascotas
"""

from flask import render_template, request, redirect, url_for, session, flash


class RutasMascotas:
    """
    Gestiona rutas relacionadas con mascotas:
    - Listar mascotas (/mascotas)
    - Filtrar mascotas (/filtrar_mascotas)
    - Ver detalle de mascota (/mascota/<id>)
    - Solicitar adopción (/adoptar/<id>)
    - Eliminar solicitud (/eliminar_solicitud/<id>)
    - Cancelar solicitud (/cancelar_solicitud/<id>)
    """

    def __init__(self, app, conexion):
        """
        Inicializa las rutas de mascotas

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion
        """
        self.app = app
        self.conexion = conexion
        self.mysql = conexion.mysql
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas de mascotas"""

        @self.app.route('/mascotas')
        def mascotas():
            """
            Muestra el listado de todas las mascotas disponibles
            Ordena por estado (disponibles primero)
            """
            try:
                cursor = self.conexion.get_cursor()
                cursor.execute("SELECT id, nombre, estado, fecha_ingreso FROM mascotas ORDER BY estado ASC")
                lista_mascotas = cursor.fetchall()
                cursor.close()
                return render_template('mascotas/mascotas.html', mascotas=lista_mascotas)
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al cargar mascotas: {e}', 'danger')
                return render_template('mascotas/mascotas.html', mascotas=[])

        @self.app.route('/filtrar_mascotas', methods=['GET'])
        def filtrar_mascotas():
            """
            Filtra mascotas por especie, raza, edad y sexo
            Parámetros GET: especie, raza, edad, sexo
            """
            try:
                especie = request.args.get('especie')
                raza = request.args.get('raza')
                edad = request.args.get('edad')
                sexo = request.args.get('sexo')

                # Construir query dinámicamente según filtros
                sql_query = "SELECT * FROM mascotas WHERE 1=1"
                params = []

                if especie:
                    sql_query += " AND especie = %s"
                    params.append(especie)

                if raza:
                    sql_query += " AND raza LIKE %s"
                    params.append(f"%{raza}%")

                if edad:
                    sql_query += " AND edad = %s"
                    params.append(edad)

                if sexo:
                    sql_query += " AND sexo = %s"
                    params.append(sexo)

                # Ejecutar query
                cur = self.conexion.get_cursor()
                cur.execute(sql_query, params)
                mascotas_filtradas = cur.fetchall()

                # Convertir resultados a diccionarios si es necesario
                column_names = [desc[0] for desc in cur.description] if cur.description else []
                cur.close()

                lista_de_mascotas = []
                for row in mascotas_filtradas:
                    lista_de_mascotas.append(dict(zip(column_names, row)))

                return render_template('mascotas/mascotas.html', mascotas=lista_de_mascotas)
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al filtrar mascotas: {e}', 'danger')
                return render_template('mascotas/mascotas.html', mascotas=[])

        @self.app.route('/mascota/<int:mascota_id>')
        def detalle_mascota(mascota_id):
            """
            Muestra los detalles de una mascota específica

            Args:
                mascota_id: ID de la mascota
            """
            try:
                cursor = self.conexion.get_cursor()
                cursor.execute('SELECT * FROM mascotas WHERE id = %s', [mascota_id])
                mascota = cursor.fetchone()
                cursor.close()

                if mascota:
                    return render_template('mascotas/detalle_mascota.html', mascota=mascota)
                return 'Mascota no encontrada', 404
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al cargar mascota: {e}', 'danger')
                return redirect(url_for('mascotas'))

        @self.app.route('/adoptar/<int:mascota_id>', methods=['GET', 'POST'])
        def solicitar_adopcion(mascota_id):
            """
            GET: Muestra formulario para solicitar adopción
            POST: Procesa la solicitud de adopción
            Requiere que el usuario esté autenticado
            """
            # Verificar que el usuario esté logueado
            if 'loggedin' not in session:
                flash('Es necesario iniciar sesión para poder adoptar.', 'danger')
                return redirect(url_for('login'))

            try:
                cursor = self.conexion.get_cursor()
                cursor.execute('SELECT * FROM mascotas WHERE id = %s', [mascota_id])
                mascota = cursor.fetchone()

                # Validar que la mascota existe y está disponible
                if not mascota or mascota['estado'] != 'Disponible':
                    flash('Esta mascota no está disponible para adopción.', 'warning')
                    return redirect(url_for('mascotas'))

                if request.method == 'POST':
                    # Obtener datos del formulario
                    id_usuario = session['id']
                    direccion = request.form.get('direccion')
                    telefono = request.form.get('telefono')
                    ingresos = request.form.get('ingresos')
                    estrato = request.form.get('estrato')
                    mensaje = request.form.get('mensaje')

                    # Guardar solicitud de adopción
                    from datetime import datetime
                    cursor.execute('''
                        INSERT INTO solicitudes_adopcion
                        (id_usuario, id_mascota, fecha_solicitud, estado_solicitud, mensaje, direccion, telefono, ingresos, estrato_social)
                        VALUES (%s, %s, %s, 'pendiente', %s, %s, %s, %s, %s)
                    ''', (id_usuario, mascota_id, datetime.utcnow(), mensaje, direccion, telefono, ingresos, estrato))

                    # Cambiar estado de la mascota a "En proceso"
                    cursor.execute("UPDATE mascotas SET estado = 'En proceso' WHERE id = %s", [mascota_id])
                    self.conexion.commit()
                    cursor.close()

                    flash('¡Tu solicitud de adopción ha sido enviada con éxito!', 'success')
                    return redirect(url_for('mascotas'))

                cursor.close()
                return render_template('mascotas/solicitud_adopcion.html', mascota=mascota)
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al procesar solicitud de adopción: {e}', 'danger')
                return redirect(url_for('mascotas'))

        @self.app.route('/eliminar_solicitud/<int:solicitud_id>')
        def eliminar_solicitud(solicitud_id):
            """
            Elimina una solicitud de adopción rechazada
            Solo el propietario de la solicitud puede eliminarla
            """
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para realizar esta acción.', 'warning')
                return redirect(url_for('login'))

            try:
                user_id = session['id']
                cursor = self.conexion.get_cursor()
                cursor.execute('SELECT estado_solicitud FROM solicitudes_adopcion WHERE id = %s AND id_usuario = %s',
                             (solicitud_id, user_id))
                solicitud = cursor.fetchone()

                # Validar que la solicitud existe y pertenece al usuario
                if not solicitud:
                    flash('Solicitud no encontrada o no pertenece al usuario.', 'danger')
                    cursor.close()
                    return redirect(url_for('perfil'))

                # Solo se pueden eliminar solicitudes rechazadas
                if solicitud['estado_solicitud'].lower() != 'rechazada':
                    flash('Solo puedes eliminar solicitudes rechazadas.', 'warning')
                    cursor.close()
                    return redirect(url_for('perfil'))

                # Eliminar solicitud
                cursor.execute('DELETE FROM solicitudes_adopcion WHERE id = %s', [solicitud_id])
                self.conexion.commit()
                cursor.close()

                flash('Solicitud rechazada eliminada correctamente.', 'success')
                return redirect(url_for('perfil'))
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al eliminar solicitud: {e}', 'danger')
                return redirect(url_for('perfil'))

        @self.app.route('/cancelar_solicitud/<int:solicitud_id>')
        def cancelar_solicitud(solicitud_id):
            """
            Cancela una solicitud de adopción en proceso
            Libera la mascota para que otros usuarios puedan adoptarla
            """
            if 'loggedin' not in session:
                return redirect(url_for('login'))

            try:
                cursor = self.conexion.get_cursor()
                cursor.execute('SELECT id_mascota FROM solicitudes_adopcion WHERE id = %s AND id_usuario = %s',
                             (solicitud_id, session['id']))
                solicitud = cursor.fetchone()

                if solicitud:
                    # Obtener ID de la mascota y cambiar su estado a disponible
                    id_mascota = solicitud['id_mascota']
                    cursor.execute("UPDATE mascotas SET estado = 'Disponible' WHERE id = %s", [id_mascota])
                    # Eliminar la solicitud
                    cursor.execute('DELETE FROM solicitudes_adopcion WHERE id = %s', [solicitud_id])
                    self.conexion.commit()
                    flash('Tu solicitud de adopción ha sido cancelada.', 'success')
                else:
                    flash('No se pudo cancelar la solicitud.', 'danger')

                cursor.close()
                return redirect(url_for('perfil'))
            except Exception as e:
                self.conexion.rollback()
                flash(f'Error al cancelar solicitud: {e}', 'danger')
                return redirect(url_for('perfil'))
