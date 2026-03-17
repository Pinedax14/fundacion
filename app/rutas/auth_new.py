"""
Módulo de rutas para autenticación (refactorizado con SQLAlchemy ORM)
Contiene las rutas de registro, login, perfil y gestión de usuarios
"""

import re
import random
import string
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from app.models import db, Usuario, VerificacionEmail
from datetime import datetime, timedelta

bcrypt = Bcrypt()

def registrar_rutas_auth(app):
    """
    Registra todas las rutas de autenticación usando SQLAlchemy ORM
    """
    
    # Credenciales de correo
    REMITENTE = os.getenv("EMAIL_USER", "almasconcola@gmail.com")
    CONTRASENA_APP = os.getenv("EMAIL_PASSWORD", "bdtz hpjl ugpf spzs")
    
    def enviar_correo_verificacion(email, nombre, codigo):
        """Envía correo de verificación"""
        try:
            mensaje = MIMEMultipart('alternative')
            mensaje['Subject'] = "Verifica tu cuenta"
            mensaje['From'] = REMITENTE
            mensaje['To'] = email
            
            html = f"""
            <html>
                <body>
                    <h2>Bienvenido a Almas con Cola, {nombre}!</h2>
                    <p>Tu código de verificación es: <strong>{codigo}</strong></p>
                    <p>Ingresa este código en nuestra plataforma para verificar tu cuenta.</p>
                </body>
            </html>
            """
            
            parte_html = MIMEText(html, 'html')
            mensaje.attach(parte_html)
            
            servidor = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            servidor.login(REMITENTE, CONTRASENA_APP)
            servidor.send_message(mensaje)
            servidor.quit()
            return True
        except Exception as e:
            app.logger.error(f"Error enviando correo: {e}")
            return False

    @app.route('/registro', methods=['GET', 'POST'])
    def registro():
        """
        GET: Muestra formulario de registro
        POST: Procesa el registro de nuevo usuario
        """
        msg = ''
        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirmar_password = request.form.get('confirmar_password', '')

            # Validaciones
            usuario_existente = Usuario.query.filter_by(email=email).first()
            
            if usuario_existente:
                msg = 'La cuenta de correo electrónico ya existe!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Dirección de correo electrónico no válida!'
            elif password != confirmar_password:
                msg = 'Las contraseñas no coinciden!'
            elif len(password) < 8:
                msg = 'La contraseña debe tener al menos 8 caracteres.'
            elif not re.search(r"[0-9]", password):
                msg = 'La contraseña debe contener al menos un número.'
            elif not re.search(r"[!@#$%^&*()-_=+{};:,<.>]", password):
                msg = 'La contraseña debe contener al menos un símbolo especial.'
            else:
                try:
                    # Crear nuevo usuario
                    hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
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
                    
                    # Enviar correo
                    enviar_correo_verificacion(email, nombre, codigo)
                    flash('Te has registrado exitosamente! Se ha enviado un correo de verificación.', 'success')
                    return redirect(url_for('verificar_email'))
                    
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error en registro: {e}")
                    msg = 'Error durante el registro. Intenta de nuevo.'
        
        return render_template('auth/registro.html', msg=msg)

    @app.route('/verificar_email', methods=['GET', 'POST'])
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
                # Buscar verificación pendiente
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
                        flash('Cuenta verificada exitosamente! Ahora puedes iniciar sesión.', 'success')
                        return redirect(url_for('login'))
                else:
                    msg = 'Código incorrecto o ya usado.'
        
        return render_template('auth/verificar_email.html', msg=msg)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        GET: Muestra formulario de login
        POST: Autentica usuario y crea sesión
        """
        msg = ''
        
        # Si ya está logueado, redirigir
        if 'usuario_id' in session:
            return redirect(url_for('home'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and bcrypt.check_password_hash(usuario.password, password):
                # Verificar que email esté verificado
                if not usuario.verified:
                    msg = 'Debes verificar tu cuenta antes de iniciar sesión.'
                else:
                    # Crear sesión
                    session['usuario_id'] = usuario.id
                    session['usuario_nombre'] = usuario.nombre
                    session['usuario_rol'] = usuario.rol
                    flash(f"Bienvenido de vuelta, {usuario.nombre}!", 'success')
                    return redirect(url_for('home'))
            else:
                msg = 'Correo electrónico o contraseña incorrectos!'
        
        return render_template('auth/login.html', msg=msg)

    @app.route('/logout')
    def logout():
        """Cierra la sesión del usuario"""
        session.clear()
        flash('Has cerrado sesión exitosamente.', 'info')
        return redirect(url_for('home'))

    @app.route('/perfil')
    def perfil():
        """
        Muestra el perfil del usuario logueado con sus solicitudes de adopción
        """
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para ver tu perfil.', 'warning')
            return redirect(url_for('login'))

        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            session.clear()
            return redirect(url_for('login'))
        
        solicitudes = usuario.solicitudes_adopcion
        
        return render_template('usuario/perfil.html', usuario=usuario, solicitudes=solicitudes)

    @app.route('/editar_perfil', methods=['GET', 'POST'])
    def editar_perfil():
        """
        GET: Muestra formulario de edición de perfil
        POST: Actualiza los datos del usuario
        """
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('login'))

        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            session.clear()
            return redirect(url_for('login'))

        msg = ''
        if request.method == 'POST':
            try:
                nombre = request.form.get('nombre', '').strip()
                
                if not nombre:
                    msg = 'El nombre no puede estar vacío.'
                else:
                    usuario.nombre = nombre
                    db.session.commit()
                    session['usuario_nombre'] = nombre
                    flash('Perfil actualizado exitosamente!', 'success')
                    return redirect(url_for('perfil'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error actualizando perfil: {e}")
                msg = 'Error actualizando el perfil.'
        
        return render_template('usuario/editar_perfil.html', usuario=usuario, msg=msg)

    @app.route('/cambiar_password', methods=['GET', 'POST'])
    def cambiar_password():
        """
        GET: Muestra formulario de cambio de contraseña
        POST: Actualiza la contraseña
        """
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('login'))

        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            session.clear()
            return redirect(url_for('login'))

        msg = ''
        if request.method == 'POST':
            password_actual = request.form.get('password_actual', '')
            password_nueva = request.form.get('password_nueva', '')
            confirmar_password = request.form.get('confirmar_password', '')

            # Verificar contraseña actual
            if not bcrypt.check_password_hash(usuario.password, password_actual):
                msg = 'La contraseña actual es incorrecta.'
            elif password_nueva != confirmar_password:
                msg = 'Las contraseñas nuevas no coinciden.'
            elif len(password_nueva) < 8:
                msg = 'La contraseña debe tener al menos 8 caracteres.'
            elif not re.search(r"[0-9]", password_nueva):
                msg = 'La contraseña debe contener al menos un número.'
            elif not re.search(r"[!@#$%^&*()-_=+{};:,<.>]", password_nueva):
                msg = 'La contraseña debe contener al menos un símbolo especial.'
            else:
                try:
                    hash_nueva = bcrypt.generate_password_hash(password_nueva).decode('utf-8')
                    usuario.password = hash_nueva
                    db.session.commit()
                    flash('Contraseña cambida exitosamente!', 'success')
                    return redirect(url_for('perfil'))
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error cambiando contraseña: {e}")
                    msg = 'Error al cambiar la contraseña.'
        
        return render_template('usuario/cambiar_password.html', msg=msg)
