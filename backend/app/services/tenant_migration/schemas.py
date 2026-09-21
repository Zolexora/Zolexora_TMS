from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid

class MigrationResult(BaseModel):
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None

class ReconciliationReport(BaseModel):
    counts_match: bool
    financials_match: bool
    details: Dict[str, Any]
    
class ValidationReport(BaseModel):
    success: bool
    operations_passed: int
    operations_failed: int
    details: List[str]

class AdminMigrationReport(BaseModel):
    migration_id: str
    organisation_id: str
    source: str
    destination: str
    schema_version: int
    tables: int
    rows: int
    reconciliation: str
    financial_reconciliation: str
    referential_integrity: str
    runtime_validation: str
    overall_status: str

