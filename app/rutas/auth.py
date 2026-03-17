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
from app.models import db, Usuario, VerificacionEmail, SolicitudAdopcion, Mascota
from datetime import datetime, timedelta


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
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password')
                confirmar_password = request.form.get('confirmar_password')

                # Obtener usuario existente con este email (usando ORM)
                cuenta = Usuario.query.filter_by(email=email).first()

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
                    try:
                        # Crear nuevo usuario
                        hash_password = self.bcrypt.generate_password_hash(password).decode('utf-8')
                        nuevo_usuario = Usuario(
                            nombre=nombre,
                            email=email,
                            password=hash_password,
                            rol='user'
                        )
                        db.session.add(nuevo_usuario)
                        db.session.commit()

                        # Generar código de verificación
                        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                        fecha_expiracion = datetime.utcnow() + timedelta(hours=24)
                        
                        verificacion = VerificacionEmail(
                            usuario_id=nuevo_usuario.id,
                            codigo=codigo,
                            fecha_expiracion=fecha_expiracion
                        )
                        db.session.add(verificacion)
                        db.session.commit()

                        # Enviar correo de verificación
                        self._enviar_correo_verificacion(email, nombre, codigo)
                        flash('¡Te has registrado exitosamente! Se ha enviado un correo de verificación.', 'success')
                        return redirect(url_for('verificar_email'))
                    except Exception as e:
                        db.session.rollback()
                        self.app.logger.error(f"Error en registro: {e}")
                        msg = 'Error durante el registro. Intenta de nuevo.'
            
            return render_template('auth/registro.html', msg=msg)

        @self.app.route('/verificar_email', methods=['GET', 'POST'])
        def verificar_email():
            """
            GET: Muestra formulario para ingresar código de verificación
            POST: Verifica el código y activa la cuenta
            """
            msg = ''
            if request.method == 'POST':
                email = request.form.get('email', '').strip().lower()
                codigo = request.form.get('codigo', '').strip().upper()

                usuario = Usuario.query.filter_by(email=email).first()
                
                if not usuario:
                    msg = 'Correo no registrado.'
                else:
                    # Buscar verificación pendiente (usando ORM)
                    verificacion = VerificacionEmail.query.filter_by(
                        usuario_id=usuario.id,
                        codigo=codigo,
                        usado=False
                    ).first()

                    if verificacion:
                        # Verificar que no haya expirado
                        if datetime.utcnow() > verificacion.fecha_expiracion:
                            msg = 'El código ha expirado. Solicita uno nuevo.'
                        else:
                            # Marcar como verificado
                            verificacion.usado = True
                            usuario.verified = True
                            db.session.commit()
                            flash('¡Cuenta verificada exitosamente! Ahora puedes iniciar sesión.', 'success')
                            return redirect(url_for('login'))
                    else:
                        msg = 'Código incorrecto o ya usado.'
            
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
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password')

                # Buscar usuario por email (usando ORM)
                cuenta = Usuario.query.filter_by(email=email).first()

                # Verificar credenciales
                if cuenta and self.bcrypt.check_password_hash(cuenta.password, password):
                    # Verificar que email esté verificado
                    if not cuenta.verified:
                        msg = 'Debes verificar tu cuenta antes de iniciar sesión.'
                    else:
                        # Crear sesión del usuario
                        session['loggedin'] = True
                        session['id'] = cuenta.id
                        session['nombre'] = cuenta.nombre
                        session['usuario_id'] = cuenta.id
                        session['usuario_nombre'] = cuenta.nombre
                        session['usuario_rol'] = cuenta.rol
                        session['rol'] = cuenta.rol
                        flash(f"¡Bienvenido de vuelta, {session['nombre']}!", 'success')
                        return redirect(url_for('home'))
                else:
                    msg = '¡Correo electrónico o contraseña incorrectos!'
            
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

            user_id = session.get('usuario_id') or session.get('id')

            # Obtener datos básicos del usuario (usando ORM)
            usuario = Usuario.query.get(user_id)
            
            if not usuario:
                flash('Usuario no encontrado.', 'warning')
                return redirect(url_for('login'))

            # Obtener solicitudes de adopción del usuario (usando ORM con joins)
            solicitudes = db.session.query(
                SolicitudAdopcion.id,
                SolicitudAdopcion.fecha_solicitud,
                SolicitudAdopcion.estado,
                Mascota.nombre.label('mascota_nombre'),
                Mascota.foto_url.label('mascota_foto')
            ).join(Mascota).filter(
                SolicitudAdopcion.usuario_id == user_id
            ).order_by(
                db.desc(SolicitudAdopcion.fecha_solicitud)
            ).all()

            # Convert to dict-like format for template compatibility
            solicitudes_formatted = []
            for solicitud in solicitudes:
                solicitudes_formatted.append({
                    'id': solicitud[0],
                    'fecha_solicitud': solicitud[1],
                    'estado_solicitud': solicitud[2],
                    'mascota_nombre': solicitud[3],
                    'mascota_foto': solicitud[4]
                })

            # Convert usuario to dict for template
            usuario_dict = {
                'nombre': usuario.nombre,
                'email': usuario.email,
                'fecha_registro': usuario.fecha_registro
            }

            return render_template('usuario/perfil.html', usuario=usuario_dict, solicitudes=solicitudes_formatted)

        @self.app.route('/editar_perfil', methods=['GET', 'POST'])
        def editar_perfil():
            """
            GET: Muestra formulario para editar perfil
            POST: Actualiza datos del perfil (nombre, email, foto, contraseña)
            """
            if 'loggedin' not in session:
                flash('Debes iniciar sesión para editar tu perfil.', 'warning')
                return redirect(url_for('login'))

            user_id = session.get('usuario_id') or session.get('id')
            usuario_orm = Usuario.query.get(user_id)
            
            if not usuario_orm:
                flash('Usuario no encontrado.', 'warning')
                return redirect(url_for('login'))

            # Convert ORM object to dict for template
            usuario = {
                'id': usuario_orm.id,
                'nombre': usuario_orm.nombre,
                'email': usuario_orm.email,
                'password': usuario_orm.password,
                'foto_perfil': getattr(usuario_orm, 'foto_perfil', None)
            }

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
                    filename_parts = foto_file.filename.rsplit('.', 1)
                    if len(filename_parts) > 1:
                        extension = filename_parts[1].lower()
                        if extension not in allowed_extensions:
                            flash('Solo se permiten imágenes (png, jpg, jpeg, gif)', 'danger')
                            return redirect(url_for('editar_perfil'))

                        # Generar nombre único para la foto
                        import uuid
                        filename = f"{uuid.uuid4().hex}.{extension}"
                        upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads', 'perfiles')

                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder)

                        filepath = os.path.join(upload_folder, filename)
                        foto_file.save(filepath)
                        usuario['foto_perfil'] = filename
                        usuario_orm.foto_perfil = filename

                # Validaciones de actualización
                errores = []

                if not nombre or not email:
                    errores.append("El nombre y correo son obligatorios.")

                # Verificar si quiere cambiar contraseña
                cambiar_password = password_nueva and password_actual

                if cambiar_password:
                    if not self.bcrypt.check_password_hash(usuario_orm.password, password_actual):
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
                    try:
                        # Actualizar nombre y email
                        usuario_orm.nombre = nombre
                        usuario_orm.email = email
                        
                        # Actualizar contraseña si se cambió
                        if cambiar_password:
                            usuario_orm.password = self.bcrypt.generate_password_hash(password_nueva).decode('utf-8')

                        db.session.commit()
                        session['nombre'] = nombre
                        session['usuario_nombre'] = nombre
                        flash("¡Perfil actualizado correctamente!", "success")
                        return redirect(url_for('editar_perfil'))
                    except Exception as e:
                        db.session.rollback()
                        self.app.logger.error(f"Error actualizando perfil: {e}")
                        flash("Error al actualizar el perfil.", "danger")

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

            # Obtener usuario (usando ORM)
            user_id = session.get('usuario_id') or session.get('id')
            usuario = Usuario.query.get(user_id)

            if not usuario:
                flash('Usuario no encontrado.', 'danger')
                return redirect(url_for('login'))

            # Verificar contraseña actual
            if usuario and self.bcrypt.check_password_hash(usuario.password, current_password):
                try:
                    # Cambiar contraseña
                    usuario.password = self.bcrypt.generate_password_hash(new_password).decode('utf-8')
                    db.session.commit()
                    flash('¡Contraseña actualizada exitosamente!', 'success')
                except Exception as e:
                    db.session.rollback()
                    self.app.logger.error(f"Error actualizando contraseña: {e}")
                    flash('Error al actualizar la contraseña.', 'danger')
            else:
                flash('La contraseña actual es incorrecta.', 'danger')
            
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
            with open("app/static/images/logos/logo.jpg", "rb") as f:
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
