"""
Modelos de SQLAlchemy para la aplicación
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Usuario(db.Model):
    """Modelo de Usuario"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='user', nullable=False)  # 'user', 'admin'
    verified = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    solicitudes_adopcion = db.relationship('SolicitudAdopcion', back_populates='usuario', cascade='all, delete-orphan')
    reportes = db.relationship('Reporte', back_populates='usuario', cascade='all, delete-orphan')
    voluntariados = db.relationship('Voluntariado', back_populates='usuario', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.nombre} ({self.email})>'


class Mascota(db.Model):
    """Modelo de Mascota"""
    __tablename__ = 'mascotas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    especie = db.Column(db.String(50), nullable=False)  # perro, gato, etc
    raza = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer, nullable=False)  # en meses
    sexo = db.Column(db.String(1), nullable=False)  # M, F
    descripcion = db.Column(db.Text)
    foto_url = db.Column(db.String(255))
    estado = db.Column(db.String(50), default='Disponible', nullable=False)  # Disponible, En proceso, Adoptado
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    solicitudes_adopcion = db.relationship('SolicitudAdopcion', back_populates='mascota', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Mascota {self.nombre} ({self.especie})>'


class SolicitudAdopcion(db.Model):
    """Modelo de Solicitud de Adopción"""
    __tablename__ = 'solicitudes_adopcion'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    mensaje = db.Column(db.Text)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(20))
    ingresos = db.Column(db.Integer)
    estrato_social = db.Column(db.Integer)  # 1-6
    estado = db.Column(db.String(50), default='pendiente', nullable=False)  # pendiente, aprobada, rechazada
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    nombre_mascota = db.Column(db.String(120))  # Denormalizado para queries
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='solicitudes_adopcion')
    mascota = db.relationship('Mascota', back_populates='solicitudes_adopcion')
    
    def __repr__(self):
        return f'<SolicitudAdopcion Usuario:{self.usuario_id} Mascota:{self.mascota_id}>'


class Reporte(db.Model):
    """Modelo de Reporte de Maltrato"""
    __tablename__ = 'reportes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    ubicacion = db.Column(db.String(255), nullable=False)
    descripcion_incidente = db.Column(db.Text, nullable=False)
    foto_evidencia_url = db.Column(db.String(255))
    estado = db.Column(db.String(50), default='recibido', nullable=False)  # recibido, en_proceso, resuelto
    fecha_reporte = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='reportes')
    
    def __repr__(self):
        return f'<Reporte {self.ubicacion}>'


class Voluntariado(db.Model):
    """Modelo de Voluntariado"""
    __tablename__ = 'voluntariados'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    dias_disponibles = db.Column(db.String(255))  # JSON o string separado por comas
    franjas_horarias = db.Column(db.String(255))  # JSON o string
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='voluntariados')
    
    def __repr__(self):
        return f'<Voluntariado Usuario:{self.usuario_id}>'


class VerificacionEmail(db.Model):
    """Modelo de Verificación de Email"""
    __tablename__ = 'verificaciones_email'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    codigo = db.Column(db.String(10), unique=True, nullable=False, index=True)
    usado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<VerificacionEmail Usuario:{self.usuario_id}>'


class Donacion(db.Model):
    """Modelo de Donación"""
    __tablename__ = 'donaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Float, nullable=False)
    moneda = db.Column(db.String(10), default='COP')
    metodo_pago = db.Column(db.String(50))  # nequi, daviplata, etc
    descripcion = db.Column(db.Text)
    fecha_donacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Donacion ${self.cantidad} {self.moneda}>'
