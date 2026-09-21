from datetime import datetime, date, time
from decimal import Decimal
import json
from uuid import UUID
from enum import Enum
from typing import Any, Dict

class TenantDataTransformer:
    """
    Transforms PostgreSQL native types into D1/SQLite compatible representations.
    """
    
    @staticmethod
    def transform_value(value: Any) -> Any:
        if value is None:
            return None
            
        if isinstance(value, UUID):
            return str(value)
            
        if isinstance(value, Enum):
            return value.name
            
        if isinstance(value, datetime):
            return value.isoformat()
            
        if isinstance(value, date):
            return value.isoformat()
            
        if isinstance(value, time):
            return value.isoformat()
            
        if isinstance(value, Decimal):
            # Financial precision rule: Convert to canonical string representation.
            # SQLite does not have native decimal, floating point causes drift.
            return str(value)
            
        if isinstance(value, dict) or isinstance(value, list):
            # JSON/JSONB -> Canonical string
            return json.dumps(value, sort_keys=True, separators=(',', ':'))
            
        if isinstance(value, bool):
            return 1 if value else 0
            
        return value

    @staticmethod
    def transform_row(row: dict) -> dict:
        return {k: TenantDataTransformer.transform_value(v) for k, v in row.items()}

