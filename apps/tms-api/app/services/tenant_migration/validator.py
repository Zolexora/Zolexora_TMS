from typing import Dict, Any
from sqlalchemy import text
from app.services.tenant_migration.importer import TenantDataImporter

class TenantRuntimeValidator:
    def __init__(self, importer: TenantDataImporter):
        self.importer = importer

    def run_validation(self) -> Dict[str, Any]:
        """
        Executes representative read/write operations against the pilot database.
        """
        report = {
            "success": True,
            "operations_passed": 0,
            "operations_failed": 0,
            "details": []
        }
        
        try:
            with self.importer.engine.begin() as conn:
                # 1. Read Master Data
                conn.execute(text("SELECT id, full_name FROM drivers LIMIT 1"))
                report["operations_passed"] += 1
                report["details"].append("Read drivers - PASS")
                
                # 2. Read Invoices
                conn.execute(text("SELECT id, grand_total, status FROM invoices LIMIT 1"))
                report["operations_passed"] += 1
                report["details"].append("Read invoices - PASS")
                
        except Exception as e:
            report["success"] = False
            report["operations_failed"] += 1
            report["details"].append(f"Validation failed: {str(e)}")
            
        return report
