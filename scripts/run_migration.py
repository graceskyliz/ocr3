#!/usr/bin/env python3
"""
Script para ejecutar la migración de UUID a TEXT
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Construir URL de conexión
db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

print(f"Conectando a la base de datos...")
engine = create_engine(db_url)

# Leer el archivo SQL
sql_file = Path(__file__).parent / "migration_fix_all_uuids.sql"
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print("Ejecutando migración...")
print("-" * 50)

with engine.connect() as conn:
    # Ejecutar cada statement
    for statement in sql_content.split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                print(f"Ejecutando: {statement[:100]}...")
                result = conn.execute(text(statement))
                conn.commit()
                print("✓ OK")
            except Exception as e:
                print(f"✗ Error: {e}")
                conn.rollback()

print("-" * 50)
print("Migración completada!")
