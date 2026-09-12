import sqlite3
from sqlalchemy import Table, MetaData, Column, String, Integer, Float, Text, create_engine
from sqlalchemy.schema import CreateTable
from typing import List, Dict, Any

class TenantDataImporter:
    """
    Imports transformed data into a SQLite/D1 database.
    """
    def __init__(self, db_path: str):
        # We use sqlite directly or SQLAlchemy sync engine to represent D1
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")

    def prepare_schema(self, tables: Dict[str, Table]):
        """
        Creates a D1-compatible schema from SQLAlchemy definitions.
        Postgres-specific types are ignored or cast to generic variants by SQLite dialect.
        """
        metadata = MetaData()
        
        with self.engine.begin() as conn:
            for name, table in tables.items():
                # We build a stripped-down Table for SQLite representation
                columns = []
                for col in table.columns:
                    # Map to generic types explicitly for D1 safety
                    col_type = col.type
                    col_type_str = str(col_type).upper()
                    
                    new_type = String()
                    if "INT" in col_type_str:
                        new_type = Integer()
                    elif "FLOAT" in col_type_str or "REAL" in col_type_str:
                        new_type = Float()
                    else:
                        # Fallback for UUID, JSONB, ENUM, TIMESTAMP -> TEXT
                        new_type = Text()
                        
                    columns.append(Column(col.name, new_type, primary_key=col.primary_key, nullable=col.nullable))
                    
                sqlite_table = Table(name, metadata, *columns)
                conn.execute(CreateTable(sqlite_table))

    def import_table(self, table_name: str, rows: List[Dict[str, Any]]):
        """
        Inserts transformed rows into the D1 database.
        """
        if not rows:
            return
            
        with self.engine.begin() as conn:
            # Build insert statement
            columns = rows[0].keys()
            placeholders = ", ".join([f":{col}" for col in columns])
            columns_str = ", ".join(columns)
            
            stmt = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Executemany
            conn.execute(text(stmt), rows)
            
from sqlalchemy import text
