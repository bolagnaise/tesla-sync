#!/usr/bin/env python3
"""Ensure all required database columns exist.

This script runs after flask db upgrade to fix cases where Alembic
thinks the schema is up to date but columns are actually missing.
"""
import sqlite3
import sys
import os

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/app.db')

# Columns that must exist in the user table
# Format: (column_name, column_type, default_value)
REQUIRED_COLUMNS = [
    ('sigenergy_export_limit_kw', 'REAL', None),
    ('inverter_power_limit_w', 'INTEGER', None),
]


def get_existing_columns(cursor, table_name):
    """Get list of existing column names in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def ensure_columns():
    """Ensure all required columns exist in the database."""
    if not os.path.exists(DATABASE_PATH):
        print("Database not found, skipping column check")
        return True

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        existing = get_existing_columns(cursor, 'user')
        added = []

        for col_name, col_type, default in REQUIRED_COLUMNS:
            if col_name not in existing:
                print(f"Adding missing column: user.{col_name}")
                sql = f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"
                if default is not None:
                    sql += f" DEFAULT {default}"
                cursor.execute(sql)
                added.append(col_name)

        if added:
            conn.commit()
            print(f"Added {len(added)} missing column(s): {', '.join(added)}")
        else:
            print("All required columns exist")

        conn.close()
        return True

    except Exception as e:
        print(f"Error ensuring columns: {e}")
        return False


if __name__ == '__main__':
    success = ensure_columns()
    sys.exit(0 if success else 1)
