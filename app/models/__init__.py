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
    foto_perfil = db.Column(db.String(255))  # URL o nombre del archivo de foto de perfil
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    solicitudes_adopcion = db.relationship('SolicitudAdopcion', back_populates='usuario', cascade='all, delete-orphan')
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
    usuario_id = db.Column('id_usuario', db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mascota_id = db.Column('id_mascota', db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    mensaje = db.Column(db.Text)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(20))
    ingresos = db.Column(db.Integer)
    estrato_social = db.Column(db.Integer)  # 1-6
    estado = db.Column('estado_solicitud', db.String(50), default='pendiente', nullable=False)  # pendiente, aprobada, rechazada
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
    ubicacion = db.Column(db.String(255), nullable=False)
    descripcion_incidente = db.Column(db.Text, nullable=False)
    foto_evidencia_url = db.Column(db.String(255))
    estado = db.Column('estado_reporte', db.String(50), default='recibido', nullable=False)  # recibido, en_proceso, resuelto
    fecha_reporte = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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


class SolicitudVoluntariado(db.Model):
    """Modelo de Solicitud de Voluntariado
    
    Captura solicitudes de personas que quieren ser voluntarios.
    """
    __tablename__ = 'solicitudes_voluntariado'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    franja_dias = db.Column(db.String(50), nullable=False)  # fines_semana, entre_semana, flexible
    dias_semana = db.Column(db.String(255), nullable=False)  # JSON o string: "lunes, miercoles, viernes"
    franja_horaria = db.Column(db.String(50), nullable=False)  # manana_8_14, tarde_14_20, noche_20_22
    motivo_voluntariado = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(50), default='pendiente', nullable=False)  # pendiente, aprobada, rechazada
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SolicitudVoluntariado {self.nombre_completo}>'


class Item_Donacion(db.Model):
    """Modelo de Items de Donación
    
    Describe los artículos específicos donados en una donación.
    """
    __tablename__ = 'donaciones_items'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_donante = db.Column(db.String(120), nullable=False)
    contacto_email = db.Column(db.String(120))
    tipo_donacion = db.Column(db.String(100), nullable=False)  # alimento, juguete, medicinas, etc
    descripcion_donacion = db.Column(db.Text)
    fecha_donacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado_entrega = db.Column(db.String(50), default='pendiente')  # pendiente, entregado, cancelado
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    valor_unitario = db.Column(db.Float)
    
    def __repr__(self):
        return f'<Item_Donacion {self.tipo_donacion}>'


class AuditLog(db.Model):
    """Modelo de Registro de Auditoría
    
    Rastrea todos los cambios en la BD para seguridad y debugging.
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_nombre = db.Column(db.String(120))  # Desnormalizado por si se elimina usuario
    accion = db.Column(db.String(20), nullable=False)  # INSERT, UPDATE, DELETE
    tabla_afectada = db.Column('tabla_afectada', db.String(50), nullable=False, index=True)
    registro_id = db.Column(db.Integer, nullable=False, index=True)  # PK del registro modificado
    datos_antes = db.Column('datos_antes', db.JSON)  # Dict con valores anteriores (para UPDATE/DELETE)
    datos_despues = db.Column('datos_despues', db.JSON)  # Dict con valores nuevos (para INSERT/UPDATE)
    ip_address = db.Column(db.String(45))  # IPv4 o IPv6
    user_agent = db.Column(db.String(500))
    ruta = db.Column(db.String(255))
    estado_respuesta = db.Column(db.String(50))
    notas = db.Column(db.Text)
    metodo_http = db.Column(db.String(20))
    
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    
    def __repr__(self):
        return f'<AuditLog {self.accion} {self.tabla_afectada}[{self.registro_id}] por {self.usuario_nombre}>'
    
    def to_dict(self):
        """Convierte el log a diccionario para visualización"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario_nombre,
            'accion': self.accion,
            'tabla_afectada': self.tabla_afectada,
            'registro_id': self.registro_id,
            'datos_antes': self.datos_antes,
            'datos_despues': self.datos_despues,
            'ip_address': self.ip_address,
            'metodo_http': self.metodo_http,
            'ruta': self.ruta,
            'estado_respuesta': self.estado_respuesta,
            'notas': self.notas
        }
