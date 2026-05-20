-- Procedimientos almacenados para Neon / PostgreSQL

-- 1) Registrar usuario usando procedimiento almacenado
CREATE OR REPLACE FUNCTION sp_registrar_usuario(
    p_nombre TEXT,
    p_email TEXT,
    p_password TEXT,
    p_fecha_nacimiento DATE
)
RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO usuarios(nombre, email, password, fecha_nacimiento, rol, verified, fecha_registro)
    VALUES (p_nombre, p_email, p_password, p_fecha_nacimiento, 'user', false, NOW())
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$;

-- 2) Consulta básica de usuario por email (puede usarse para validaciones en Flask)
CREATE OR REPLACE FUNCTION sp_obtener_usuario_por_email(
    p_email TEXT
)
RETURNS TABLE(id INTEGER, nombre TEXT, email TEXT, fecha_nacimiento DATE, rol TEXT, verified BOOLEAN) LANGUAGE sql AS $$
    SELECT id, nombre, email, fecha_nacimiento, rol, verified
    FROM usuarios
    WHERE email = p_email;
$$;
