-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public IS 'standard public schema';

-- DROP SEQUENCE public.audit_logs_id_seq;

CREATE SEQUENCE public.audit_logs_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.audit_logs_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.audit_logs_id_seq TO neondb_owner;

-- DROP SEQUENCE public.donaciones_id_seq;

CREATE SEQUENCE public.donaciones_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.donaciones_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.donaciones_id_seq TO neondb_owner;

-- DROP SEQUENCE public.donaciones_items_id_seq;

CREATE SEQUENCE public.donaciones_items_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.donaciones_items_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.donaciones_items_id_seq TO neondb_owner;

-- DROP SEQUENCE public.mascotas_id_seq;

CREATE SEQUENCE public.mascotas_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.mascotas_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.mascotas_id_seq TO neondb_owner;

-- DROP SEQUENCE public.reportes_id_seq;

CREATE SEQUENCE public.reportes_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.reportes_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.reportes_id_seq TO neondb_owner;

-- DROP SEQUENCE public.solicitudes_adopcion_id_seq;

CREATE SEQUENCE public.solicitudes_adopcion_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.solicitudes_adopcion_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.solicitudes_adopcion_id_seq TO neondb_owner;

-- DROP SEQUENCE public.solicitudes_voluntariado_id_seq;

CREATE SEQUENCE public.solicitudes_voluntariado_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.solicitudes_voluntariado_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.solicitudes_voluntariado_id_seq TO neondb_owner;

-- DROP SEQUENCE public.usuarios_id_seq;

CREATE SEQUENCE public.usuarios_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.usuarios_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.usuarios_id_seq TO neondb_owner;

-- DROP SEQUENCE public.verificaciones_email_id_seq;

CREATE SEQUENCE public.verificaciones_email_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.verificaciones_email_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.verificaciones_email_id_seq TO neondb_owner;

-- DROP SEQUENCE public.verificaciones_id_seq;

CREATE SEQUENCE public.verificaciones_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.verificaciones_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.verificaciones_id_seq TO neondb_owner;

-- DROP SEQUENCE public.voluntariados_id_seq;

CREATE SEQUENCE public.voluntariados_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.voluntariados_id_seq OWNER TO neondb_owner;
GRANT ALL ON SEQUENCE public.voluntariados_id_seq TO neondb_owner;
-- public.donaciones definition

-- Drop table

-- DROP TABLE public.donaciones;

CREATE TABLE public.donaciones (
	id serial4 NOT NULL,
	cantidad float8 NOT NULL,
	moneda varchar(10) NULL,
	metodo_pago varchar(50) NULL,
	descripcion text NULL,
	fecha_donacion timestamp NULL,
	CONSTRAINT donaciones_pkey PRIMARY KEY (id)
);

-- Permissions

ALTER TABLE public.donaciones OWNER TO neondb_owner;
GRANT ALL ON TABLE public.donaciones TO neondb_owner;


-- public.mascotas definition

-- Drop table

-- DROP TABLE public.mascotas;

CREATE TABLE public.mascotas (
	id serial4 NOT NULL,
	nombre varchar(100) NOT NULL,
	especie varchar(50) NOT NULL,
	raza varchar(100) NULL,
	edad int4 NULL,
	sexo text NULL,
	descripcion text NOT NULL,
	foto_url varchar(255) NULL,
	estado text DEFAULT 'Disponible'::text NULL,
	fecha_ingreso timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT mascotas_estado_check CHECK ((estado = ANY (ARRAY['Disponible'::text, 'En proceso'::text, 'Adoptado'::text]))),
	CONSTRAINT mascotas_pkey PRIMARY KEY (id),
	CONSTRAINT mascotas_sexo_check CHECK ((sexo = ANY (ARRAY['Macho'::text, 'Hembra'::text])))
);

-- Permissions

ALTER TABLE public.mascotas OWNER TO neondb_owner;
GRANT ALL ON TABLE public.mascotas TO neondb_owner;


-- public.reportes definition

-- Drop table

-- DROP TABLE public.reportes;

CREATE TABLE public.reportes (
	id serial4 NOT NULL,
	ubicacion varchar(255) NOT NULL,
	descripcion_incidente text NOT NULL,
	foto_evidencia_url varchar(255) NULL,
	fecha_reporte timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	estado_reporte text DEFAULT 'recibido'::text NULL,
	CONSTRAINT reportes_estado_reporte_check CHECK ((estado_reporte = ANY (ARRAY['recibido'::text, 'resuelto'::text]))),
	CONSTRAINT reportes_pkey PRIMARY KEY (id)
);

-- Permissions

ALTER TABLE public.reportes OWNER TO neondb_owner;
GRANT ALL ON TABLE public.reportes TO neondb_owner;


-- public.solicitudes_voluntariado definition

-- Drop table

-- DROP TABLE public.solicitudes_voluntariado;

CREATE TABLE public.solicitudes_voluntariado (
	id serial4 NOT NULL,
	nombre_completo varchar(150) NOT NULL,
	correo varchar(150) NOT NULL,
	telefono varchar(50) NOT NULL,
	franja_dias varchar(30) NOT NULL,
	dias_semana varchar(120) NULL,
	franja_horaria varchar(30) NOT NULL,
	motivo_voluntariado text NOT NULL,
	fecha_solicitud timestamp DEFAULT now() NOT NULL,
	estado varchar(20) DEFAULT 'pendiente'::character varying NOT NULL,
	CONSTRAINT solicitudes_voluntariado_pkey PRIMARY KEY (id)
);

-- Permissions

ALTER TABLE public.solicitudes_voluntariado OWNER TO neondb_owner;
GRANT ALL ON TABLE public.solicitudes_voluntariado TO neondb_owner;


-- public.usuarios definition

-- Drop table

-- DROP TABLE public.usuarios;

CREATE TABLE public.usuarios (
	id serial4 NOT NULL,
	nombre varchar(150) NOT NULL,
	email varchar(150) NOT NULL,
	"password" varchar(255) NOT NULL,
	fecha_registro timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	rol text DEFAULT 'user'::text NULL,
	foto_perfil varchar(255) NULL,
	verified bool DEFAULT false NULL,
	fecha_actualizacion timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	fecha_nacimiento date NULL,
	CONSTRAINT usuarios_email_key UNIQUE (email),
	CONSTRAINT usuarios_pkey PRIMARY KEY (id),
	CONSTRAINT usuarios_rol_check CHECK ((rol = ANY (ARRAY['user'::text, 'admin'::text])))
);

-- Permissions

ALTER TABLE public.usuarios OWNER TO neondb_owner;
GRANT ALL ON TABLE public.usuarios TO neondb_owner;


-- public.audit_logs definition

-- Drop table

-- DROP TABLE public.audit_logs;

CREATE TABLE public.audit_logs (
	id serial4 NOT NULL,
	"timestamp" timestamp NOT NULL,
	usuario_id int4 NULL,
	usuario_nombre varchar(120) NULL,
	accion varchar(20) NOT NULL,
	tabla_afectada varchar(50) NOT NULL,
	registro_id int4 NOT NULL,
	datos_antes json NULL,
	datos_despues json NULL,
	ip_address varchar(45) NULL,
	user_agent varchar(500) NULL,
	metodo_http varchar(10) NULL,
	ruta varchar(255) NULL,
	estado_respuesta int4 NULL,
	notas text NULL,
	CONSTRAINT audit_logs_pkey PRIMARY KEY (id),
	CONSTRAINT audit_logs_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id)
);
CREATE INDEX ix_audit_logs_registro_id ON public.audit_logs USING btree (registro_id);
CREATE INDEX ix_audit_logs_tabla_afectada ON public.audit_logs USING btree (tabla_afectada);
CREATE INDEX ix_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");

-- Permissions

ALTER TABLE public.audit_logs OWNER TO neondb_owner;
GRANT ALL ON TABLE public.audit_logs TO neondb_owner;


-- public.donaciones_items definition

-- Drop table

-- DROP TABLE public.donaciones_items;

CREATE TABLE public.donaciones_items (
	id serial4 NOT NULL,
	id_donacion int4 NOT NULL,
	cantidad int4 NOT NULL,
	tipo_item varchar(100) NOT NULL,
	descripcion text NULL,
	valor_unitario float8 NOT NULL,
	fecha_registro timestamp NULL,
	CONSTRAINT donaciones_items_pkey PRIMARY KEY (id),
	CONSTRAINT donaciones_items_id_donacion_fkey FOREIGN KEY (id_donacion) REFERENCES public.donaciones(id)
);

-- Permissions

ALTER TABLE public.donaciones_items OWNER TO neondb_owner;
GRANT ALL ON TABLE public.donaciones_items TO neondb_owner;


-- public.solicitudes_adopcion definition

-- Drop table

-- DROP TABLE public.solicitudes_adopcion;

CREATE TABLE public.solicitudes_adopcion (
	id serial4 NOT NULL,
	id_usuario int4 NOT NULL,
	id_mascota int4 NOT NULL,
	fecha_solicitud timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	estado_solicitud text DEFAULT 'pendiente'::text NULL,
	mensaje text NULL,
	direccion varchar(255) NOT NULL,
	telefono varchar(20) NOT NULL,
	estrato_social int2 NOT NULL,
	mensaje_respuesta text NULL,
	ingresos varchar(50) NULL,
	CONSTRAINT solicitudes_adopcion_estado_solicitud_check CHECK ((estado_solicitud = ANY (ARRAY['pendiente'::text, 'aprobada'::text, 'rechazada'::text]))),
	CONSTRAINT solicitudes_adopcion_pkey PRIMARY KEY (id),
	CONSTRAINT fk_solicitudes_mascota FOREIGN KEY (id_mascota) REFERENCES public.mascotas(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_solicitudes_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Permissions

ALTER TABLE public.solicitudes_adopcion OWNER TO neondb_owner;
GRANT ALL ON TABLE public.solicitudes_adopcion TO neondb_owner;


-- public.verificaciones definition

-- Drop table

-- DROP TABLE public.verificaciones;

CREATE TABLE public.verificaciones (
	id serial4 NOT NULL,
	id_usuario int4 NOT NULL,
	codigo varchar(6) NOT NULL,
	fecha_creacion timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	usado bool DEFAULT false NULL,
	CONSTRAINT verificaciones_pkey PRIMARY KEY (id),
	CONSTRAINT fk_verificaciones_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id)
);

-- Permissions

ALTER TABLE public.verificaciones OWNER TO neondb_owner;
GRANT ALL ON TABLE public.verificaciones TO neondb_owner;


-- public.verificaciones_email definition

-- Drop table

-- DROP TABLE public.verificaciones_email;

CREATE TABLE public.verificaciones_email (
	id serial4 NOT NULL,
	usuario_id int4 NOT NULL,
	codigo varchar(10) NOT NULL,
	usado bool NULL,
	fecha_creacion timestamp NULL,
	fecha_expiracion timestamp NOT NULL,
	CONSTRAINT verificaciones_email_pkey PRIMARY KEY (id),
	CONSTRAINT verificaciones_email_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id)
);
CREATE UNIQUE INDEX ix_verificaciones_email_codigo ON public.verificaciones_email USING btree (codigo);

-- Permissions

ALTER TABLE public.verificaciones_email OWNER TO neondb_owner;
GRANT ALL ON TABLE public.verificaciones_email TO neondb_owner;


-- public.voluntariados definition

-- Drop table

-- DROP TABLE public.voluntariados;

CREATE TABLE public.voluntariados (
	id serial4 NOT NULL,
	usuario_id int4 NOT NULL,
	dias_disponibles varchar(255) NULL,
	franjas_horarias varchar(255) NULL,
	fecha_registro timestamp NULL,
	fecha_actualizacion timestamp NULL,
	CONSTRAINT voluntariados_pkey PRIMARY KEY (id),
	CONSTRAINT voluntariados_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id)
);

-- Permissions

ALTER TABLE public.voluntariados OWNER TO neondb_owner;
GRANT ALL ON TABLE public.voluntariados TO neondb_owner;



-- DROP FUNCTION public.sp_obtener_usuario_por_email(text);

CREATE OR REPLACE FUNCTION public.sp_obtener_usuario_por_email(p_email text)
 RETURNS TABLE(id integer, nombre text, email text, fecha_nacimiento date, rol text, verified boolean)
 LANGUAGE sql
AS $function$
    SELECT id, nombre, email, fecha_nacimiento, rol, verified
    FROM usuarios
    WHERE email = p_email;
$function$
;

-- Permissions

ALTER FUNCTION public.sp_obtener_usuario_por_email(text) OWNER TO neondb_owner;
GRANT ALL ON FUNCTION public.sp_obtener_usuario_por_email(text) TO neondb_owner;

-- DROP FUNCTION public.sp_registrar_usuario(text, text, text, date);

CREATE OR REPLACE FUNCTION public.sp_registrar_usuario(p_nombre text, p_email text, p_password text, p_fecha_nacimiento date)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO usuarios(nombre, email, password, fecha_nacimiento, rol, verified, fecha_registro)
    VALUES (p_nombre, p_email, p_password, p_fecha_nacimiento, 'user', false, NOW())
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.sp_registrar_usuario(text, text, text, date) OWNER TO neondb_owner;
GRANT ALL ON FUNCTION public.sp_registrar_usuario(text, text, text, date) TO neondb_owner;


-- Permissions

GRANT ALL ON SCHEMA public TO pg_database_owner;
GRANT USAGE ON SCHEMA public TO public;
ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT UPDATE, TRIGGER, REFERENCES, SELECT, TRUNCATE, DELETE, MAINTAIN, INSERT ON TABLES TO neon_superuser WITH GRANT OPTION;
ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT USAGE, UPDATE, SELECT ON SEQUENCES TO neon_superuser WITH GRANT OPTION;