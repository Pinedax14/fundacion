"""
Servicios de autenticación
Contiene la lógica de negocio de registro, login, verificación, etc.
"""

import re
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask import current_app, render_template
from flask_bcrypt import Bcrypt
from app.models import db, Usuario, VerificacionEmail


class AuthService:
    """Servicio de autenticación y gestión de usuarios"""
    
    def __init__(self):
        self.bcrypt = Bcrypt()
    
    @staticmethod
    def validar_email(email):
        """Valida el formato de un email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validar_contrasena(password):
        """
        Valida que la contraseña cumpla con requisitos de seguridad
        Retorna (es_valida, mensaje_error)
        """
        errors = []
        
        if len(password) < current_app.config['MIN_PASSWORD_LENGTH']:
            errors.append(f"Mínimo {current_app.config['MIN_PASSWORD_LENGTH']} caracteres")
        
        if current_app.config['REQUIRE_NUMBER'] and not re.search(r'\d', password):
            errors.append("Debe contener al menos un número")
        
        if current_app.config['REQUIRE_SPECIAL_CHAR'] and not re.search(r'[!@#$%^&*]', password):
            errors.append("Debe contener al menos un símbolo especial (!@#$%^&*)")
        
        if errors:
            return False, ", ".join(errors)
        return True, None
    
    def registrar_usuario(self, nombre, email, password, confirm_password):
        """
        Registra un nuevo usuario
        Retorna (éxito, usuario_o_error)
        """
        # Validaciones
        if not nombre or not email or not password:
            return False, "Todos los campos son requeridos"
        
        if not self.validar_email(email):
            return False, "Email no válido"
        
        if password != confirm_password:
            return False, "Las contraseñas no coinciden"
        
        # Validar contraseña
        valida, error = self.validar_contrasena(password)
        if not valida:
            return False, error
        
        # Verificar email único
        if Usuario.query.filter_by(email=email).first():
            return False, "El email ya está registrado"
        
        try:
            # Hash de contraseña
            password_hash = self.bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Crear usuario
            usuario = Usuario(
                nombre=nombre,
                email=email,
                password=password_hash,
                rol='user'
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            return True, usuario
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al registrar usuario: {str(e)}")
            return False, "Error al registrar el usuario"
    
    def verificar_usuario(self, email, password):
        """
        Verifica credenciales de login
        Retorna (éxito, usuario_o_error)
        """
        if not email or not password:
            return False, "Email y contraseña requeridos"
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            return False, "Email no encontrado"
        
        if not usuario.verified:
            return False, "Por favor verifica tu email primero"
        
        if not self.bcrypt.check_password_hash(usuario.password, password):
            return False, "Contraseña incorrecta"
        
        return True, usuario
    
    def generar_codigo_verificacion(self, usuario_id):
        """
        Genera código de verificación de 6 dígitos
        Retorna el código generado
        """
        try:
            # Limpiar códigos expirados
            fecha_expiracion_minima = datetime.utcnow() - timedelta(hours=1)
            VerificacionEmail.query.filter(
                VerificacionEmail.usuario_id == usuario_id,
                VerificacionEmail.fecha_creacion < fecha_expiracion_minima
            ).delete()
            db.session.commit()
            
            # Generar nuevo código
            codigo = str(secrets.randbelow(1000000)).zfill(6)
            
            # Guardar verificación
            verificacion = VerificacionEmail(
                usuario_id=usuario_id,
                codigo=codigo,
                fecha_expiracion=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(verificacion)
            db.session.commit()
            
            return codigo
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generando código: {str(e)}")
            return None
    
    def enviar_email_verificacion(self, usuario, codigo):
        """
        Envía email con código de verificación
        Retorna (éxito, mensaje)
        """
        try:
            mensaje = MIMEMultipart()
            mensaje['From'] = current_app.config['MAIL_DEFAULT_SENDER']
            mensaje['To'] = usuario.email
            mensaje['Subject'] = 'Verifica tu email - Almas con Cola'
            
            # Cuerpo HTML
            contexto = {
                'nombre': usuario.nombre,
                'codigo': codigo
            }
            cuerpo_html = render_template('auth/correo_verificacion.html', **contexto)
            mensaje.attach(MIMEText(cuerpo_html, 'html'))
            
            # Adjuntar logo
            try:
                with open("app/static/images/logos/logo.jpg", "rb") as f:
                    imagen = MIMEImage(f.read())
                    imagen.add_header('Content-ID', '<logo_fundacion>')
                    imagen.add_header('Content-Disposition', 'inline', filename="logo.jpg")
                    mensaje.attach(imagen)
            except FileNotFoundError:
                current_app.logger.warning("Logo no encontrado para email")
            
            # Enviar
            server = smtplib.SMTP(
                current_app.config['MAIL_SERVER'],
                current_app.config['MAIL_PORT']
            )
            server.starttls()
            server.login(
                current_app.config['MAIL_USERNAME'],
                current_app.config['MAIL_PASSWORD']
            )
            server.send_message(mensaje)
            server.quit()
            
            current_app.logger.info(f"Email enviado a {usuario.email}")
            return True, "Email enviado exitosamente"
        except Exception as e:
            current_app.logger.error(f"Error enviando email: {str(e)}")
            return False, f"Error al enviar email: {str(e)}"
    
    def verificar_codigo(self, usuario_id, codigo):
        """
        Verifica el código de confirmación
        Retorna (éxito, mensaje)
        """
        verificacion = VerificacionEmail.query.filter_by(
            usuario_id=usuario_id,
            codigo=codigo,
            usado=False
        ).first()
        
        if not verificacion:
            return False, "Código inválido"
        
        if datetime.utcnow() > verificacion.fecha_expiracion:
            return False, "Código expirado"
        
        try:
            # Marcar como usado
            verificacion.usado = True
            
            # Marcar usuario como verificado
            usuario = Usuario.query.get(usuario_id)
            usuario.verified = True
            
            db.session.commit()
            return True, "Email verificado exitosamente"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error verificando código: {str(e)}")
            return False, "Error al verificar código"
    
    def cambiar_contrasena(self, usuario_id, contrasena_actual, contrasena_nueva):
        """
        Cambia la contraseña del usuario
        Retorna (éxito, mensaje)
        """
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return False, "Usuario no encontrado"
        
        if not self.bcrypt.check_password_hash(usuario.password, contrasena_actual):
            return False, "Contraseña actual incorrecta"
        
        valida, error = self.validar_contrasena(contrasena_nueva)
        if not valida:
            return False, error
        
        try:
            usuario.password = self.bcrypt.generate_password_hash(contrasena_nueva).decode('utf-8')
            db.session.commit()
            return True, "Contraseña actualizada"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cambiando contraseña: {str(e)}")
            return False, "Error al cambiar contraseña"
    
    def actualizar_perfil(self, usuario_id, nombre, email):
        """
        Actualiza información del perfil
        Retorna (éxito, mensaje)
        """
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return False, "Usuario no encontrado"
        
        if not nombre:
            return False, "El nombre es requerido"
        
        if not self.validar_email(email):
            return False, "Email no válido"
        
        # Verificar si el email ya existe (y no es del mismo usuario)
        otro_usuario = Usuario.query.filter_by(email=email).first()
        if otro_usuario and otro_usuario.id != usuario_id:
            return False, "El email ya está registrado"
        
        try:
            usuario.nombre = nombre
            usuario.email = email
            db.session.commit()
            return True, "Perfil actualizado"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error actualizando perfil: {str(e)}")
            return False, "Error al actualizar perfil"
