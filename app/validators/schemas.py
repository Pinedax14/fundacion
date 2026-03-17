"""
Validadores usando Marshmallow para validación centralizada de datos
"""

from marshmallow import Schema, fields, ValidationError, validate, pre_load
import re


class UsuarioRegistroSchema(Schema):
    """Schema para validar registro de usuario"""
    nombre = fields.Str(required=True, validate=validate.Length(min=3, max=120))
    email = fields.Email(required=True)
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
    ingresos = fields.Int(required=True)
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
