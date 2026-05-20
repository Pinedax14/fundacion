"""
Módulo de rutas para mascotas
Contiene las rutas para listar, filtrar, ver detalles y solicitar adopción de mascotas
"""

from flask import render_template, request, redirect, url_for, session, flash
from app.services.admin_data_service import AdminDataStructureService
import re


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
        self.admin_data_service = AdminDataStructureService()
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas de mascotas"""

        @self.app.route('/mascotas')
        def mascotas():
            """
            Muestra el listado de todas las mascotas disponibles
            Carga mascotas en LinkedList para procesamiento en memoria
            """
            try:
                # Cargar mascotas en LinkedList
                mascotas_linkedlist = self.admin_data_service.cargar_mascotas_en_linkedlist()
                
                # Convertir a lista para template
                lista_mascotas = mascotas_linkedlist.to_list()
                
                print(f"DEBUG: Cargadas {len(lista_mascotas)} mascotas en LinkedList")
                
                return render_template('mascotas/mascotas.html', mascotas=lista_mascotas)
            except Exception as e:
                flash(f'Error al cargar mascotas: {e}', 'danger')
                print(f"ERROR en mascotas: {e}")
                return render_template('mascotas/mascotas.html', mascotas=[])

        @self.app.route('/filtrar_mascotas', methods=['GET'])
        def filtrar_mascotas():
            """
            Filtra mascotas por especie, raza, edad y sexo
            Carga todas las mascotas en LinkedList y filtra en memoria
            Parámetros GET: especie, raza, edad, sexo
            """
            try:
                # Obtener parámetros de filtro
                especie = request.args.get('especie', '').strip().lower()
                raza = request.args.get('raza', '').strip().lower()
                edad = request.args.get('edad', '').strip()
                sexo = request.args.get('sexo', '').strip().upper()

                # Cargar todas las mascotas en LinkedList
                mascotas_linkedlist = self.admin_data_service.cargar_mascotas_en_linkedlist()
                mascotas_disponibles = mascotas_linkedlist.to_list()

                # Filtrar en memoria
                mascotas_filtradas = []
                for mascota in mascotas_disponibles:
                    coincide = True
                    
                    if especie and mascota.get('especie', '').lower() != especie:
                        coincide = False
                    
                    if coincide and raza and raza not in mascota.get('raza', '').lower():
                        coincide = False
                    
                    if coincide and edad and str(mascota.get('edad', '')) != edad:
                        coincide = False
                    
                    if coincide and sexo and mascota.get('sexo', '').upper() != sexo:
                        coincide = False
                    
                    if coincide:
                        mascotas_filtradas.append(mascota)

                print(f"DEBUG: Cargadas {len(mascotas_disponibles)} mascotas, filtradas a {len(mascotas_filtradas)}")

                return render_template('mascotas/mascotas.html', mascotas=mascotas_filtradas)
            except Exception as e:
                flash(f'Error al filtrar mascotas: {e}', 'danger')
                print(f"ERROR en filtrar_mascotas: {e}")
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
                    ingresos_raw = request.form.get('ingresos', '').strip()
                    estrato_raw = request.form.get('estrato', '').strip()
                    mensaje = request.form.get('mensaje')

                    # Validar ingresos como rango válido
                    ingresos_rangos_validos = [
                        '1000000-2000000',
                        '2000000-3000000',
                        '3000000-4000000',
                        '4000000-5000000',
                        '5000000-6000000',
                        '6000000-7000000',
                        '7000000-8000000',
                        '8000000-9000000',
                        '9000000-10000000',
                        '10000000+'
                    ]
                    try:
                        if not ingresos_raw or ingresos_raw not in ingresos_rangos_validos:
                            raise ValueError('Debes seleccionar un rango de ingresos válido.')
                        ingresos = ingresos_raw
                    except ValueError as err:
                        flash(str(err), 'danger')
                        cursor.close()
                        return redirect(url_for('solicitar_adopcion', mascota_id=mascota_id))

                    try:
                        if not estrato_raw or not re.fullmatch(r'\d+', estrato_raw):
                            raise ValueError('El estrato social debe ser un número entero.')
                        estrato = int(estrato_raw)
                        if estrato < 1 or estrato > 6:
                            raise ValueError('El estrato social debe estar entre 1 y 6.')
                    except ValueError as err:
                        flash(str(err), 'danger')
                        cursor.close()
                        return redirect(url_for('solicitar_adopcion', mascota_id=mascota_id))

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
