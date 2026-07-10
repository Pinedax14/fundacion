# Diccionario de datos

Describe las columnas de los CSV generados por `scripts/extraer_datos.py` +
`scripts/limpieza_datos.py` en `data/raw/` y `data/processed/` (ambas
carpetas están en `.gitignore` porque contienen PII real — este documento
sí se versiona porque no contiene datos, solo la descripción de columnas).

## mascotas.csv

| Columna | Tipo | Descripción |
|---|---|---|
| id | int | ID de la mascota |
| nombre | str | Nombre de la mascota |
| especie | str | Perro / Gato (valores fuera de estos dos son errores de captura, ver notebook) |
| raza | str | Raza declarada |
| edad | int | Edad en meses |
| sexo | str | Macho / Hembra |
| descripcion | str | Descripción libre mostrada en el catálogo |
| foto_url | str | Ruta de la foto |
| estado | str | Disponible / En proceso / Adoptado |
| fecha_ingreso | datetime | Fecha de ingreso al refugio |

## solicitudes_adopcion.csv

| Columna | Tipo | Descripción |
|---|---|---|
| id | int | ID de la solicitud |
| id_usuario | int | FK a usuarios |
| id_mascota | int | FK a mascotas |
| fecha_solicitud | datetime | Fecha de la solicitud |
| estado_solicitud | str | pendiente / aprobada / rechazada |
| mensaje | str | Mensaje del solicitante |
| direccion | str | **PII** — dirección del solicitante |
| telefono | str | **PII** — teléfono del solicitante |
| estrato_social | int | Estrato (1-6) |
| mensaje_respuesta | str | Respuesta del admin (nullable) |
| ingresos | str | Rango de ingresos (`"min-max"` o `"max+"`). Valores `legacy_invalido` son registros previos a la migración `migrate_ingresos_type.py` que traían el entero crudo (incluye un sentinel `2147483647` = overflow de INTEGER) |

## reportes.csv

| Columna | Tipo | Descripción |
|---|---|---|
| id | int | ID del reporte |
| ubicacion | str | **PII/sensible** — ubicación del incidente |
| descripcion_incidente | str | Descripción del maltrato reportado |
| foto_evidencia_url | str | Foto de evidencia (nullable) |
| fecha_reporte | datetime | Fecha del reporte |
| estado_reporte | str | recibido / en_proceso / resuelto |

## donaciones.csv

| Columna | Tipo | Descripción |
|---|---|---|
| id | int | ID de la donación |
| cantidad | float | Monto donado |
| moneda | str | Moneda (default COP) |
| metodo_pago | str | nequi, daviplata, etc. |
| descripcion | str | Descripción libre |
| fecha_donacion | datetime | Fecha de la donación |

*(Vacía en el corte actual — el flujo de donación monetaria aún no tiene transacciones reales.)*

## donaciones_items.csv

| Columna | Tipo | Descripción |
|---|---|---|
| id | int | ID del ítem |
| id_donacion | int | FK a donaciones |
| tipo_item | str | alimento, juguete, medicinas, etc. |
| descripcion | str | Descripción del ítem |
| cantidad | int | Cantidad donada |
| valor_unitario | float | Valor unitario estimado (nullable) |
| fecha_registro | datetime | Fecha de registro |

*(Vacía en el corte actual.)*

## solicitudes_voluntariado.csv

| Columna | Tipo | Descripción |
|---|---|---|
| id | int | ID de la solicitud |
| nombre_completo | str | **PII** |
| correo | str | **PII** |
| telefono | str | **PII** |
| franja_dias | str | fines_semana / entre_semana / flexible |
| dias_semana | str | Días específicos (nullable) |
| franja_horaria | str | Franja horaria preferida |
| motivo_voluntariado | str | Motivación del voluntario |
| estado | str | pendiente / aprobada / rechazada |
| fecha_solicitud | datetime | Fecha de la solicitud |

## voluntariados.csv

Voluntariados ya aprobados/activos. Vacía en el corte actual (todo el
volumen existente está en `solicitudes_voluntariado.csv`, aún sin aprobar).

---

**Nota de privacidad**: las columnas marcadas **PII** contienen datos
personales reales. Si este dataset se va a entregar/compartir como parte
de un trabajo académico, se recomienda anonimizar o eliminar esas columnas
primero (`direccion`, `telefono`, `correo`, `nombre_completo`, `ubicacion`).
