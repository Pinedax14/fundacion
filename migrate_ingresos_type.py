"""
Script para migrar el tipo de dato del campo 'ingresos' de INTEGER a VARCHAR
en la tabla solicitudes_adopcion
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_ingresos_column():
    """Migra la columna ingresos de INTEGER a VARCHAR"""
    
    # Conexión a la base de datos
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL no está configurada")
        return False
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Iniciando migración de columna 'ingresos'...")
        
        # Paso 1: Crear columna temporal
        print("1. Creando columna temporal...")
        cursor.execute("""
            ALTER TABLE solicitudes_adopcion 
            ADD COLUMN ingresos_temp VARCHAR(50);
        """)
        conn.commit()
        print("   ✓ Columna temporal creada")
        
        # Paso 2: Copiar datos (convertir de integer a string)
        print("2. Copiando datos de ingresos a ingresos_temp...")
        cursor.execute("""
            UPDATE solicitudes_adopcion 
            SET ingresos_temp = CAST(ingresos AS VARCHAR(50))
            WHERE ingresos IS NOT NULL;
        """)
        conn.commit()
        print(f"   ✓ {cursor.rowcount} filas actualizadas")
        
        # Paso 3: Eliminar la columna original
        print("3. Eliminando columna ingresos original...")
        cursor.execute("""
            ALTER TABLE solicitudes_adopcion 
            DROP COLUMN ingresos;
        """)
        conn.commit()
        print("   ✓ Columna original eliminada")
        
        # Paso 4: Renombrar la columna temporal
        print("4. Renombrando columna temporal...")
        cursor.execute("""
            ALTER TABLE solicitudes_adopcion 
            RENAME COLUMN ingresos_temp TO ingresos;
        """)
        conn.commit()
        print("   ✓ Columna renombrada")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Migración completada exitosamente")
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Error en la migración: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    success = migrate_ingresos_column()
    exit(0 if success else 1)
