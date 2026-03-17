"""
Tests para AuthService
"""

import pytest
from app.services.auth_service import AuthService
from app.models import Usuario
from flask import Flask


class TestAuthService:
    """Tests del servicio de autenticación"""
    
    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Setup para cada test"""
        self.app = app
        self.auth_service = AuthService()
    
    def test_validar_email_valido(self):
        """Test validación de email válido"""
        assert AuthService.validar_email('usuario@example.com') == True
        assert AuthService.validar_email('test.email@domain.co') == True
    
    def test_validar_email_invalido(self):
        """Test validación de email inválido"""
        assert AuthService.validar_email('invalidemail') == False
        assert AuthService.validar_email('user@') == False
        assert AuthService.validar_email('') == False
    
    def test_validar_contrasena_valida(self):
        """Test validación de contraseña válida"""
        with self.app.app_context():
            valida, error = AuthService.validar_contrasena('Password123!')
            assert valida == True
    
    def test_validar_contrasena_corta(self):
        """Test rechazo de contraseña corta"""
        with self.app.app_context():
            valida, error = AuthService.validar_contrasena('Pass1!')
            assert valida == False
            assert 'caracteres' in error.lower()
    
    def test_validar_contrasena_sin_numero(self):
        """Test rechazo si no hay número"""
        with self.app.app_context():
            valida, error = AuthService.validar_contrasena('Password!')
            assert valida == False
            assert 'número' in error.lower()
    
    def test_validar_contrasena_sin_simbolo(self):
        """Test rechazo si no hay símbolo especial"""
        with self.app.app_context():
            valida, error = AuthService.validar_contrasena('Password123')
            assert valida == False
            assert 'símbolo' in error.lower()
    
    def test_registrar_usuario_exitoso(self):
        """Test registro de usuario exitoso"""
        with self.app.app_context():
            exito, usuario = self.auth_service.registrar_usuario(
                nombre='Juan Perez',
                email='juan@example.com',
                password='Password123!',
                confirm_password='Password123!'
            )
            assert exito == True
            assert usuario.email == 'juan@example.com'
            assert usuario.rol == 'user'
    
    def test_registrar_usuario_email_duplicado(self):
        """Test rechazo de email duplicado"""
        with self.app.app_context():
            # Primer registro
            self.auth_service.registrar_usuario(
                nombre='Juan Perez',
                email='juan@example.com',
                password='Password123!',
                confirm_password='Password123!'
            )
            
            # Segundo registro con mismo email
            exito, mensaje = self.auth_service.registrar_usuario(
                nombre='Otro Usuario',
                email='juan@example.com',
                password='Password123!',
                confirm_password='Password123!'
            )
            assert exito == False
            assert 'registrado' in mensaje.lower()
    
    def test_registrar_usuario_contrasenas_no_coinciden(self):
        """Test rechazo si contraseñas no coinciden"""
        with self.app.app_context():
            exito, mensaje = self.auth_service.registrar_usuario(
                nombre='Juan Perez',
                email='juan@example.com',
                password='Password123!',
                confirm_password='DifferentPass123!'
            )
            assert exito == False
            assert 'coinciden' in mensaje.lower()
    
    def test_verificar_usuario_exitoso(self):
        """Test login exitoso"""
        with self.app.app_context():
            # Crear usuario verificado
            usuario = Usuario(
                nombre='Juan',
                email='juan@example.com',
                password=self.auth_service.bcrypt.generate_password_hash('Password123!').decode('utf-8'),
                verified=True
            )
            from app.models import db
            db.session.add(usuario)
            db.session.commit()
            
            # Login
            exito, usuario_login = self.auth_service.verificar_usuario('juan@example.com', 'Password123!')
            assert exito == True
            assert usuario_login.email == 'juan@example.com'
    
    def test_verificar_usuario_contrasena_incorrecta(self):
        """Test login con contraseña incorrecta"""
        with self.app.app_context():
            # Crear usuario
            usuario = Usuario(
                nombre='Juan',
                email='juan@example.com',
                password=self.auth_service.bcrypt.generate_password_hash('Password123!').decode('utf-8'),
                verified=True
            )
            from app.models import db
            db.session.add(usuario)
            db.session.commit()
            
            # Login fallido
            exito, mensaje = self.auth_service.verificar_usuario('juan@example.com', 'WrongPassword123!')
            assert exito == False
            assert 'incorrecta' in mensaje.lower()
