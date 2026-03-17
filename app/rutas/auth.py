"""
Módulo de rutas para autenticación
Contiene las rutas de registro, login, perfil y gestión de usuarios
"""

import re
import random
import string
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask import render_template, request, redirect, url_for, session, flash, g
from app.rutas.decoradores import admin_required_factory


class RutasAuth:
    """
    Gestiona rutas de autenticación y perfil:
    - Registro (/registro)
    - Login (/login)
    - Logout (/logout)
    - Verificación de email (/verificar_email)
    - Perfil de usuario (/perfil)
    - Edición de perfil (/editar_perfil)
    - Cambio de contraseña (/cambiar_password)
    """

    def __init__(self, app, conexion):
        """
        Inicializa las rutas de autenticación

        Args:
            app: Instancia de Flask
            conexion: Instancia de Conexion
        """
        self.app = app
        self.conexion = conexion
        self.mysql = conexion.mysql
        self.bcrypt = conexion.bcrypt
        self.admin_required = admin_required_factory(app)
        # Credenciales de correo desde variables de entorno
        self.REMITENTE = "almasconcola@gmail.com"
        self.CONTRASENA_APP = "bdtz hpjl ugpf spzs"
        self.registrar_rutas()

    def registrar_rutas(self):
        """Registra todas las rutas de autenticación"""

        @self.app.route('/registro', methods=['GET', 'POST'])
        def registro():
            """
            GET: Muestra formulario de registro
            POST: Procesa el registro de nuevo usuario
            Validaciones: email único, formato válido, contraseña fuerte
            """
            msg = ''
            if request.method == 'POST':
                nombre = request.form.get('nombre')
                email = request.form.get('email')
                password = request.form.get('password')
                confirmar_password = request.form.get('confirmar_password')

                # Obtener usuario existente con este email
                cur = self.conexion.get_cursor()
                cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
                cuenta = cur.fetchone()

                # Validaciones del registro
                if cuenta:
                    msg = '¡La cuenta de correo electrónico ya existe!'
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                    msg = '¡Dirección de correo electrónico no válida!'
                elif password != confirmar_password:
                    msg = '¡Las contraseñas no coinciden!'
                # Requerimientos de contraseña: 8+ chars, número y símbolo especial
                elif len(password) < 8 or not re.search(r"[0-9]", password) or not re.search(r"[!@#$%^&*()-_=+{};:,<.>]", password):
                    msg = 'La contraseña debe tener al menos 8 caracteres, un número y un símbolo especial.'
                else:
                    # Crear nuevo usuario
                    hash_password = self.bcrypt.generate_password_hash(password).decode('utf-8')
                    cur.execute('INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)',
                                (nombre, email, hash_password, 'user'))
                    self.conexion.commit()

                    # Obtener ID del nuevo usuario
                    cur.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
                    nuevo_usuario = cur.fetchone()
                    id_usuario = nuevo_usuario['id']

                    # Generar código de verificación de 6 caracteres
                    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    cur.execute('INSERT INTO verificaciones (id_usuario, codigo, fecha_creacion, usado) VALUES (%s, %s, NOW(), %s)',
                                (id_usuario, codigo, False))
                    self.conexion.commit()

                    # Enviar correo de verificación
                    self._enviar_correo_verificacion(email, nombre, codigo)
                    flash('¡Te has registrado exitosamente! Se ha enviado un correo de verificación.', 'success')
                    cur.close()
                    return redirect(url_for('verificar_email'))

                cur.close()
            return render_template('auth/registro.html', msg=msg)

        @self.app.route('/verificar_email', methods=['GET', 'POST'])
        def verificar_email():
            """
            GET: Muestra formulario para ingresar código de verificación
            POST: Verifica el código y activa la cuenta
            """
            msg = ''
            if request.method == 'POST':
                email = request.form.get('email')
                codigo = request.form.get('codigo')

                cur = self.conexion.get_cursor()
                cur.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
                usuario = cur.fetchone()

                if not usuario:
                    msg = 'Correo no registrado.'
                else:
                    # Buscar verificación pendiente con ese código
                    cur.execute('SELECT * FROM verificaciones WHERE id_usuario = %s AND codigo = %s AND usado = FALSE',
                                (usuario['id'], codigo))
                    verificacion = cur.fetchone()

                    if verificacion:
                        # Marcar verificación como usada
                        cur.execute('UPDATE verificaciones SET usado = TRUE WHERE id = %s', (verificacion['id'],))
                        self.conexion.commit()
                        flash('¡Cuenta verificada exitosamente! Ahora puedes iniciar sesión.', 'success')
                        cur.close()
                        return redirect(url_for('login'))
                    else:
                        msg = 'Código incorrecto o ya usado.'
                cur.close()
            return render_template('auth/verificar_email.html', msg=msg)

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """
            GET: Muestra formulario de login
            POST: Autentica usuario y crea sesión
            """
            msg = ''
            # Si ya está logueado, redirigir a home
            if 'loggedin' in session:
                return redirect(url_for('home'))

            if request.method == 'POST':
                email = request.form.get('email')
                password = request.form.get('password')

                cur = self.conexion.get_cursor()
                cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
                cuenta = cur.fetchone()

                # Verificar credenciales y que email esté verificado
                if cuenta and self.bcrypt.check_password_hash(cuenta['password'], password):
                    cur.execute('SELECT * FROM verificaciones WHERE id_usuario = %s AND usado = FALSE', (cuenta['id'],))
                    pendiente = cur.fetchone()
                    if pendiente:
                        msg = 'Debes verificar tu cuenta antes de iniciar sesión.'
                    else:
                        # Crear sesión del usuario
                        session['loggedin'] = True
                        session['id'] = cuenta['id']
                        session['nombre'] = cuenta['nombre']
                        session['rol'] = cuenta['rol']
                        flash(f"¡Bienvenido de vuelta, {session['nombre']}!", 'success')
                        cur.close()
                        return redirect(url_for('home'))
                else:
                    msg = '¡Correo electrónico o contraseña incorrectos!'
                cur.close()
            return render_template('auth/login.html', msg=msg)

        @self.app.route('/logout')
        def logout():
            """Cierra la sesión del usuario"""
            session.clear()
            flash('Has cerrado sesión exitosamente.', 'info')
            return redirect(url_for('home'))

        @self.app.route('/perfil')
        def perfil():
            """
            Muestra el perfil del usuario logueado con sus solicitudes de adopción
            Requiere que el usuario esté autenticado
            """
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para ver tu perfil.', 'warning')
                return redirect(url_for('login'))

            user_id = session['id']
            cursor = self.conexion.get_cursor()

            # Obtener datos básicos del usuario
            cursor.execute('SELECT nombre, email, fecha_registro FROM usuarios WHERE id = %s', [user_id])
            usuario = cursor.fetchone()

            # Obtener solicitudes de adopción del usuario
            cursor.execute('''
                SELECT s.id, s.fecha_solicitud, s.estado_solicitud, m.nombre as mascota_nombre, m.foto_url as mascota_foto
                FROM solicitudes_adopcion s
                JOIN mascotas m ON s.id_mascota = m.id
                WHERE s.id_usuario = %s
                ORDER BY s.fecha_solicitud DESC
            ''', [user_id])
            solicitudes = cursor.fetchall()
            cursor.close()

            return render_template('usuario/perfil.html', usuario=usuario, solicitudes=solicitudes)

        @self.app.route('/editar_perfil', methods=['GET', 'POST'])
        def editar_perfil():
            """
            GET: Muestra formulario para editar perfil
            POST: Actualiza datos del perfil (nombre, email, foto, contraseña)
            """
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para editar tu perfil.', 'warning')
                return redirect(url_for('login'))

            user_id = session['id']
            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
            usuario = cursor.fetchone()

            if request.method == 'POST':
                nombre = request.form.get('nombre')
                email = request.form.get('email')
                password_actual = request.form.get('password_actual')
                password_nueva = request.form.get('password_nueva')
                password_confirm = request.form.get('password_confirm')
                foto_file = request.files.get('foto_perfil')

                # Procesar foto de perfil si se subió
                if foto_file and foto_file.filename != '':
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    extension = foto_file.filename.rsplit('.', 1)[1].lower()
                    if extension not in allowed_extensions:
                        flash('Solo se permiten imágenes (png, jpg, jpeg, gif)', 'danger')
                        return redirect(url_for('editar_perfil'))

                    # Generar nombre único para la foto
                    import uuid
                    filename = f"{uuid.uuid4().hex}.{extension}"
                    upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads', 'perfiles')

                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)

                    filepath = os.path.join('app/static/uploads/perfiles/', filename)
                    foto_file.save(filepath)
                    usuario['foto_perfil'] = filename

                    # Actualizar foto en BD
                    cursor.execute('UPDATE usuarios SET foto_perfil=%s WHERE id=%s', (filename, user_id))
                    self.conexion.commit()

                # Validaciones de actualización
                errores = []

                if not nombre or not email:
                    errores.append("El nombre y correo son obligatorios.")

                # Verificar si quiere cambiar contraseña
                cambiar_password = password_nueva and password_actual

                if cambiar_password:
                    if not self.bcrypt.check_password_hash(usuario['password'], password_actual):
                        errores.append("La contraseña actual no es correcta.")
                    elif password_nueva != password_confirm:
                        errores.append("La nueva contraseña no coincide con la confirmación.")
                    elif len(password_nueva) < 8:
                        errores.append("La nueva contraseña debe tener al menos 8 caracteres.")

                # Si no hay errores, guardar cambios
                if errores:
                    for e in errores:
                        flash(e, "danger")
                else:
                    # Actualizar nombre y email
                    cursor.execute('UPDATE usuarios SET nombre=%s, email=%s WHERE id=%s', (nombre, email, user_id))
                    self.conexion.commit()
                    session['nombre'] = nombre

                    # Actualizar contraseña si se cambió
                    if cambiar_password:
                        hashed_password = self.bcrypt.generate_password_hash(password_nueva).decode('utf-8')
                        cursor.execute('UPDATE usuarios SET password=%s WHERE id=%s', (hashed_password, user_id))
                        self.conexion.commit()

                    flash("¡Perfil actualizado correctamente!", "success")
                    cursor.close()
                    return redirect(url_for('editar_perfil'))

            return render_template('usuario/editar_perfil.html', usuario=usuario)

        @self.app.route('/cambiar_password', methods=['POST'])
        def cambiar_password():
            """
            Endpoint POST para cambiar contraseña desde el perfil
            Valida contraseña actual y que nuevas contraseñas coincidan
            """
            if 'loggedin' not in session:
                return redirect(url_for('login'))

            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Validar que las nuevas contraseñas coincidan
            if new_password != confirm_password:
                flash('Las nuevas contraseñas no coinciden.', 'danger')
                return redirect(url_for('perfil'))

            # Verificar contraseña actual
            cursor = self.conexion.get_cursor()
            cursor.execute('SELECT password FROM usuarios WHERE id = %s', [session['id']])
            user = cursor.fetchone()

            if user and self.bcrypt.check_password_hash(user['password'], current_password):
                # Cambiar contraseña
                new_hash_password = self.bcrypt.generate_password_hash(new_password).decode('utf-8')
                cursor.execute('UPDATE usuarios SET password = %s WHERE id = %s', (new_hash_password, session['id']))
                self.conexion.commit()
                flash('¡Contraseña actualizada exitosamente!', 'success')
            else:
                flash('La contraseña actual es incorrecta.', 'danger')
            cursor.close()
            return redirect(url_for('perfil'))

        @self.app.route('/eliminar_cuenta')
        def eliminar_cuenta():
            """
            Endpoint para eliminar cuenta (aún en construcción)
            """
            flash('La funcionalidad para eliminar la cuenta aún está en construcción.', 'info')
            return redirect(url_for('perfil'))

    def _enviar_correo_verificacion(self, email, nombre, codigo):
        """
        Envía correo de verificación al usuario registrado

        Args:
            email: Email del usuario
            nombre: Nombre del usuario
            codigo: Código de verificación
        """
        try:
            # Crear mensaje de correo
            asunto = "Código de verificación de tu cuenta"
            mensaje = MIMEMultipart()
            mensaje['From'] = self.REMITENTE
            mensaje['To'] = email
            mensaje['Subject'] = asunto

            # Usar plantilla HTML para el correo
            cuerpo_html = render_template('auth/correo_verificacion.html', nombre=nombre, codigo=codigo)
            mensaje.attach(MIMEText(cuerpo_html, 'html'))

            # Adjuntar logo de la fundación
            with open("app/static/images/logo.jpg", "rb") as f:
                imagen = MIMEImage(f.read())
                imagen.add_header('Content-ID', '<logo_fundacion>')
                imagen.add_header('Content-Disposition', 'inline', filename="logo.jpg")
                mensaje.attach(imagen)

            # Enviar correo
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.REMITENTE, self.CONTRASENA_APP)
            server.sendmail(self.REMITENTE, email, mensaje.as_string())
            server.quit()

        except Exception as e:
            print(f"Error al enviar correo: {e}")
            flash(f'Error al enviar el correo de verificación: {e}', 'danger')
