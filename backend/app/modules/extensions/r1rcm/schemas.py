from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import date, datetime
import uuid

class R1ExcelRow(BaseModel):
    date: str
    trip_id: str
    employee_id: str
    employee_name: str
    shift: str
    location: str
    pickup: str
    drop: str
    route_number: str
    cab_type: str
    vendor: str
    vehicle_number: str
    rate: str

class ValidationResult(BaseModel):
    row_index: int
    row_data: R1ExcelRow
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class R1ImportPreviewResponse(BaseModel):
    batch_id: uuid.UUID
    total_rows: int
    valid_count: int
    error_count: int
    warning_count: int
    results: List[ValidationResult]

class R1ConfirmImportRequest(BaseModel):
    batch_id: uuid.UUID
    customer_id: uuid.UUID
    location: str
