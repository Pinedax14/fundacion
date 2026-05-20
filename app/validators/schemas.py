"""
Validadores usando Marshmallow para validación centralizada de datos
"""

from marshmallow import Schema, fields, ValidationError, validate
from datetime import datetime, timedelta
import re


class UsuarioRegistroSchema(Schema):
    """Schema para validar registro de usuario"""
    nombre = fields.Str(required=True, validate=validate.Length(min=3, max=120))
    email = fields.Email(required=True)
    fecha_nacimiento = fields.Date(required=True, format='%Y-%m-%d')
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True
    )
    confirm_password = fields.Str(
        required=True,
        load_only=True
    )
    
    def validate_password(self, value):
        """Validar que la contraseña cumple requisitos"""
        if not re.search(r'\d', value):
            raise ValidationError("Debe contener al menos un número")
        if not re.search(r'[!@#$%^&*]', value):
            raise ValidationError("Debe contener al menos un símbolo especial")
    
    def validate_fecha_nacimiento(self, value):
        """Validar que la fecha de nacimiento es válida"""
        hoy = datetime.now().date()
        
        # No permitir fechas futuras
        if value > hoy:
            raise ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        
        # No permitir fechas muy antiguas (más de 150 años atrás)
        fecha_minima = hoy - timedelta(days=150*365.25)
        if value < fecha_minima:
            raise ValidationError("La fecha de nacimiento no puede ser más de 150 años atrás.")
        
        # Validar que sea mayor de edad (mínimo 13 años)
        edad_minima = hoy - timedelta(days=13*365.25)
        if value > edad_minima:
            raise ValidationError("Debes tener al menos 13 años para registrarte.")


class UsuarioLoginSchema(Schema):
    """Schema para validar login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class VerificacionEmailSchema(Schema):
    """Schema para validar verificación de email"""
    codigo = fields.Str(
        required=True,
        validate=validate.Length(equal=6),
        error_messages={'validator_failed': 'El código debe ser de 6 dígitos'}
    )


class SolicitudAdopcionSchema(Schema):
    """Schema para validar solicitud de adopción"""
    mascota_id = fields.Int(required=True)
    mensaje = fields.Str()
    direccion = fields.Str(required=True, validate=validate.Length(min=10))
    telefono = fields.Str(required=True, validate=validate.Length(min=7, max=20))
    ingresos = fields.Str(required=True, validate=validate.OneOf([
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
    ]))
    estrato_social = fields.Int(required=True, validate=validate.Range(min=1, max=6))


class ReporteMaltratoSchema(Schema):
    """Schema para validar reporte de maltrato"""
    ubicacion = fields.Str(required=True, validate=validate.Length(min=10))
    descripcion_incidente = fields.Str(required=True, validate=validate.Length(min=20))


class MascotaSchema(Schema):
    """Schema para validar datos de mascota"""
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    especie = fields.Str(required=True)
    raza = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    edad = fields.Int(required=True, validate=validate.Range(min=0, max=300))
    sexo = fields.Str(required=True, validate=validate.OneOf(['M', 'F']))
    descripcion = fields.Str()


class VoluntariadoSchema(Schema):
    """Schema para validar voluntariado"""
    dias_disponibles = fields.Str(required=True)
    franjas_horarias = fields.Str(required=True)


class ActualizarPerfilSchema(Schema):
    """Schema para actualizar perfil de usuario"""
    nombre = fields.Str(required=True, validate=validate.Length(min=3, max=120))
    email = fields.Email(required=True)


class CambiarPasswordSchema(Schema):
    """Schema para cambiar contraseña"""
    contrasena_actual = fields.Str(required=True, load_only=True)
    contrasena_nueva = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
    confirmar_contrasena = fields.Str(required=True, load_only=True)


def validar_datos(schema, datos):
    """
    Función auxiliar para validar datos contra un schema
    
    Retorna: (válido, datos_limpios_o_errores)
    """
    try:
        datos_validados = schema.load(datos)
        return True, datos_validados
    except ValidationError as e:
        return False, e.messages
